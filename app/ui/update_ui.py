# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'update.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)
import ui.icons_rc

class Ui_w_autoupdate(object):
    def setupUi(self, w_autoupdate):
        if not w_autoupdate.objectName():
            w_autoupdate.setObjectName(u"w_autoupdate")
        w_autoupdate.setWindowModality(Qt.NonModal)
        w_autoupdate.resize(344, 163)
        icon = QIcon()
        icon.addFile(u":/icon/yt-dlp-gui.ico", QSize(), QIcon.Normal, QIcon.Off)
        w_autoupdate.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(w_autoupdate)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(w_autoupdate)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.verticalLayout.addWidget(self.label)

        self.cb_autoupdate = QCheckBox(w_autoupdate)
        self.cb_autoupdate.setObjectName(u"cb_autoupdate")
        self.cb_autoupdate.setChecked(True)

        self.verticalLayout.addWidget(self.cb_autoupdate)

        self.b_confirm = QPushButton(w_autoupdate)
        self.b_confirm.setObjectName(u"b_confirm")

        self.verticalLayout.addWidget(self.b_confirm)


        self.retranslateUi(w_autoupdate)

        QMetaObject.connectSlotsByName(w_autoupdate)
    # setupUi

    def retranslateUi(self, w_autoupdate):
        w_autoupdate.setWindowTitle(QCoreApplication.translate("w_autoupdate", u"Enable Automatic Updates?", None))
        self.label.setText(QCoreApplication.translate("w_autoupdate", u"Would you like to automatically install any updates to yt-dlp on startup in the future? You can change this preference in the \'conf.json\' configuration file.", None))
        self.cb_autoupdate.setText(QCoreApplication.translate("w_autoupdate", u"Check for dependency updates on startup.", None))
        self.b_confirm.setText(QCoreApplication.translate("w_autoupdate", u"OK", None))
    # retranslateUi

