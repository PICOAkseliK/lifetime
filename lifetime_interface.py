import asyncio
import os
from os import path
import time
import sys
from lifetime_ui import Ui_MainWindow
from PySide6.QtCore import Signal, QTimer
import pyqtgraph as pg
from PySide6.QtWidgets import QMainWindow, QLineEdit
from seed import Seed
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from collections import deque
from threading import Thread, Lock, Event
from PySide6.QtWidgets import QApplication
from typing import Optional
from serial.tools.list_ports import comports
from datetime import datetime


class Lifetime(QMainWindow):
    updateSeedPD = Signal(int, int)
    updateStatus = Signal(Seed)
    stopSeed = Signal(Seed)
    deleteSeed = Signal(Seed)
    seedConnected = Signal(bool, bool)
    readyToStart = Signal(bool)

    def __init__(self):
        super(Lifetime, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.seeds: list[Seed] = []

        self.slow_event = Event()

       # self.ui.btnStart.setEnabled(True)

        self.poll_event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.poll_thread = Thread(target=self.poller_thread, daemon=True)
        self.poll_thread.start()

        self.com_port_timer = QTimer()
        self.com_port_timer.timeout.connect(self.poll_comports)
        self.com_port_timer.start(1500)

        self.new_seed = Seed(self.stopSeed, self.deleteSeed, self.seedConnected, self.readyToStart)
        self.ui.leditLogLocation.setProperty("valid", False)
        self.ui.leditLogLocation.textChanged.connect(self.log_location_changed)
        self.ui.btnBrowse.clicked.connect(self.browse_log_file)

        self.readyToStart.connect(self.ui.btnStart.setEnabled)
        self.ui.btnStart.clicked.connect(self.start_seed)

        self.ui.cboxCOM.currentIndexChanged.connect(lambda index: self.ui.btnConnect.setEnabled(index != 0))

        self.ui.leditSeed.textChanged.connect(lambda seed_name: self.new_seed.seed_name_changed(seed_name))
        self.ui.leditChip.textChanged.connect(lambda chip_name: self.new_seed.chip_name_changed(chip_name))

        self.ui.dsboxLogPeriod.valueChanged.connect(lambda log_period: self.new_seed.log_period_changed(log_period))
        self.ui.sboxLogTimeHours.valueChanged.connect(lambda log_hours: self.new_seed.target_log_time_changed(log_hours))
        self.ui.dsboxLogPeriod.valueChanged.connect(lambda log_period: self.new_seed.log_period_changed(log_period))

        self.ui.sboxSeedPD.valueChanged.connect(lambda pd_value: self.new_seed.reference_pd_value_changed(pd_value))
        self.ui.dsboxSeedPower.valueChanged.connect(lambda ref_pwr: self.new_seed.reference_power_changed(ref_pwr))

        self.stopSeed.connect(lambda seed: seed.poll_timer.stop())
       # self.readyToStart.connect(self.ui.btnConnect.setEnabled)
        self.ui.tableLasers.insertRow(0)
        self.ui.tableLasers.setCellWidget(0, 1, QLineEdit(enabled=False, text="helloo"))
        self.ui.leditDriverSerial.setDisabled(True)
        self.ui.leditDriverSerial.setStyleSheet("background-color: white")

        elapsed_time_timer = QTimer()
        elapsed_time_timer.timeout.connect(self.update_elapsed_times)
        elapsed_time_timer.start(500)
        self.ui.btnConnect.clicked.connect(self.connect_seed)
        self.seedConnected.connect(self.seed_connected)
    def update_elapsed_times(self):
        for row in range(self.ui.tableLasers.rowCount()):
            time_span = time.time() - self.seeds[row].log_start_time - self.seeds[row].start_offset
            hours = time_span // 3600
            minutes = (time_span - hours*3600) // 60
            seconds = round(time_span-hours*3600-minutes*60)
            self.ui.tableLasers.cellWidget(row, 9).setText(str(hours) + ":" + str(minutes) + ":" + str(seconds))

    def connect_seed(self):
        self.ui.btnConnect.setDisabled(True)
        self.ui.cboxCOM.setDisabled(True)
        self.ui.btnConnect.setText("Disconnect")
        asyncio.run_coroutine_threadsafe(self.new_seed.connect_to_driver(self.ui.cboxCOM.currentText()),
                                         self.poll_event_loop)

    def seed_connected(self, connected: bool, got_info: bool):
        print("halloo", connected, got_info)
        if not connected:
            self.ui.btnConnect.setText("Connect")
        elif got_info:
            self.ui.leditDriverSerial.setText(self.new_seed.driver_serial_number)
        self.ui.cboxCOM.setEnabled(True)

    def delete_seed(self, seed: Seed):
        self.seeds.remove(seed)
        del seed

    def browse_log_file(self):
        r = Tk()
        r.withdraw()
        log_path = askdirectory(title="Select log file location")
        if log_path:
            self.ui.leditLogLocation.setText(log_path)

    def log_location_changed(self, log_loc: str):
        if path.isdir(log_loc):
            self.ui.leditLogLocation.setProperty("valid", True)
            self.new_seed.log_file_location_changed(log_loc)
        else:
            self.ui.leditLogLocation.setProperty("valid", False)
            self.new_seed.log_file_location_changed("")

    def poller_thread(self):
        self.poll_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.poll_event_loop)
        print("no moro")
        self.poll_event_loop.run_forever()

    def update_seed_pd(self, row: int, pd: int):
        self.ui.tableLasers.cellWidget(row, -1).setText(str(pd) + " uA")

    def disconnect_seed(self, row: int):
        seed = self.seeds.pop(row)
        self.ui.tableLasers.removeRow(row)
        seed.poll_timer.stop()

    def connect_new_seed(self, com_port: str):
        asyncio.run_coroutine_threadsafe(self.new_seed.connect_to_driver(com_port), self.poll_event_loop)

    def continue_seed_logging(self):
        pass

    def poll_comports(self):
        comport_items = comports()
        found_ports = [c.name for c in comport_items]
        for seed in self.seeds:
            try:
                found_ports.remove(seed.com_port)
            except ValueError:
                pass
        existing = [self.ui.cboxCOM.itemText(i) for i in range(1, self.ui.cboxCOM.count())]
        if sorted(found_ports) != sorted(existing):
            for com_text in set(found_ports + existing):

                if com_text in found_ports and com_text not in existing:
                    self.ui.cboxCOM.addItem(com_text)

                elif com_text in existing:
                    self.ui.cboxCOM.removeItem(self.ui.cboxCOM.findText(com_text))

    def start_seed(self):
        seed, self.new_seed = self.new_seed, Seed(self.stopSeed, self.deleteSeed, self.seedConnected, self.readyToStart)
        seed.write_log_header()
        seed.poll_timer.timeout.connect(lambda: asyncio.run_coroutine_threadsafe(seed.get_data(), self.poll_event_loop))
        self.seeds.append(seed)
        self.ui.btnConnect.setText("Connect")
        self.ui.cboxCOM.setCurrentIndex(0)
        self.ui.leditLogLocation.clear()
        self.ui.leditSeed.clear()
        self.ui.leditChip.clear()
        self.ui.leditDriverSerial.clear()
        self.ui.sboxLogTimeHours.setValue(10000)
        self.ui.dsboxLogPeriod.setValue(0.5)
        self.ui.sboxSeedPD.setValue(600)
        self.ui.dsboxSeedPower.setValue(100)

        self.ui.tableLasers.insertRow(self.ui.tableLasers.rowCount())
        ledit_com = QLineEdit(enabled=False, text=seed.com_port)
        self.ui.tableLasers.setCellWidget(0, 0, ledit_com)

        ledit_driver = QLineEdit(enabled=False, text=seed.driver_serial_number)
        self.ui.tableLasers.setCellWidget(0, 1, ledit_driver)

        ledit_seed = QLineEdit(enabled=False, text=seed.seed_name)
        self.ui.tableLasers.setCellWidget(0, 2, ledit_seed)

        ledit_chip = QLineEdit(enabled=False, text=seed.chip_name)
        self.ui.tableLasers.setCellWidget(0, 3, ledit_chip)

        ledit_log_period = QLineEdit(enabled=False, text=seed.log_period)
        self.ui.tableLasers.setCellWidget(0, 4, ledit_log_period)

        ledit_power = QLineEdit(enabled=False, text=seed.seed_ref_power)
        self.ui.tableLasers.setCellWidget(0, 5, ledit_power)

        ledit_pc_target = QLineEdit(enabled=False, text=seed.seed_ref_pd)
        self.ui.tableLasers.setCellWidget(0, 6, ledit_pc_target)

        ledit_pd1 = QLineEdit(enabled=False)
        seed.updatePD.connect(lambda ret, pd_value: ledit_pd1.setText(str(pd_value if ret else "nan") + "uA"))
        self.ui.tableLasers.setCellWidget(0, 7, ledit_pd1)

        ledit_start_time = QLineEdit(enabled=False)
        ledit_start_time.setText(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        self.ui.tableLasers.setCellWidget(0, 8, ledit_start_time)

        ledit_elapsed_time = QLineEdit(enabled=False)
        self.ui.tableLasers.setCellWidget(0, 9, ledit_elapsed_time)

        ledit_status = QLineEdit(enabled=False, text=seed.com_port)
        self.ui.tableLasers.setCellWidget(0, 10, ledit_status)

        btn_disconnect = QLineEdit(enabled=False, text=seed.com_port)
        self.ui.tableLasers.setCellWidget(0, 11, btn_disconnect)




app = QApplication(sys.argv)
lt = Lifetime()
lt.show()
app.exec()