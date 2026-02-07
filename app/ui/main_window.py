# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(770, 570)
        self.action_about = QAction(MainWindow)
        self.action_about.setObjectName(u"action_about")
        self.action_exit = QAction(MainWindow)
        self.action_exit.setObjectName(u"action_exit")
        self.action_clear_url_list = QAction(MainWindow)
        self.action_clear_url_list.setObjectName(u"action_clear_url_list")
        self.action_open_bin_folder = QAction(MainWindow)
        self.action_open_bin_folder.setObjectName(u"action_open_bin_folder")
        self.action_open_log_folder = QAction(MainWindow)
        self.action_open_log_folder.setObjectName(u"action_open_log_folder")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        font = QFont()
        font.setPointSize(9)
        self.centralwidget.setFont(font)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gb_params = QGroupBox(self.centralwidget)
        self.gb_params.setObjectName(u"gb_params")
        self.gridLayout = QGridLayout(self.gb_params)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lb_path = QLabel(self.gb_params)
        self.lb_path.setObjectName(u"lb_path")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_path.sizePolicy().hasHeightForWidth())
        self.lb_path.setSizePolicy(sizePolicy)
        self.lb_path.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.lb_path, 2, 0, 1, 1)

        self.pb_path = QPushButton(self.gb_params)
        self.pb_path.setObjectName(u"pb_path")

        self.gridLayout.addWidget(self.pb_path, 2, 2, 1, 1)

        self.pb_add = QPushButton(self.gb_params)
        self.pb_add.setObjectName(u"pb_add")

        self.gridLayout.addWidget(self.pb_add, 2, 4, 1, 1)

        self.le_path = QLineEdit(self.gb_params)
        self.le_path.setObjectName(u"le_path")
        self.le_path.setEnabled(True)
        self.le_path.setReadOnly(True)

        self.gridLayout.addWidget(self.le_path, 2, 1, 1, 1)

        self.lb_link = QLabel(self.gb_params)
        self.lb_link.setObjectName(u"lb_link")
        self.lb_link.setMinimumSize(QSize(0, 0))

        self.gridLayout.addWidget(self.lb_link, 0, 0, 1, 1)

        self.dd_preset = QComboBox(self.gb_params)
        self.dd_preset.setObjectName(u"dd_preset")

        self.gridLayout.addWidget(self.dd_preset, 2, 3, 1, 1)

        self.te_link = QPlainTextEdit(self.gb_params)
        self.te_link.setObjectName(u"te_link")

        self.gridLayout.addWidget(self.te_link, 0, 1, 1, 4)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 5)
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setColumnStretch(3, 2)

        self.verticalLayout.addWidget(self.gb_params)

        self.gb_downloads = QGroupBox(self.centralwidget)
        self.gb_downloads.setObjectName(u"gb_downloads")
        self.gridLayout_3 = QGridLayout(self.gb_downloads)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.tw = QTreeWidget(self.gb_downloads)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(5, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(4, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(3, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(2, Qt.AlignCenter);
        self.tw.setHeaderItem(__qtreewidgetitem)
        self.tw.setObjectName(u"tw")
        self.tw.header().setVisible(True)

        self.gridLayout_3.addWidget(self.tw, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.gb_downloads)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.pb_clear = QPushButton(self.centralwidget)
        self.pb_clear.setObjectName(u"pb_clear")
        self.pb_clear.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.pb_clear)

        self.pb_download = QPushButton(self.centralwidget)
        self.pb_download.setObjectName(u"pb_download")
        self.pb_download.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.pb_download)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 5)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 770, 33))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuEdit = QMenu(self.menuBar)
        self.menuEdit.setObjectName(u"menuEdit")
        MainWindow.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuEdit.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.action_open_bin_folder)
        self.menuFile.addAction(self.action_open_log_folder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.action_exit)
        self.menuHelp.addAction(self.action_about)
        self.menuEdit.addAction(self.action_clear_url_list)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"yt-dlp-gui", None))
        self.action_about.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.action_exit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.action_clear_url_list.setText(QCoreApplication.translate("MainWindow", u"Clear URL List", None))
        self.action_open_bin_folder.setText(QCoreApplication.translate("MainWindow", u"Open Binaries Folder", None))
        self.action_open_log_folder.setText(QCoreApplication.translate("MainWindow", u"Open Log Folder", None))
        self.gb_params.setTitle(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.lb_path.setText(QCoreApplication.translate("MainWindow", u"Save to", None))
        self.pb_path.setText(QCoreApplication.translate("MainWindow", u"Browse...", None))
        self.lb_link.setText(QCoreApplication.translate("MainWindow", u"Video URL(s)", None))
        self.gb_downloads.setTitle(QCoreApplication.translate("MainWindow", u"Downloads", None))
        ___qtreewidgetitem = self.tw.headerItem()
        ___qtreewidgetitem.setText(6, QCoreApplication.translate("MainWindow", u"ETA", None));
        ___qtreewidgetitem.setText(5, QCoreApplication.translate("MainWindow", u"Speed", None));
        ___qtreewidgetitem.setText(4, QCoreApplication.translate("MainWindow", u"Status", None));
        ___qtreewidgetitem.setText(3, QCoreApplication.translate("MainWindow", u"Progress", None));
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("MainWindow", u"Size", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("MainWindow", u"Preset", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("MainWindow", u"Title", None));
#if QT_CONFIG(tooltip)
        self.pb_clear.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Clear</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pb_clear.setText("")
#if QT_CONFIG(tooltip)
        self.pb_download.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Download</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pb_download.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
    # retranslateUi

