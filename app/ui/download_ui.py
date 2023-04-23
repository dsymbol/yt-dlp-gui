# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'download.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QProgressBar, QSizePolicy,
    QVBoxLayout, QWidget)
import ui.icons_rc

class Ui_w_Downloader(object):
    def setupUi(self, w_Downloader):
        if not w_Downloader.objectName():
            w_Downloader.setObjectName(u"w_Downloader")
        w_Downloader.setWindowModality(Qt.NonModal)
        w_Downloader.resize(441, 73)
        icon = QIcon()
        icon.addFile(u":/icon/yt-dlp-gui.ico", QSize(), QIcon.Normal, QIcon.Off)
        w_Downloader.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(w_Downloader)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lb_progress = QLabel(w_Downloader)
        self.lb_progress.setObjectName(u"lb_progress")

        self.verticalLayout.addWidget(self.lb_progress, 0, Qt.AlignHCenter)

        self.pb = QProgressBar(w_Downloader)
        self.pb.setObjectName(u"pb")
        self.pb.setValue(0)

        self.verticalLayout.addWidget(self.pb)


        self.retranslateUi(w_Downloader)

        QMetaObject.connectSlotsByName(w_Downloader)
    # setupUi

    def retranslateUi(self, w_Downloader):
        w_Downloader.setWindowTitle(QCoreApplication.translate("w_Downloader", u"Fetching dependency...", None))
        self.lb_progress.setText(QCoreApplication.translate("w_Downloader", u"?: 0/0 [00:00<?, ?KB/s]", None))
    # retranslateUi

