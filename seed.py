import time

import serial



class Seed:

    def __init__(self, **kwargs):


        if "log_file" in kwargs:
            self.log_file = kwargs["log_file"]
            self.read_log_file(self.log_file)
        else:
            self.com_port = kwargs["com_port"]
            # TODO REPLACE WITH DRIVER
            self.ser = serial.Serial(self.com_port)
            self.driver_sn = kwargs["drive_sn"]
            self.seed_name = kwargs["seed_name"]
            self.chip_name = kwargs["chip_name"]
            self.log_file_location = kwargs["log_file_location"]
            self.log_period = kwargs["log_period"]
            self.target_log_time_hours = kwargs["target_log_time_hours"]
            self.seed_ref_power = kwargs["seed_ref_power"]
            self.seed_ref_pd = kwargs["seed_ref_pd"]

            self.log_start_time = time.time()
            self.log_file_name = self.seed_name + "_" + self.chip_name + "_lifetime.txt"
            self.write_log_header()
            self.pd_histogram: dict[int, list[int]] = {}
            self.pd_freq_histogram: dict[int, list[float]] = {}
            self.pulse_current_histogram: dict[int, list[float]] = {}

            self.start_offset = 0




    def write_log_header(self):
        pass

    def read_log_file(self, log_file: str):
        return 0, {}

    def get_data(self):