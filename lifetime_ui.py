# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lifetime.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QGridLayout,
    QGroupBox, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QSpinBox, QStatusBar, QTableWidget, QTableWidgetItem,
    QWidget)

from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1270, 738)
        MainWindow.setMinimumSize(QSize(0, 640))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(13)
        self.groupBox_4.setFont(font)
        self.gridLayout_5 = QGridLayout(self.groupBox_4)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_5 = QLabel(self.groupBox_4)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setPointSize(12)
        self.label_5.setFont(font1)

        self.gridLayout_5.addWidget(self.label_5, 0, 0, 1, 1)

        self.dsboxSeedPower = QDoubleSpinBox(self.groupBox_4)
        self.dsboxSeedPower.setObjectName(u"dsboxSeedPower")
        self.dsboxSeedPower.setMinimumSize(QSize(105, 0))
        self.dsboxSeedPower.setFont(font1)
        self.dsboxSeedPower.setMinimum(0.010000000000000)
        self.dsboxSeedPower.setMaximum(10000.000000000000000)
        self.dsboxSeedPower.setValue(100.000000000000000)

        self.gridLayout_5.addWidget(self.dsboxSeedPower, 0, 1, 1, 1)

        self.label_6 = QLabel(self.groupBox_4)
        self.label_6.setObjectName(u"label_6")
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setFont(font1)

        self.gridLayout_5.addWidget(self.label_6, 1, 0, 1, 1)

        self.sboxSeedPD = QSpinBox(self.groupBox_4)
        self.sboxSeedPD.setObjectName(u"sboxSeedPD")
        self.sboxSeedPD.setFont(font1)
        self.sboxSeedPD.setMinimum(1)
        self.sboxSeedPD.setMaximum(100000)
        self.sboxSeedPD.setValue(600)

        self.gridLayout_5.addWidget(self.sboxSeedPD, 1, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox_4, 0, 3, 1, 1)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setFont(font)
        self.gridLayout_4 = QGridLayout(self.groupBox_3)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.btnBrowse = QPushButton(self.groupBox_3)
        self.btnBrowse.setObjectName(u"btnBrowse")
        self.btnBrowse.setFont(font1)

        self.gridLayout_4.addWidget(self.btnBrowse, 2, 1, 1, 1)

        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setFont(font1)

        self.gridLayout_4.addWidget(self.label_4, 0, 1, 1, 1)

        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)

        self.gridLayout_4.addWidget(self.label_3, 0, 0, 1, 1)

        self.dsboxLogPeriod = QDoubleSpinBox(self.groupBox_3)
        self.dsboxLogPeriod.setObjectName(u"dsboxLogPeriod")
        self.dsboxLogPeriod.setFont(font1)
        self.dsboxLogPeriod.setLayoutDirection(Qt.LeftToRight)
        self.dsboxLogPeriod.setDecimals(1)
        self.dsboxLogPeriod.setMinimum(0.100000000000000)
        self.dsboxLogPeriod.setValue(0.500000000000000)

        self.gridLayout_4.addWidget(self.dsboxLogPeriod, 1, 0, 1, 1)

        self.sboxLogTimeHours = QSpinBox(self.groupBox_3)
        self.sboxLogTimeHours.setObjectName(u"sboxLogTimeHours")
        self.sboxLogTimeHours.setFont(font1)
        self.sboxLogTimeHours.setMinimum(1)
        self.sboxLogTimeHours.setMaximum(100000)
        self.sboxLogTimeHours.setValue(10000)

        self.gridLayout_4.addWidget(self.sboxLogTimeHours, 1, 1, 1, 1)

        self.label_13 = QLabel(self.groupBox_3)
        self.label_13.setObjectName(u"label_13")
        sizePolicy.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy)
        self.label_13.setFont(font1)

        self.gridLayout_4.addWidget(self.label_13, 2, 0, 1, 1)

        self.leditLogLocation = QLineEdit(self.groupBox_3)
        self.leditLogLocation.setObjectName(u"leditLogLocation")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leditLogLocation.sizePolicy().hasHeightForWidth())
        self.leditLogLocation.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setPointSize(11)
        self.leditLogLocation.setFont(font2)

        self.gridLayout_4.addWidget(self.leditLogLocation, 3, 0, 1, 2)


        self.gridLayout.addWidget(self.groupBox_3, 0, 2, 1, 1)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setFont(font)
        self.gridLayout_3 = QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.leditChip = QLineEdit(self.groupBox_2)
        self.leditChip.setObjectName(u"leditChip")
        sizePolicy1.setHeightForWidth(self.leditChip.sizePolicy().hasHeightForWidth())
        self.leditChip.setSizePolicy(sizePolicy1)
        self.leditChip.setMaximumSize(QSize(200, 16777215))
        self.leditChip.setFont(font2)

        self.gridLayout_3.addWidget(self.leditChip, 3, 0, 1, 2)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMaximumSize(QSize(200, 16777215))
        self.label_2.setFont(font1)

        self.gridLayout_3.addWidget(self.label_2, 2, 0, 1, 2)

        self.leditSeed = QLineEdit(self.groupBox_2)
        self.leditSeed.setObjectName(u"leditSeed")
        sizePolicy1.setHeightForWidth(self.leditSeed.sizePolicy().hasHeightForWidth())
        self.leditSeed.setSizePolicy(sizePolicy1)
        self.leditSeed.setMaximumSize(QSize(200, 16777215))
        self.leditSeed.setFont(font2)

        self.gridLayout_3.addWidget(self.leditSeed, 1, 0, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QSize(200, 16777215))
        self.label.setFont(font1)

        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_2, 0, 1, 1, 1)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setFont(font)
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.btnConnect = QPushButton(self.groupBox)
        self.btnConnect.setObjectName(u"btnConnect")
        self.btnConnect.setEnabled(False)
        self.btnConnect.setFont(font1)

        self.gridLayout_2.addWidget(self.btnConnect, 1, 0, 1, 2)

        self.label_9 = QLabel(self.groupBox)
        self.label_9.setObjectName(u"label_9")
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)
        font3 = QFont()
        font3.setPointSize(14)
        self.label_9.setFont(font3)

        self.gridLayout_2.addWidget(self.label_9, 0, 0, 1, 1)

        self.cboxCOM = QComboBox(self.groupBox)
        self.cboxCOM.addItem("")
        self.cboxCOM.setObjectName(u"cboxCOM")
        sizePolicy1.setHeightForWidth(self.cboxCOM.sizePolicy().hasHeightForWidth())
        self.cboxCOM.setSizePolicy(sizePolicy1)
        self.cboxCOM.setMinimumSize(QSize(100, 0))
        self.cboxCOM.setFont(font1)

        self.gridLayout_2.addWidget(self.cboxCOM, 0, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)
        self.label_7.setMaximumSize(QSize(150, 16777215))
        self.label_7.setFont(font1)

        self.gridLayout_2.addWidget(self.label_7, 2, 0, 1, 1)

        self.leditDriverSerial = QLineEdit(self.groupBox)
        self.leditDriverSerial.setObjectName(u"leditDriverSerial")
        sizePolicy1.setHeightForWidth(self.leditDriverSerial.sizePolicy().hasHeightForWidth())
        self.leditDriverSerial.setSizePolicy(sizePolicy1)
        self.leditDriverSerial.setMaximumSize(QSize(150, 16777215))
        self.leditDriverSerial.setFont(font2)

        self.gridLayout_2.addWidget(self.leditDriverSerial, 2, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.tableLasers = QTableWidget(self.centralwidget)
        if (self.tableLasers.columnCount() < 12):
            self.tableLasers.setColumnCount(12)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(9, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(10, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableLasers.setHorizontalHeaderItem(11, __qtablewidgetitem11)
        self.tableLasers.setObjectName(u"tableLasers")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tableLasers.sizePolicy().hasHeightForWidth())
        self.tableLasers.setSizePolicy(sizePolicy2)
        self.tableLasers.setMinimumSize(QSize(0, 0))
        self.tableLasers.setMaximumSize(QSize(16777215, 16777215))
        font4 = QFont()
        font4.setPointSize(10)
        self.tableLasers.setFont(font4)
        self.tableLasers.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tableLasers.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableLasers.setShowGrid(True)
        self.tableLasers.horizontalHeader().setDefaultSectionSize(92)
        self.tableLasers.verticalHeader().setDefaultSectionSize(72)

        self.gridLayout.addWidget(self.tableLasers, 2, 0, 1, 6)

        self.btnStart = QPushButton(self.centralwidget)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setEnabled(False)
        self.btnStart.setMinimumSize(QSize(0, 30))
        self.btnStart.setMaximumSize(QSize(100, 16777215))
        font5 = QFont()
        font5.setPointSize(28)
        self.btnStart.setFont(font5)

        self.gridLayout.addWidget(self.btnStart, 0, 5, 1, 1)

        self.plot = PlotWidget(self.centralwidget)
        self.plot.setObjectName(u"plot")

        self.gridLayout.addWidget(self.plot, 0, 6, 3, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1270, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Seed PD1 and Power", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Seed Power", None))
        self.dsboxSeedPower.setSuffix(QCoreApplication.translate("MainWindow", u" mW", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Seed PD", None))
        self.sboxSeedPD.setSuffix(QCoreApplication.translate("MainWindow", u" uA", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Log Settings", None))
        self.btnBrowse.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Target Log Time", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Logging Period", None))
        self.dsboxLogPeriod.setSuffix(QCoreApplication.translate("MainWindow", u" s", None))
        self.sboxLogTimeHours.setSuffix(QCoreApplication.translate("MainWindow", u" h", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Log File Location", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Seed and Chip Names", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Chip", None))
        self.leditSeed.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Seed", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Driver", None))
        self.btnConnect.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"COM Port", None))
        self.cboxCOM.setItemText(0, QCoreApplication.translate("MainWindow", u"None", None))

        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Driver S/N", None))
        self.leditDriverSerial.setText("")
        ___qtablewidgetitem = self.tableLasers.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"COM Port", None));
        ___qtablewidgetitem1 = self.tableLasers.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Driver S/N", None));
        ___qtablewidgetitem2 = self.tableLasers.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Seed", None));
        ___qtablewidgetitem3 = self.tableLasers.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Chip", None));
        ___qtablewidgetitem4 = self.tableLasers.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Logging Period", None));
        ___qtablewidgetitem5 = self.tableLasers.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Seed Power", None));
        ___qtablewidgetitem6 = self.tableLasers.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"PC Target", None));
        ___qtablewidgetitem7 = self.tableLasers.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"PD1 Value", None));
        ___qtablewidgetitem8 = self.tableLasers.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("MainWindow", u"Start Time", None));
        ___qtablewidgetitem9 = self.tableLasers.horizontalHeaderItem(9)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("MainWindow", u"Run Time", None));
        ___qtablewidgetitem10 = self.tableLasers.horizontalHeaderItem(10)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("MainWindow", u"Status", None));
        ___qtablewidgetitem11 = self.tableLasers.horizontalHeaderItem(11)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("MainWindow", u"Disconnect", None));
        self.btnStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
    # retranslateUi

