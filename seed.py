import time
import serial
from driver import Driver
from datetime import datetime
from os import path
from PySide6.QtCore import QObject, QTimer, Signal
import asyncio
from typing import Optional
import numpy as np
from threading import Lock
import gc
from itertools import cycle
from bitarray import bitarray
import pandas

AMOUNT_TIME_DATA = 12*10**4
COMM_ERR = 0
CONNECTION_ERR = 1
PD_ERR = 2
FREQ_ERR = 3
SET_CURR_ERR = 4
SEED_DEATH = 5
PD_READ_ERR = 6
FREQ_READ_ERR = 7
CURR_READ_ERR = 8

DEFAULT_FREQ_KHZ = 20
DEFAULT_PD = 150
DEFAULT_POWER = 20.0
DEFAULT_WAVELENGTH = 1064




class Seed(QObject):
    updatePD = Signal(str)
    updateStatus = Signal(str)
    newValues = Signal(float, float, float)
    startValues = Signal(int, int)


    def __init__(self, stop_signal: Signal, delete_signal: Signal, seed_connected: Signal,
                 ready_to_start: Signal):
        super(Seed, self).__init__()
        self.com_port = ""
        self.seed_name = ""
        self.chip_name = ""
        self.log_file_location = ""
        self.log_file = ""
        self.power_file = ""
        self.log_period = 0.5
        self.target_log_time_hours = 10000
        self.seed_ref_power = DEFAULT_POWER
        self.seed_ref_pd = DEFAULT_PD
        self.seed_ref_wavelength = DEFAULT_WAVELENGTH
        self.seed_target_freq = DEFAULT_FREQ_KHZ*1000

        self.log_start_time = 0.0
        # now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.log_file_name = ""
       # self.write_log_header()
        self.driver: Optional[Driver] = None
        self.driver_serial_number = ""
        self.pd_histogram = np.zeros(2**16, dtype=np.uint32)
        self.pd_min, self.pd_max = np.inf, -np.inf

        self.pd_freq_histogram = np.zeros(2**16, dtype=np.uint32)
        self.pd_freq_min, self.pd_freq_max = np.inf, -np.inf

        self.pulse_current_histogram = np.zeros(2**16, dtype=np.uint32)
        self.pulse_current_min, self.pulse_current_max = np.inf, -np.inf

        self.start_offset = 0

        self.last_log = 0

        self.delete_this = False

        self.poll_timer = QTimer()
        self.stop_signal: Signal[Seed] = stop_signal
        self.delete_signal: Signal[Seed] = delete_signal
        self.seed_connected: Signal[bool] = seed_connected
        self.ready_to_start: Signal[bool] = ready_to_start

        self.data_lock = Lock()
        self.file_lock = Lock()

        self.time_data_pd_value = np.empty(AMOUNT_TIME_DATA, dtype=np.int16)
        self.time_data_pd_freq_set_current = np.empty((AMOUNT_TIME_DATA, 2), dtype=np.uint16)
        self.time_data_time = np.empty(AMOUNT_TIME_DATA, dtype=np.int32)

        self.measured_powers = np.empty((300, 2), dtype=np.int32)
        self.power_index = 0

        self.time_data_index = 0

        self.time_data_interval = self.target_log_time_hours*3600/AMOUNT_TIME_DATA

        self.stop_when_ready = False
        self.stopped = False

        self.error_array = bitarray([0]*9)
        self.error_indices = [(COMM_ERR, "COMM ERROR"), (CONNECTION_ERR, "CONNECTION\nERROR"), (PD_ERR, "PD ERROR"),
                              (FREQ_ERR, "FREQ ERROR"), (SET_CURR_ERR, "SET CURR ERROR"), (SEED_DEATH, "SEED DEATH"),
                              (PD_READ_ERR, "PD READ ERROR"), (FREQ_READ_ERR, "FREQ READ ERROR"), (CURR_READ_ERR, "CURR READ ERROR")]
        self.cyclic = cycle(self.error_indices)

        self.driver_lock = Lock()

        self.continued_run = False

    def read_log_file(self, log_file):
        try:
            np_df = pandas.read_csv(log_file, header=1, dtype=np.float64, sep=";").to_numpy()
            np_df[:, 2] = np_df[:, 2] * 100
            np_df[:, 3] = np_df[:, 3] * 1000

            np_df = np_df.astype(np.int32)
            for a_ind, hist in enumerate([self.pd_histogram, self.pd_freq_histogram, self.pulse_current_histogram], start=1):
                minim, maxim = np.min(np_df[:, a_ind]), np.max(np_df[:, a_ind])
                count, division = np.histogram(np_df[:, a_ind], bins=max(int(maxim-minim), 1))
                division = division.astype(np.uint32)

                for c_ind, c in enumerate(count):
                    if a_ind == 1:
                        hist[division[c_ind]+2**15] = c
                    else:
                        hist[division[c_ind]] = c


            return True
        except (ValueError, IndexError):
            return False

    def read_power_file(self, power_file):
        try:
            self.power_file = power_file
            np_df = pandas.read_csv(self.power_file, header=1, dtype=np.float64, sep=",").to_numpy()
            np_df[:, 1] = np_df[:, 1] * 10
            np_df = np_df.astype(np.int32)
            self.measured_powers[np_df.shape[0], :] = np_df
            self.power_index = np_df.shape[0]
        except (ValueError, IndexError) :
            self.power_file = ""
            self.power_index = 0

    def create_power_file(self):
        if self.continued_run:
            self.power_file = self.log_file[:-4] + "_power.txt"
        else:
            power_file_name = self.log_file_name[:-4] + "_power.txt"
            self.power_file = path.join(self.log_file_location, power_file_name)
        with open(self.power_file, "w") as f:
            f.write("Start: " + datetime.fromtimestamp(self.log_start_time).strftime("%Y/%m/%d %H:%M:%S") + "\n")
            f.write("Time (s), Power (mW)\n")

    def add_power_measurement(self, power: float):
        if self.power_file == "":
            self.create_power_file()
        with open(self.power_file, "a") as f:
            f.write(str(int(round(time.time() - self.log_start_time))) + ", " + str(power) + "\n")

    def target_freq_changed(self, freq_khz: float):
        self.seed_target_freq = int(freq_khz*1000)

    def set_stop_when_ready(self, stop: bool):
        self.stop_when_ready = stop

    def delete_seed(self):
        with self.driver_lock:

            self.driver = None
       # self.deleteLater()

    async def shutdown_driver(self, delete=False):
        with self.driver_lock:

            for shutoff_try in range(10):
                if self.driver is not None:
                    try:
                        await self.driver.shutdown_all_devices()
                        all_off = False
                        while not all_off:
                            all_off = True
                            for laser_id in [1, 2]:
                                ret, resp, _ = await self.driver.get_laser_state(laser_id)
                                if not ret or resp[0] != 0:
                                    all_off = False
                                    await self.driver.set_laser_state(laser_id, 0)
                            for tec_id in [1, 2, 3, 4]:
                                ret, resp, _ = await self.driver.get_tec_state(tec_id)
                                if not ret or resp[0] != 0:
                                    all_off = False
                                    await self.driver.set_tec_state(laser_id, 0)
                        break
                    except (serial.SerialException, serial.SerialTimeoutException):
                        continue

        if delete:
            self.driver = None
           # self.deleteLater()

    def set_histograms(self, pd_histogram: dict[int, int], pd_freq_histogram: dict[float, int],
                       pulse_current_histogram: dict[float, int]):
        self.pd_histogram = pd_histogram
        self.pd_freq_histogram = pd_freq_histogram
        self.pulse_current_histogram = pulse_current_histogram

    def reference_wavelength_changed(self, ref_wavelength: float):
        self.seed_ref_wavelength = ref_wavelength

    def reference_pd_value_changed(self, ref_pd: int):
        self.seed_ref_pd = ref_pd

    def reference_power_changed(self, ref_power: float):
        self.seed_ref_power = ref_power

    def log_file_location_changed(self, log_location: str):
        self.log_file_location = log_location
        self.log_file = ""
        self.check_ready_to_start()

    def log_file_changed(self, log_file: str):
        if log_file and self.read_log_file(log_file):
            self.log_file = log_file
            self.log_file_location = path.dirname(log_file)
            self.check_ready_to_start()
            return True
        else:
            self.log_file = ""
            self.log_file_location = ""
            self.check_ready_to_start()
            return False


    def log_period_changed(self, log_period: int):
        self.log_period = log_period
        self.check_ready_to_start()

    def target_log_time_changed(self, target_hours: int):
        self.target_log_time_hours = target_hours
        self.time_data_interval = self.target_log_time_hours*3600/AMOUNT_TIME_DATA
        self.check_ready_to_start()

    def chip_name_changed(self, chip_name: str):
        self.chip_name = chip_name
        self.check_ready_to_start()

    def seed_name_changed(self, seed_name: str):
        self.seed_name = seed_name
        self.check_ready_to_start()

    def check_ready_to_start(self):
        if (self.seed_name and self.chip_name and (path.isdir(self.log_file_location) or path.isfile(self.log_file))
                and self.driver is not None):
            self.ready_to_start.emit(True)
        else:
            self.ready_to_start.emit(False)

    async def get_driver_info(self):
        ret, resp, other_resp = await self.driver.get_info()
        if ret:
            model, manufacturer, serial1, batch = resp
            serial1: int
            self.driver_serial_number = serial1.to_bytes(8, "big").decode("utf-8")

    async def connect_to_driver(self, com_port=""):
        if self.driver is None:
            try:
                self.com_port = com_port
                self.driver = Driver(self.com_port, timeout=0.1, read_timeout=0.1, resend_amount=4)
                await self.get_driver_info()
                if self.driver_serial_number != "":
                    pd2_ret, pd2_resp, _ = await self.driver.get_pd(2)
                    if pd2_ret:
                        pd2_freq_ret, pd2_freq_resp, _ = await self.driver.get_pd_freq(2)
                        if pd2_ret:
                            pd2, pd2_freq = pd2_resp[0], pd2_freq_resp[0]*10
                            self.seed_target_freq = pd2_freq
                            self.seed_ref_pd = pd2
                            self.startValues.emit(pd2, pd2_freq)
                        else:
                            raise serial.SerialException
                    else:
                        raise serial.SerialException
                    self.seed_connected.emit(True)
                else:
                    raise serial.SerialException

            except (serial.SerialException, serial.SerialTimeoutException):
                self.handle_serial_error()
                self.driver = None
                self.driver_serial_number = ""
                self.seed_connected.emit(False)
        else:
            self.driver = None
            self.driver_serial_number = ""
            self.seed_connected.emit(False)

    def handle_serial_error(self):
        self.driver = None

    def write_log_header(self):
        self.log_start_time = round(time.time(), 1)
        now = datetime.now()
        now_text = now.strftime("%Y/%m/%d %H:%M:%S")
        now = now.strftime("%Y_%m_%d_%H_%M_%S")

        self.log_file_name = "_".join([now, self.seed_name, self.chip_name, "lifetime.txt"])
        with open(path.join(self.log_file_location, self.log_file_name), "w") as f:
            f.write("Start time: " + now_text + "\n")
            f.write(";".join(["Time (s)", "PD2 Value (uA)", "PD2 Freq (kHz)", "Pulse Driver Set Current (A)"]) + "\n")

    def log_data(self, pd2: int, pd2_freq: float, pulse_set_current: float):
        try:
            if self.continued_run:
                with open(self.log_file, "a") as f:
                    f.write(";".join([str(round(self.last_log-self.log_start_time, 1)),
                                      str(pd2), str(pd2_freq/100), str(pulse_set_current/1000)]) + "\n")
            else:
                with open(path.join(self.log_file_location, self.log_file_name), "a") as f:
                    f.write(";".join([str(round(self.last_log-self.log_start_time, 1)),
                                      str(pd2), str(pd2_freq/100), str(pulse_set_current/1000)]) + "\n")
        except (PermissionError, FileNotFoundError):
            pass
        # TODO HANDLE ERROR

    async def get_data(self):
        if not self.driver_lock.locked():
            with self.driver_lock:
                if self.stop_when_ready:
                    if time.time() - self.log_start_time > self.target_log_time_hours*3600 + self.start_offset:
                        self.stop_signal.emit(self)
                        if self.driver is not None:
                            await self.shutdown_driver()
                            self.stopped = True
                if not self.stopped:
                    if self.driver is None:
                        try:
                            self.driver = Driver(self.com_port, timeout=0.1, read_timeout=0.1, resend_amount=4)
                        except (serial.SerialException, serial.SerialTimeoutException):
                            self.driver = None
                    if self.driver is not None:
                        try:
                            pd2_ret, pd2_resp, _ = await self.driver.get_pd(2)
                            pd2 = pd2_resp[0] if pd2_ret else np.nan
                            pd2_freq_ret, pd2_freq_resp, _ = await self.driver.get_pd_freq(2)
                            pd2_freq = pd2_freq_resp[0] if pd2_freq_ret else np.nan
                            current_ret, current_resp, _ = await self.driver.get_laser_set_current(1)
                            self.last_log = time.time()
                            pulse_set_current = current_resp[0] if current_ret else np.nan
                            with self.data_lock:
                                if self.last_log-self.log_start_time > self.time_data_interval * self.time_data_index and self.time_data_index < AMOUNT_TIME_DATA:
                                    self.time_data_time[self.time_data_index] = int(round(self.last_log-self.log_start_time, 1)*10)
                                    self.time_data_pd_value[self.time_data_index] = int(pd2) if not np.isnan(pd2) else -69
                                    self.time_data_pd_freq_set_current[self.time_data_index, :] = [pd2_freq if not np.isnan(pd2_freq) else 0, pulse_set_current if not np.isnan(pulse_set_current) else 0]
                                    self.time_data_index += 1
                                elif self.last_log-self.log_start_time > self.time_data_interval * self.time_data_index:
                                    self.time_data_time = np.roll(self.time_data_time, -1)
                                    self.time_data_time[self.time_data_index] = int(
                                        round(self.last_log - self.log_start_time, 1) * 10)

                                    self.time_data_pd_value = np.roll(self.time_data_pd_value, -1)
                                    self.time_data_pd_value[self.time_data_index] = int(pd2) if not np.isnan(pd2) else -69

                                    self.time_data_pd_freq_set_current = np.roll(self.time_data_pd_freq_set_current, -1, 0)
                                    self.time_data_pd_freq_set_current[self.time_data_index, :] = [
                                        pd2_freq if not np.isnan(pd2_freq) else 0,
                                        pulse_set_current if not np.isnan(pulse_set_current) else 0]

                                self.pd_histogram[pd2+2**15 if pd2_ret else 2**15] += 1

                                self.pd_freq_histogram[pd2_freq if pd2_freq_ret else 0] += 1

                                self.pulse_current_histogram[pulse_set_current if current_ret else 0] += 1
                            with self.file_lock:
                                self.log_data(pd2, pd2_freq, pulse_set_current)

                            self.updatePD.emit(str(pd2))
                            if pd2_ret:
                                self.error_array[COMM_ERR] = 0
                                if not self.seed_ref_pd*0.9 < pd2 < self.seed_ref_pd*1.1:
                                    self.error_array[PD_ERR] = 1
                                else:
                                    self.error_array[PD_ERR] = 0
                            self.error_array[PD_READ_ERR] = not pd2_ret

                            if pd2_freq_ret:
                                self.error_array[COMM_ERR] = 0
                                if pd2_freq * 10 < 100:
                                    self.error_array[SEED_DEATH] = 1
                                    self.error_array[FREQ_ERR] = 0
                                elif abs(self.seed_target_freq-pd2_freq*10) > 200:
                                    self.error_array[FREQ_ERR] = 1
                                else:
                                    self.error_array[FREQ_ERR] = 0
                            self.error_array[FREQ_READ_ERR] = not pd2_freq_ret

                            if current_ret:
                                self.error_array[COMM_ERR] = 0
                                if pulse_set_current == 0:
                                    self.error_array[SET_CURR_ERR] = 1
                                else:
                                    self.error_array[SET_CURR_ERR] = 0
                            self.error_array[CURR_READ_ERR] = not current_ret

                            if self.error_array[[PD_READ_ERR, FREQ_READ_ERR, CURR_READ_ERR]].all():
                                self.error_array[[PD_READ_ERR, FREQ_READ_ERR, CURR_READ_ERR, PD_ERR, FREQ_ERR, SET_CURR_ERR]] = 0
                                self.error_array[COMM_ERR] = 1

                            self.error_array[CONNECTION_ERR] = 0

                        except (serial.SerialException, serial.SerialTimeoutException):
                            self.error_array[:] = 0
                            self.error_array[CONNECTION_ERR] = 1
                            del self.driver
                            self.driver = None
                    else:
                        self.error_array[:] = 0
                        self.error_array[CONNECTION_ERR] = 1

