import time
import serial
from driver import Driver
from datetime import datetime
from os import path
from PySide6.QtCore import QObject, QTimer, Signal
import asyncio
from typing import Optional
import numpy as np


class Seed(QObject):
    updatePD = Signal(bool, int)
    commError = Signal()
    serialError = Signal()

    def __init__(self, stop_signal: Signal, delete_signal: Signal, seed_connected: Signal,
                 ready_to_start: Signal):
        super(Seed, self).__init__()
        self.com_port = ""
        self.seed_name = ""
        self.chip_name = ""
        self.log_file_location = ""
        self.log_period = 0
        self.target_log_time_hours = 0
        self.seed_ref_power = 0.0
        self.seed_ref_pd = 0

        self.log_start_time = 0.0
        # now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.log_file_name = ""
       # self.write_log_header()
        self.driver: Optional[Driver] = None
        self.driver_serial_number = ""
        self.pd_histogram: dict[int, int] = {}
        self.pd_freq_histogram: dict[float, int] = {}
        self.pulse_current_histogram: dict[float, int] = {}

        self.start_offset = 0

        self.last_log = 0

        self.delete_this = False

        self.poll_timer = QTimer()
        self.stop_signal: Signal[Seed] = stop_signal
        self.delete_signal: Signal[Seed] = delete_signal
        self.seed_connected: Signal[bool, bool] = seed_connected
        self.ready_to_start: Signal[bool] = ready_to_start

    async def shutdown_driver(self):
        self.driver.shutdown_all_devices()
        all_off = False
        while not all_off:
            all_off = True
            for laser_id in [1, 2]:
                ret, resp, _ = await self.driver.get_laser_state(laser_id)
                if not ret or resp[0] != 0:
                    all_off = False
            for tec_id in [1, 2, 3, 4]:
                ret, resp, _ = await self.driver.get_tec_state(tec_id)
                if not ret or resp[0] != 0:
                    all_off = False
        self.driver = None
        self.delete_signal.emit(self)

    def set_histograms(self, pd_histogram: dict[int, int], pd_freq_histogram: dict[float, int],
                       pulse_current_histogram: dict[float, int]):
        self.pd_histogram = pd_histogram
        self.pd_freq_histogram = pd_freq_histogram
        self.pulse_current_histogram = pulse_current_histogram

    def reference_pd_value_changed(self, ref_pd: int):
        self.seed_ref_pd = ref_pd

    def reference_power_changed(self, ref_power: float):
        self.seed_ref_power = ref_power

    def log_file_location_changed(self, log_location: str):
        self.log_file_location = log_location
        print(log_location, self)
        self.check_ready_to_start()

    def log_period_changed(self, log_period: int):
        self.log_period = log_period
        print(log_period, self)
        self.check_ready_to_start()

    def target_log_time_changed(self, target_hours: int):
        self.target_log_time_hours = target_hours
        print(target_hours, self)
        self.check_ready_to_start()

    def chip_name_changed(self, chip_name: str):
        self.chip_name = chip_name
        print(chip_name, self)
        self.check_ready_to_start()

    def seed_name_changed(self, seed_name: str):
        self.seed_name = seed_name
        print(seed_name, self)
        self.check_ready_to_start()

    def check_ready_to_start(self):
        if self.seed_name and self.chip_name and path.isdir(self.log_file_location) and self.driver is not None:
            self.ready_to_start.emit(True)
            print("ready")
        else:
            self.ready_to_start.emit(False)
            print("not ready")

    async def get_driver_info(self):
        ret, resp, other_resp = await self.driver.get_info()
        if ret:
            model, manufacturer, serial1, batch = resp
            serial1: int
            self.driver_serial_number = serial1.to_bytes(8, "big").decode("utf-8")
        else:
            self.commError.emit()

    async def connect_to_driver(self, com_port=""):
        print("terve")
        print(self.driver)
        if self.driver is None:
            try:
                self.com_port = com_port
                self.driver = Driver(self.com_port, timeout=0.1, read_timeout=0.1, resend_amount=10)
                while self.driver_serial_number == "":
                    await self.get_driver_info()
                    self.seed_connected.emit(True, self.driver_serial_number != "")
            except (serial.SerialException, serial.SerialTimeoutException):
                print("täällä")
                self.handle_serial_error()
                self.driver = None
                self.driver_serial_number = ""
                self.seed_connected.emit(False, False)
        else:
            print("driver is none")
            self.driver = None
            self.driver_serial_number = ""
            self.seed_connected.emit(False, False)

    def handle_serial_error(self):
        self.driver = None

    def write_log_header(self):
        self.log_start_time = time.time()
        with open(path.join(self.log_file_location, self.log_file_name), "w") as f:
            f.write("")
            f.write(";".join(["Time (s)", "PD2 Value (uA)", "PD2 Freq (kHz)", "Pulse Driver Set Current (A)"]))

    def log_data(self, pd2: int, pd2_freq: float, pulse_set_current: float):
        with open(path.join(self.log_file_location, self.log_file_name), "a") as f:
            f.write(";".join([str(round(self.last_log-self.log_start_time, 1)),
                              str(pd2), str(pd2_freq), str(pulse_set_current)]))

    async def get_data(self):
        if time.time() - self.log_start_time > self.target_log_time_hours + self.start_offset:
            self.stop_signal.emit(self)
        else:
            if self.driver is None:
                await self.connect_to_driver(self.com_port)
                if self.driver is None:
                    self.serialError.emit()
            try:
                pd2_ret, pd2_resp, _ = await self.driver.get_pd(2)
                pd2 = pd2_resp[0] if pd2_ret else np.nan
                pd2_freq_ret, pd2_freq_resp, _ = await self.driver.get_pd_freq(2)
                pd2_freq = pd2_freq_resp[0]/1000 if pd2_freq_ret else np.nan
                current_ret, current_resp, _ = await self.driver.get_laser_set_current(1)
                self.last_log = time.time()
                pulse_set_current = current_resp[0]/1000 if current_ret else np.nan
                if pd2 not in self.pd_histogram:
                    self.pd_histogram[pd2] = 1
                else:
                    self.pd_histogram[pd2] += 1

                if pd2_freq not in self.pd_freq_histogram:
                    self.pd_freq_histogram[pd2_freq] = 1
                else:
                    self.pd_freq_histogram[pd2_freq] += 1

                if pulse_set_current not in self.pulse_current_histogram:
                    self.pulse_current_histogram[pulse_set_current] = 1
                else:
                    self.pulse_current_histogram[pulse_set_current] += 1

                self.log_data(pd2, pd2_freq, pulse_set_current)
                self.updatePD.emit(pd2_ret, pd2 if pd2_ret else 0)
                if not pd2_ret or not pd2_freq_ret or current_ret:
                    self.commError.emit()

            except (serial.SerialException, serial.SerialTimeoutException):
                self.serialError.emit()
