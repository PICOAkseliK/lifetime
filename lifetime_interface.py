import asyncio
import os
from os import path
import time
import sys
from lifetime_ui import Ui_MainWindow
from PySide6.QtCore import Signal, QTimer, QRectF
import pyqtgraph as pg
from PySide6.QtWidgets import (QMainWindow, QLineEdit, QPushButton, QLabel, QTableWidgetItem, QDialog, QGridLayout,
                               QDialogButtonBox, QCheckBox, QAbstractSpinBox)
from seed import Seed, DEFAULT_POWER, DEFAULT_WAVELENGTH, DEFAULT_PD, DEFAULT_FREQ_KHZ
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from collections import deque
from threading import Thread, Lock, Event
from PySide6.QtWidgets import QApplication
from typing import Optional
from serial.tools.list_ports import comports
from datetime import datetime
from PySide6.QtGui import QFont
import numpy as np
import pandas as pd
from PySide6.QtGui import QLinearGradient, QBrush, QColor, QPalette

ON_GOING_COLOR = 120, 120, 255
ELAPSED_COLOR_DIFF = 0.00001


class Lifetime(QMainWindow):
    updateSeedPD = Signal(int, int)
    updateStatus = Signal(Seed)
    stopSeed = Signal(Seed)
    deleteSeed = Signal(Seed)
    seedConnected = Signal(bool)
    readyToStart = Signal(bool)

    def __init__(self):
        super(Lifetime, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.seed_lock = Lock()
        self.seeds: list[Seed] = []

        self.slow_event = Event()

       # self.ui.btnStart.setEnabled(True)

        self.poll_event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.poll_thread = Thread(target=self.poller_thread, daemon=True)
        self.poll_thread.start()

        self.poll_comports()
        self.com_port_timer = QTimer()
        self.com_port_timer.timeout.connect(self.poll_comports)
        self.com_port_timer.start(1500)

        self.new_seed = Seed(self.stopSeed, self.deleteSeed, self.seedConnected, self.readyToStart)
        self.new_seed.startValues.connect(self.set_start_values)
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

        self.ui.sboxSeedPD.valueChanged.connect(lambda pd_value: self.new_seed.reference_pd_value_changed(pd_value))
        self.ui.dsboxSeedFreq.valueChanged.connect(lambda freq: self.new_seed.target_freq_changed(freq))
        self.ui.dsboxSeedPower.valueChanged.connect(lambda ref_pwr: self.new_seed.reference_power_changed(ref_pwr))

        self.ui.dsboxSeedWavelength.valueChanged.connect(lambda ref_wavelength: self.new_seed.reference_wavelength_changed(ref_wavelength))

        self.stopSeed.connect(lambda seed: seed.poll_timer.stop())

        self.elapsed_time_timer = QTimer()
        self.elapsed_time_timer.timeout.connect(self.update_elapsed_times)
        self.elapsed_time_timer.start(500)
        self.ui.btnConnect.clicked.connect(self.connect_seed)
        self.seedConnected.connect(self.seed_connected)
        self.ui.leditDriverSerial.setStyleSheet("background-color: white")

        self.ui.btnDisconnect.clicked.connect(self.disconnect_seed)

        self.pdi_pd_time = pg.PlotDataItem(connect="finite")
        self.pdi_pd_histogram = pg.PlotDataItem(stepMode="center", fillLevel=0, fillBrush=(255, 255, 255))
        self.ui.plot_pd.addItem(self.pdi_pd_histogram)

        self.pdi_pd_freq_time = pg.PlotDataItem(connect="finite")
        self.pdi_pd_freq_histogram = pg.PlotDataItem(stepMode="center", fillLevel=0, fillBrush=(255, 255, 255))
        self.ui.plot_freq.addItem(self.pdi_pd_freq_histogram)

        self.pdi_set_current_time = pg.PlotDataItem(connect="finite")
        self.pdi_set_current_histogram = pg.PlotDataItem(stepMode="center", fillLevel=0, fillBrush=(255, 255, 255))
        self.ui.plot_current.addItem(self.pdi_set_current_histogram)

        self.show_data_seed: Optional[Seed] = None

        self.ui.checkStopWhenReady.clicked.connect(lambda: self.show_data_seed.set_stop_when_ready(self.ui.checkStopWhenReady.isChecked()))

        self.ui.cboxSeedData.currentIndexChanged.connect(self.change_seed_data)

        self.ui.radioTime.clicked.connect(self.change_plot_type)
        self.ui.radioHistogram.clicked.connect(self.change_plot_type)
        self.ui.btnRefreshData.clicked.connect(self.change_seed_data)

        self.status_state = 0
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_for_status)
        self.status_timer.start(200)

        self.ui.dsboxSeedPower.setValue(DEFAULT_POWER)
        self.ui.dsboxSeedFreq.setValue(DEFAULT_FREQ_KHZ)
        self.ui.sboxSeedPD.setValue(DEFAULT_PD)
        self.ui.dsboxSeedWavelength.setValue(DEFAULT_WAVELENGTH)

        self.seeds_to_be_deleted: list[Seed] = []
        self.delete_seed_timer = QTimer()
        self.delete_seed_timer.timeout.connect(self.delete_seed)


        self.ui.dsboxMeasuredPower.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ui.dsboxMeasuredPower.setSuffix(" mW")
        self.ui.dsboxMeasuredPower.setDecimals(2)
        self.ui.dsboxMeasuredPower.setMaximum(99999)

        self.ui.dsboxMeasuredPower.wheelEvent = lambda value: None

        #self.start_seed()

        self.ui.radioNewLog.clicked.connect(self.run_type_changed)
        self.ui.radioContinueLog.clicked.connect(self.run_type_changed)

    def run_type_changed(self):
        self.ui.leditLogLocation.clear()
        if self.ui.radioNewLog.isChecked():
            self.new_seed.continued_run = False
            self.new_seed.power_index = 0
            self.ui.lblLogFile.setText("Log File Location")
            self.ui.leditLogLocation.setReadOnly(False)
        else:
            self.new_seed.continued_run = True
            self.ui.lblLogFile.setText("Select Log File")
            self.ui.leditLogLocation.setReadOnly(True)


    def set_start_values(self, pd2_value: int, pd2_freq_value: int):
        self.ui.sboxSeedPD.setValue(pd2_value)
        self.ui.dsboxSeedFreq.setValue(pd2_freq_value/1000)

    def change_plot_type(self):
        if self.ui.radioTime.isChecked():
            self.ui.plot_pd.removeItem(self.pdi_pd_histogram)
            self.ui.plot_freq.removeItem(self.pdi_pd_freq_histogram)
            self.ui.plot_current.removeItem(self.pdi_set_current_histogram)

            self.ui.plot_pd.addItem(self.pdi_pd_time)
            self.ui.plot_freq.addItem(self.pdi_pd_freq_time)
            self.ui.plot_current.addItem(self.pdi_set_current_time)
        else:
            self.ui.plot_pd.removeItem(self.pdi_pd_time)
            self.ui.plot_freq.removeItem(self.pdi_pd_freq_time)
            self.ui.plot_current.removeItem(self.pdi_set_current_time)

            self.ui.plot_pd.addItem(self.pdi_pd_histogram)
            self.ui.plot_freq.addItem(self.pdi_pd_freq_histogram)
            self.ui.plot_current.addItem(self.pdi_set_current_histogram)

    def update_elapsed_times(self):
        with self.seed_lock:
            for row in range(self.ui.tableLasers.rowCount()):
                seed = self.seeds[row]
                time_span = time.time() - seed.log_start_time
                hours = time_span // 3600
                minutes = (time_span - hours*3600) // 60
                seconds = round(time_span-hours*3600-minutes*60)
                self.ui.tableLasers.cellWidget(row, 8).setText(str(int(hours)).zfill(2) + ":" + str(int(minutes)).zfill(2) + ":" + str(seconds).zfill(2))
                w = self.ui.tableLasers.cellWidget(row, 8)
                rect = QRectF(w.rect())
                grad = QLinearGradient(rect.topLeft(), rect.topRight())
                palette = w.palette()
                target_seconds = seed.target_log_time_hours*3600
                if time_span < target_seconds:
                    ready_percentage = time_span/target_seconds
                    if ready_percentage > ELAPSED_COLOR_DIFF:
                        grad.setColorAt(0, QColor(*ON_GOING_COLOR))
                        grad.setColorAt(ready_percentage - ELAPSED_COLOR_DIFF, QColor(*ON_GOING_COLOR))
                    grad.setColorAt(ready_percentage, QColor("white"))

                else:
                    grad.setColorAt(0, QColor(50, 255, 50))

                palette.setBrush(QPalette.Base, QBrush(grad))
                w.setPalette(palette)

    def connect_seed(self):
        if self.new_seed.driver is None:
            self.ui.btnConnect.setDisabled(True)
            self.ui.cboxCOM.setDisabled(True)
            self.ui.btnConnect.setText("Disconnect")
        else:
            self.ui.btnConnect.setEnabled(True)
            self.ui.cboxCOM.setEnabled(True)
            self.ui.btnConnect.setText("Connect")
            self.ui.leditDriverSerial.clear()
        asyncio.run_coroutine_threadsafe(self.new_seed.connect_to_driver(self.ui.cboxCOM.currentText()),
                                         self.poll_event_loop)

    def seed_connected(self, connected: bool):
        self.ui.btnConnect.setEnabled(True)
        if not connected:
            self.ui.btnConnect.setText("Connect")
            self.ui.cboxCOM.setCurrentIndex(0)
            self.ui.cboxCOM.setEnabled(True)
            self.ui.leditDriverSerial.clear()

        else:
            self.ui.leditDriverSerial.setText(self.new_seed.driver_serial_number)
            self.ui.btnConnect.setText("Disconnect")

    def delete_seed(self):
        if self.seeds_to_be_deleted:
            for seed in self.seeds_to_be_deleted:
                if seed is not None:
                    if seed.driver is None:
                        print(seed)
                        del seed

            self.seeds_to_be_deleted = [seed for seed in self.seeds_to_be_deleted if seed is not None]
        else:
            if self.delete_seed_timer.isActive():
                self.delete_seed_timer.stop()

    def browse_for_power_log_file(self, initial_path: str):
        file_path = askopenfilename(initialdir=initial_path, title="Power Log File")
        if file_path:
            self.new_seed.read_power_file(file_path)
            if not self.new_seed.power_file:
                dlg = QDialog()
                dlg_layout = QGridLayout()
                dlg.setWindowTitle("Error")
                dlg_layout.addWidget(QLabel("Could not read Power Log File"), 0,
                                     0)
                dlg_btn = QDialogButtonBox(QDialogButtonBox.Ok)
                dlg_btn.accepted.connect(dlg.accept)
                dlg_layout.addWidget(dlg_btn)
                dlg.setLayout(dlg_layout)
                dlg.exec()

    def browse_log_file(self):
        r = Tk()
        r.withdraw()
        if self.ui.radioNewLog.isChecked():
            log_path = askdirectory(title="Select log file location")
            if log_path:
                self.ui.leditLogLocation.setText(log_path)
        else:
            file_path = askopenfilename(title="Select log file")
            if file_path:
                self.ui.leditLogLocation.setText(file_path)
                if self.new_seed.log_file:
                    dlg = QDialog()
                    dlg_layout = QGridLayout()
                    dlg.setWindowTitle("Power File")
                    dlg_layout.addWidget(QLabel("Does this Seed have a Power Log File?"), 0,
                                         0)
                    dlg_btn = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
                    dlg_btn.accepted.connect(lambda: self.browse_for_power_log_file(self.new_seed.log_file_location))
                    dlg_btn.accepted.connect(dlg.accept)
                    dlg_btn.rejected.connect(dlg.reject)
                    dlg_layout.addWidget(dlg_btn)
                    dlg.setLayout(dlg_layout)
                    dlg.exec()

    def error_at_reading_log_file(self):
        self.ui.leditLogLocation.clear()
        dlg = QDialog()
        dlg_layout = QGridLayout()
        dlg.setWindowTitle("Error")
        dlg_layout.addWidget(QLabel("Could not read Log File"), 0,
                             0)
        dlg_btn = QDialogButtonBox(QDialogButtonBox.Ok)
        dlg_btn.accepted.connect(dlg.accept)
        dlg_layout.addWidget(dlg_btn)
        dlg.setLayout(dlg_layout)
        dlg.exec()

    def log_location_changed(self, log_loc: str):
        if self.ui.radioNewLog.isChecked():

            if path.isdir(log_loc):
                self.ui.leditLogLocation.setProperty("valid", True)
                self.new_seed.log_file_location_changed(log_loc)
            else:
                self.ui.leditLogLocation.setProperty("valid", False)
                self.new_seed.log_file_location_changed("")
        else:
            if path.isfile(log_loc):
                try:
                    with open(log_loc, "r") as f:
                        line = f.readline()
                        time_line = line[line.find(":")+1:].strip().rstrip()
                        start_time = datetime.strptime(time_line, "%Y/%m/%d %H:%M:%S").timestamp()

                    self.new_seed.log_start_time = start_time
                    if self.new_seed.log_file_changed(log_loc):

                        self.ui.leditLogLocation.setProperty("valid", True)
                    else:
                        self.ui.leditLogLocation.setProperty("valid", False)
                        self.error_at_reading_log_file()


                except ValueError:
                    self.ui.leditLogLocation.setProperty("valid", False)
                    self.new_seed.log_file_changed("")
                    self.error_at_reading_log_file()

                #except Exception as e:
                  #  print(e, "töttöröö")
                  #  self.ui.leditLogLocation.setProperty("valid", False)
                   # self.new_seed.log_file_changed("")
            else:
                self.ui.leditLogLocation.setProperty("valid", False)
                self.new_seed.log_file_changed("")

    def poller_thread(self):
        self.poll_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.poll_event_loop)
        self.poll_event_loop.run_forever()

    def update_seed_pd(self, row: int, pd: int):
        self.ui.tableLasers.cellWidget(row, -1).setText(str(pd) + " uA")

    def do_disconnect_seed(self, index: int, shutdown: bool):
        print(shutdown)
        with self.seed_lock:
            self.ui.cboxSeedData.setCurrentIndex(0)
            self.ui.cboxSeedData.removeItem(index)
            seed = self.seeds.pop(index - 1)
            self.ui.tableLasers.removeRow(index - 1)
            seed.poll_timer.stop()
            if shutdown:
                asyncio.run_coroutine_threadsafe(seed.shutdown_driver(delete=True), self.poll_event_loop)
            else:
                seed.delete_seed()

    def disconnect_seed(self):

        dlg = QDialog()
        dlg_layout = QGridLayout()
        dlg.setWindowTitle("Disconnect Seed")
        index = self.ui.cboxSeedData.currentIndex()
        seed = self.seeds[index-1]
        dlg_layout.addWidget(QLabel("Disconnecting Seed\n" + str(seed.seed_name) + " at " + seed.com_port), 0, 0)
        dlg_layout.addWidget(QLabel("Do you wish to continue?"), 1, 0)
        check_shutdown = QCheckBox()
        check_shutdown.setText("Shutdown Before Disconnecting")
        dlg_layout.addWidget(check_shutdown, 2, 0)
        dlg_btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dlg_btn.accepted.connect(lambda: self.do_disconnect_seed(index, check_shutdown.isChecked()))
        dlg_btn.accepted.connect(dlg.accept)
        dlg_btn.rejected.connect(dlg.reject)
        dlg_layout.addWidget(dlg_btn)
        dlg.setLayout(dlg_layout)
        dlg.exec()

    def connect_new_seed(self, com_port: str):
        asyncio.run_coroutine_threadsafe(self.new_seed.connect_to_driver(com_port), self.poll_event_loop)

    def check_for_status(self):
        with self.seed_lock:
            if self.status_state == 0:
                for row in range(self.ui.tableLasers.rowCount()):
                    seed = self.seeds[row]
                    for s in range(len(seed.error_array)):
                        status_ind, status_name = seed.cyclic.__next__()
                        if seed.error_array[status_ind]:
                            self.ui.tableLasers.cellWidget(row, 9).setText(status_name)
                            self.ui.tableLasers.cellWidget(row, 9).setStyleSheet("background-color: red")
                            break
                    else:
                        if 0 < seed.target_log_time_hours * 3600 - (seed.last_log - seed.log_start_time):

                            self.ui.tableLasers.cellWidget(row, 9).setText("OK")
                            self.ui.tableLasers.cellWidget(row, 9).setStyleSheet("background-color: white")
                        else:
                            self.ui.tableLasers.cellWidget(row, 9).setText("Finished")
                            self.ui.tableLasers.cellWidget(row, 9).setStyleSheet("background-color: green")
            else:
                for row in range(self.ui.tableLasers.rowCount()):
                    self.ui.tableLasers.cellWidget(row, 9).setStyleSheet("background-color: white")
        self.status_state += 1
        if self.status_state > 2:
            self.status_state = 0

    def poll_comports(self):
        comport_items = comports()
        found_ports = [c.name for c in comport_items]
        with self.seed_lock:
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

                elif com_text in existing and com_text not in found_ports:
                    self.ui.cboxCOM.removeItem(self.ui.cboxCOM.findText(com_text))

    def start_seed(self):

        seed, self.new_seed = self.new_seed, Seed(self.stopSeed, self.deleteSeed, self.seedConnected, self.readyToStart)
        self.new_seed.startValues.connect(self.set_start_values)
        seed.target_freq_changed(self.ui.dsboxSeedFreq.value())
        seed.reference_pd_value_changed(self.ui.sboxSeedPD.value())
        seed.target_log_time_changed(self.ui.sboxLogTimeHours.value())
        seed.log_period_changed(self.ui.dsboxLogPeriod.value())
        seed.reference_power_changed(self.ui.dsboxSeedPower.value())
        seed.reference_wavelength_changed(self.ui.dsboxSeedWavelength.value())

        if not seed.continued_run:
            seed.write_log_header()
        seed.poll_timer.timeout.connect(lambda: asyncio.run_coroutine_threadsafe(seed.get_data(), self.poll_event_loop))

        seed.poll_timer.start(int(seed.log_period*1000))
        self.seeds.append(seed)
        self.ui.btnConnect.setText("Connect")
        self.ui.cboxCOM.setCurrentIndex(0)
        self.ui.cboxCOM.setEnabled(True)
        self.ui.leditLogLocation.clear()
        self.ui.leditSeed.clear()
        self.ui.leditChip.clear()
        self.ui.leditDriverSerial.clear()
        self.ui.sboxLogTimeHours.setValue(10000)
        self.ui.dsboxLogPeriod.setValue(0.5)
        self.ui.sboxSeedPD.setValue(600)
        self.ui.dsboxSeedPower.setValue(100)

        new_row = self.ui.tableLasers.rowCount()
        self.ui.tableLasers.insertRow(new_row)
        ledit_com = QLineEdit(enabled=False, text=seed.com_port)
        self.ui.tableLasers.setCellWidget(new_row, 0, ledit_com)

        ledit_driver = QLineEdit(enabled=False, text=seed.driver_serial_number)
        self.ui.tableLasers.setCellWidget(new_row, 1, ledit_driver)

        ledit_seed = QLineEdit(enabled=False, text=seed.seed_name)
        self.ui.tableLasers.setCellWidget(new_row, 2, ledit_seed)

        ledit_chip = QLineEdit(enabled=False, text=seed.chip_name)
        self.ui.tableLasers.setCellWidget(new_row, 3, ledit_chip)

        ledit_elapsed_time = QLineEdit(enabled=False)
        ledit_elapsed_time.setStyleSheet("color: black")

        self.ui.tableLasers.setCellWidget(new_row, 8, ledit_elapsed_time)

        ledit_power = QLineEdit(enabled=False, text=str(seed.seed_ref_power) + " mW")
        self.ui.tableLasers.setCellWidget(new_row, 5, ledit_power)

        ledit_wavelength = QLineEdit(enabled=False, text=str(seed.seed_ref_wavelength) + " mW")
        self.ui.tableLasers.setCellWidget(new_row, 4, ledit_wavelength)

        ledit_pc_target = QLineEdit(enabled=False, text=str(seed.seed_ref_pd) + " uA")
        ledit_pc_target.setStyleSheet("background-color: white; color: black")
        self.ui.tableLasers.setCellWidget(new_row, 6, ledit_pc_target)

        ledit_pd1 = QLineEdit(enabled=False)
        ledit_pd1.setStyleSheet("background-color: white; color: black")

        self.ui.tableLasers.setCellWidget(new_row, 7, ledit_pd1)

        seed.updatePD.connect(lambda pd_value, ledit_pd=ledit_pd1: ledit_pd.setText((pd_value + " uA") if pd_value.isdigit() else "nan"))

        ledit_status = QLineEdit(enabled=False, text="all good")
        self.ui.tableLasers.setCellWidget(new_row, 9, ledit_status)

        self.ui.cboxSeedData.addItem(seed.com_port + ", " + seed.seed_name + ", " + seed.chip_name,
                                     userData=seed)

    def change_seed_data(self):
        self.ui.dsboxMeasuredPower.setValue(0)
        if self.ui.cboxSeedData.currentIndex() == 0 or np.sum(self.ui.cboxSeedData.currentData().pd_histogram) == 0:
            self.ui.cboxSeedData.setCurrentIndex(0)
            self.ui.btnDisconnect.setDisabled(True)
            self.ui.checkStopWhenReady.setDisabled(True)
            self.ui.dsboxMeasuredPower.setDisabled(True)
            self.ui.radioTime.setDisabled(True)
            self.ui.radioHistogram.setDisabled(True)
            self.ui.dsboxMeasuredPower.setDisabled(True)
            self.ui.btnSetMeasuredPower.setDisabled(True)


            for row in range(self.ui.tableSeedData.rowCount()):
                for col in range(self.ui.tableSeedData.columnCount()):
                    self.ui.tableSeedData.removeCellWidget(row, col)

            self.pdi_pd_time.setData([], [])
            self.pdi_pd_histogram.setData([], [])

            self.pdi_pd_freq_time.setData([], [])
            self.pdi_pd_freq_histogram.setData([], [])

            self.pdi_set_current_time.setData([], [])
            self.pdi_set_current_histogram.setData([], [])

            self.show_data_seed = None

        else:
            self.ui.btnDisconnect.setEnabled(True)
            self.ui.dsboxMeasuredPower.setEnabled(True)
            self.ui.radioTime.setEnabled(True)
            self.ui.radioHistogram.setEnabled(True)
            self.ui.dsboxMeasuredPower.setEnabled(True)
            self.ui.btnSetMeasuredPower.setEnabled(True)

            self.show_data_seed: Seed = self.ui.cboxSeedData.currentData()
            with self.show_data_seed.data_lock:
                with self.show_data_seed.file_lock:
                    t_ind = self.show_data_seed.time_data_index
                    if t_ind >= 2:
                        self.pdi_pd_time.setData(self.show_data_seed.time_data_time[:t_ind]/10, self.show_data_seed.time_data_pd_value[:t_ind])
                        self.pdi_pd_freq_time.setData(self.show_data_seed.time_data_time[:t_ind]/10, self.show_data_seed.time_data_pd_freq_set_current[:t_ind, 0])
                        self.pdi_set_current_time.setData(self.show_data_seed.time_data_time[:t_ind]/10, self.show_data_seed.time_data_pd_freq_set_current[:t_ind, 1])
                    else:
                        self.pdi_pd_time.setData([], [])
                        self.pdi_pd_freq_time.setData([], [])
                        self.pdi_set_current_time.setData([], [])

                    x_values = np.arange(0, 2**16 + 1, 1, dtype=np.int32)
                    pd_freq_data = self.show_data_seed.time_data_pd_freq_set_current[:t_ind, 0]
                    pd_freq_min, pd_freq_max = np.min(pd_freq_data), np.max(pd_freq_data)
                    pd_freq_mean = np.mean(pd_freq_data)
                    pd_freq_cv = np.std(pd_freq_data)/pd_freq_mean if pd_freq_mean != 0 else 0

                    pd_freq_ind = np.where(self.show_data_seed.pd_freq_histogram != 0)
                    ind_min, ind_max = np.max((np.min(pd_freq_ind) - 1, 0)), np.min((np.max(pd_freq_ind) + 2, self.show_data_seed.pd_freq_histogram.size-1))
                    self.pdi_pd_freq_histogram.setData(x_values[ind_min:ind_max+1], self.show_data_seed.pd_freq_histogram.copy()[ind_min:ind_max])

                    set_current_data = self.show_data_seed.time_data_pd_freq_set_current[:t_ind, 1]
                    set_current_min, set_current_max = np.min(set_current_data), np.max(set_current_data)
                    set_current_mean = np.mean(set_current_data)
                    set_current_cv = np.std(set_current_data) / set_current_mean if set_current_mean != 0 else 0

                    set_current_ind = np.where(self.show_data_seed.pulse_current_histogram != 0)
                    ind_min, ind_max = np.max((np.min(set_current_ind) - 1, 0)), np.min(
                        (np.max(set_current_ind) + 2, self.show_data_seed.pulse_current_histogram.size - 1))
                    self.pdi_set_current_histogram.setData(x_values[ind_min:ind_max+1], self.show_data_seed.pulse_current_histogram.copy()[ind_min:ind_max])

                    x_values = x_values-2**15
                    pd_data = self.show_data_seed.time_data_pd_value[:t_ind]
                    pd_min, pd_max = np.min(pd_data), np.max(pd_data)
                    pd_mean = np.mean(pd_data)
                    pd_cv = np.std(pd_data) / pd_mean if pd_mean != 0 else 0

                    pd_ind = np.where(self.show_data_seed.pd_histogram != 0)
                    ind_min, ind_max = np.max((np.min(pd_ind) - 1, 0)), np.min(
                        (np.max(pd_ind) + 2, self.show_data_seed.pd_histogram.size - 1))
                    self.pdi_pd_histogram.setData(x_values[ind_min:ind_max+1], self.show_data_seed.pd_histogram.copy()[ind_min:ind_max])

                    self.ui.tableSeedData.setCellWidget(0, 0,
                                                        QLabel(enabled=False, text=str(np.round(pd_mean, 2)) + " uA"))
                    self.ui.tableSeedData.setCellWidget(1, 0, QLabel(enabled=False,
                                                                     text=str(np.round(pd_cv * 100, 2)) + " %"))
                    self.ui.tableSeedData.setCellWidget(2, 0, QLabel(enabled=False, text=str(pd_max) + " uA"))
                    self.ui.tableSeedData.setCellWidget(3, 0, QLabel(enabled=False, text=str(pd_min) + " uA"))

                    self.ui.tableSeedData.setCellWidget(0, 1, QLabel(enabled=False,
                                                                     text=str(np.round(pd_freq_mean/100, 2)) + " kHz"))
                    self.ui.tableSeedData.setCellWidget(1, 1, QLabel(enabled=False,
                                                                     text=str(np.round(pd_freq_cv * 100, 2)) + " %"))
                    self.ui.tableSeedData.setCellWidget(2, 1, QLabel(enabled=False, text=str(pd_freq_max/100) + " kHz"))
                    self.ui.tableSeedData.setCellWidget(3, 1, QLabel(enabled=False, text=str(pd_freq_min/100) + " kHz"))

                    self.ui.tableSeedData.setCellWidget(0, 2, QLabel(enabled=False,
                                                                     text=str(np.round(set_current_mean, 2)) + " mA"))
                    self.ui.tableSeedData.setCellWidget(1, 2, QLabel(enabled=False, text=str(
                        np.round(set_current_cv * 100, 2)) + " %"))
                    self.ui.tableSeedData.setCellWidget(2, 2,
                                                        QLabel(enabled=False, text=str(set_current_max) + " mA"))
                    self.ui.tableSeedData.setCellWidget(3, 2,
                                                        QLabel(enabled=False, text=str(set_current_min) + " mA"))

                    self.ui.leditTargetFreq.setText(str(np.round(self.show_data_seed.seed_target_freq/1000, 2)) + "kHz")
                    self.ui.leditLogPeriod.setText(str(self.show_data_seed.log_period) + " s")
                    self.ui.leditTargetTime.setText(str(self.show_data_seed.target_log_time_hours) + " h")
                    #time_left = np.max((self.show_data_seed.target_log_time_hours*3600-(self.show_data_seed.last_log-self.show_data_seed.log_start_time), 0))
                    time_left = np.max((self.show_data_seed.target_log_time_hours*3600-(time.time()-self.show_data_seed.log_start_time), 0))

                    hours = int(time_left // 3600)
                    minutes = int((time_left-hours*3600) // 60)
                    seconds = round(time_left-hours*3600 - minutes*60)
                    if seconds >= 60:
                        seconds = 0
                        minutes += 1
                        if minutes >= 60:
                            minutes = 0
                            hours += 1
                    self.ui.leditTimeLeft.setText(str(hours) + " h " + str(minutes) + " min " + str(seconds) + " s")
                    self.ui.leditTimeLeft.font().setPointSize(7)
                    self.ui.checkStopWhenReady.setEnabled(not self.show_data_seed.stopped)
                    self.ui.checkStopWhenReady.setChecked(self.show_data_seed.stop_when_ready)



app = QApplication(sys.argv)
lt = Lifetime()
lt.show()
app.exec()