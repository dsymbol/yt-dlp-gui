# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)
import ui.icons_rc

class Ui_mw_Main(object):
    def setupUi(self, mw_Main):
        if not mw_Main.objectName():
            mw_Main.setObjectName(u"mw_Main")
        mw_Main.resize(758, 581)
        icon = QIcon()
        icon.addFile(u":/icon/yt-dlp-gui.ico", QSize(), QIcon.Normal, QIcon.Off)
        mw_Main.setWindowIcon(icon)
        self.centralwidget = QWidget(mw_Main)
        self.centralwidget.setObjectName(u"centralwidget")
        font = QFont()
        font.setPointSize(9)
        self.centralwidget.setFont(font)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gb_embeds = QGroupBox(self.centralwidget)
        self.gb_embeds.setObjectName(u"gb_embeds")
        self.gb_embeds.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.gb_embeds.setFlat(False)
        self.gb_embeds.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.gb_embeds)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, -1, 0, -1)
        self.cb_metadata = QCheckBox(self.gb_embeds)
        self.cb_metadata.setObjectName(u"cb_metadata")

        self.verticalLayout.addWidget(self.cb_metadata)

        self.cb_thumbnail = QCheckBox(self.gb_embeds)
        self.cb_thumbnail.setObjectName(u"cb_thumbnail")

        self.verticalLayout.addWidget(self.cb_thumbnail)

        self.cb_subtitles = QCheckBox(self.gb_embeds)
        self.cb_subtitles.setObjectName(u"cb_subtitles")

        self.verticalLayout.addWidget(self.cb_subtitles)


        self.gridLayout.addWidget(self.gb_embeds, 0, 1, 1, 1)

        self.gb_controls = QGroupBox(self.centralwidget)
        self.gb_controls.setObjectName(u"gb_controls")
        self.verticalLayout_2 = QVBoxLayout(self.gb_controls)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pb_add = QPushButton(self.gb_controls)
        self.pb_add.setObjectName(u"pb_add")
        icon1 = QIcon()
        icon1.addFile(u":/buttons/add.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pb_add.setIcon(icon1)
        self.pb_add.setIconSize(QSize(20, 20))

        self.verticalLayout_2.addWidget(self.pb_add)

        self.pb_clear = QPushButton(self.gb_controls)
        self.pb_clear.setObjectName(u"pb_clear")
        icon2 = QIcon()
        icon2.addFile(u":/buttons/clear.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pb_clear.setIcon(icon2)
        self.pb_clear.setIconSize(QSize(20, 20))

        self.verticalLayout_2.addWidget(self.pb_clear)

        self.pb_download = QPushButton(self.gb_controls)
        self.pb_download.setObjectName(u"pb_download")
        icon3 = QIcon()
        icon3.addFile(u":/buttons/download.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pb_download.setIcon(icon3)
        self.pb_download.setIconSize(QSize(20, 20))

        self.verticalLayout_2.addWidget(self.pb_download)


        self.gridLayout.addWidget(self.gb_controls, 0, 2, 1, 1)

        self.gb_args = QGroupBox(self.centralwidget)
        self.gb_args.setObjectName(u"gb_args")
        self.verticalLayout_4 = QVBoxLayout(self.gb_args)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lo_link = QHBoxLayout()
        self.lo_link.setObjectName(u"lo_link")
        self.lo_link.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.lb_link = QLabel(self.gb_args)
        self.lb_link.setObjectName(u"lb_link")
        self.lb_link.setMinimumSize(QSize(50, 0))

        self.lo_link.addWidget(self.lb_link)

        self.le_link = QLineEdit(self.gb_args)
        self.le_link.setObjectName(u"le_link")

        self.lo_link.addWidget(self.le_link)


        self.verticalLayout_4.addLayout(self.lo_link)

        self.lo_path = QHBoxLayout()
        self.lo_path.setObjectName(u"lo_path")
        self.lb_path = QLabel(self.gb_args)
        self.lb_path.setObjectName(u"lb_path")
        self.lb_path.setMinimumSize(QSize(50, 0))

        self.lo_path.addWidget(self.lb_path)

        self.le_path = QLineEdit(self.gb_args)
        self.le_path.setObjectName(u"le_path")
        self.le_path.setEnabled(False)
        self.le_path.setReadOnly(False)

        self.lo_path.addWidget(self.le_path)

        self.tb_path = QToolButton(self.gb_args)
        self.tb_path.setObjectName(u"tb_path")

        self.lo_path.addWidget(self.tb_path)


        self.verticalLayout_4.addLayout(self.lo_path)

        self.lo_format = QHBoxLayout()
        self.lo_format.setObjectName(u"lo_format")
        self.lb_format = QLabel(self.gb_args)
        self.lb_format.setObjectName(u"lb_format")
        self.lb_format.setMinimumSize(QSize(50, 0))

        self.lo_format.addWidget(self.lb_format)

        self.dd_format = QComboBox(self.gb_args)
        self.dd_format.addItem("")
        self.dd_format.addItem("")
        self.dd_format.addItem("")
        self.dd_format.setObjectName(u"dd_format")
        self.dd_format.setMinimumSize(QSize(70, 0))

        self.lo_format.addWidget(self.dd_format)

        self.lb_cargs = QLabel(self.gb_args)
        self.lb_cargs.setObjectName(u"lb_cargs")

        self.lo_format.addWidget(self.lb_cargs)

        self.le_cargs = QLineEdit(self.gb_args)
        self.le_cargs.setObjectName(u"le_cargs")

        self.lo_format.addWidget(self.le_cargs)

        self.lb_filename = QLabel(self.gb_args)
        self.lb_filename.setObjectName(u"lb_filename")

        self.lo_format.addWidget(self.lb_filename)

        self.le_filename = QLineEdit(self.gb_args)
        self.le_filename.setObjectName(u"le_filename")

        self.lo_format.addWidget(self.le_filename)

        self.lo_format.setStretch(1, 1)
        self.lo_format.setStretch(3, 2)

        self.verticalLayout_4.addLayout(self.lo_format)


        self.gridLayout.addWidget(self.gb_args, 0, 0, 1, 1)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_3 = QGridLayout(self.frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.tw = QTreeWidget(self.frame)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(5, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(4, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(3, Qt.AlignCenter);
        __qtreewidgetitem.setTextAlignment(2, Qt.AlignCenter);
        self.tw.setHeaderItem(__qtreewidgetitem)
        self.tw.setObjectName(u"tw")
        self.tw.header().setVisible(True)

        self.gridLayout_3.addWidget(self.tw, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.frame, 1, 0, 1, 3)

        self.gridLayout.setRowStretch(0, 2)
        self.gridLayout.setRowStretch(1, 5)
        self.gridLayout.setColumnStretch(0, 5)
        self.gridLayout.setColumnStretch(1, 1)
        mw_Main.setCentralWidget(self.centralwidget)
        QWidget.setTabOrder(self.le_path, self.le_cargs)
        QWidget.setTabOrder(self.le_cargs, self.cb_metadata)
        QWidget.setTabOrder(self.cb_metadata, self.cb_thumbnail)
        QWidget.setTabOrder(self.cb_thumbnail, self.cb_subtitles)
        QWidget.setTabOrder(self.cb_subtitles, self.pb_add)
        QWidget.setTabOrder(self.pb_add, self.pb_clear)
        QWidget.setTabOrder(self.pb_clear, self.pb_download)
        QWidget.setTabOrder(self.pb_download, self.tw)

        self.retranslateUi(mw_Main)

        QMetaObject.connectSlotsByName(mw_Main)
    # setupUi

    def retranslateUi(self, mw_Main):
        mw_Main.setWindowTitle(QCoreApplication.translate("mw_Main", u"yt-dlp-gui", None))
        self.gb_embeds.setTitle(QCoreApplication.translate("mw_Main", u"Embeds", None))
        self.cb_metadata.setText(QCoreApplication.translate("mw_Main", u"Metadata", None))
        self.cb_thumbnail.setText(QCoreApplication.translate("mw_Main", u"Thumbnail", None))
        self.cb_subtitles.setText(QCoreApplication.translate("mw_Main", u"Subtitles", None))
        self.gb_controls.setTitle(QCoreApplication.translate("mw_Main", u"Controls", None))
#if QT_CONFIG(tooltip)
        self.pb_add.setToolTip(QCoreApplication.translate("mw_Main", u"<html><head/><body><p>Add</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pb_add.setText("")
#if QT_CONFIG(tooltip)
        self.pb_clear.setToolTip(QCoreApplication.translate("mw_Main", u"<html><head/><body><p>Clear</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pb_clear.setText("")
#if QT_CONFIG(tooltip)
        self.pb_download.setToolTip(QCoreApplication.translate("mw_Main", u"<html><head/><body><p>Download</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.pb_download.setText("")
        self.gb_args.setTitle(QCoreApplication.translate("mw_Main", u"Arguments", None))
        self.lb_link.setText(QCoreApplication.translate("mw_Main", u"Link", None))
        self.le_link.setPlaceholderText(QCoreApplication.translate("mw_Main", u"https://www.youtube.com/watch?v=dQw4w9WgXcQ", None))
        self.lb_path.setText(QCoreApplication.translate("mw_Main", u"Path", None))
        self.tb_path.setText(QCoreApplication.translate("mw_Main", u"...", None))
        self.lb_format.setText(QCoreApplication.translate("mw_Main", u"Format", None))
        self.dd_format.setItemText(0, QCoreApplication.translate("mw_Main", u"mp4", None))
        self.dd_format.setItemText(1, QCoreApplication.translate("mw_Main", u"mp3", None))
        self.dd_format.setItemText(2, QCoreApplication.translate("mw_Main", u"wav", None))

        self.lb_cargs.setText(QCoreApplication.translate("mw_Main", u"Custom Args", None))
        self.lb_filename.setText(QCoreApplication.translate("mw_Main", u"Filename", None))
        self.le_filename.setPlaceholderText(QCoreApplication.translate("mw_Main", u"%(title)s.%(ext)s", None))
        ___qtreewidgetitem = self.tw.headerItem()
        ___qtreewidgetitem.setText(6, QCoreApplication.translate("mw_Main", u"ETA", None));
        ___qtreewidgetitem.setText(5, QCoreApplication.translate("mw_Main", u"Speed", None));
        ___qtreewidgetitem.setText(4, QCoreApplication.translate("mw_Main", u"Status", None));
        ___qtreewidgetitem.setText(3, QCoreApplication.translate("mw_Main", u"Progress", None));
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("mw_Main", u"Size", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("mw_Main", u"Format", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("mw_Main", u"Title", None));
    # retranslateUi

