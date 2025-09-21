import logging
import os
import sys

import qtawesome as qta
from dep_dl import DownloadWindow
from PySide6 import QtCore, QtGui, QtWidgets
from ui.main_window import Ui_MainWindow
from utils import *
from worker import Worker

os.environ["PATH"] += os.pathsep + str(root / "bin")
__version__ = ""
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s (%(module)s:%(lineno)d) %(message)s",
    handlers=[
        logging.FileHandler(root / "debug.log", encoding="utf-8", delay=True),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(str(root / "assets" / "yt-dlp-gui.ico")))
        self.pb_add.setIcon(qta.icon("mdi6.plus"))
        self.pb_add.setIconSize(QtCore.QSize(21, 21))
        self.pb_clear.setIcon(qta.icon("mdi6.trash-can-outline"))
        self.pb_clear.setIconSize(QtCore.QSize(22, 22))
        self.pb_download.setIcon(qta.icon("mdi6.download"))
        self.pb_download.setIconSize(QtCore.QSize(22, 22))
        self.te_link.setPlaceholderText(
            "https://www.youtube.com/watch?v=hTWKbfoikeg\n"
            "https://www.youtube.com/watch?v=KQetemT1sWc\n"
            "https://www.youtube.com/watch?v=yKNxeF4KMsY"
        )

        self.tw.setColumnWidth(0, 200)
        self.te_link.setFocus()
        self.load_config()
        self.statusBar.showMessage(__version__)

        self.form = DownloadWindow()
        self.form.finished.connect(self.form.close)
        self.form.finished.connect(self.show)

        self.to_dl = {}
        self.worker = {}
        self.index = 0

        self.pb_path.clicked.connect(self.button_path)
        self.pb_add.clicked.connect(self.button_add)
        self.pb_clear.clicked.connect(self.button_clear)
        self.pb_download.clicked.connect(self.button_download)

        self.tw.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tw.customContextMenuRequested.connect(self.open_menu)

    def open_menu(self, position):
        menu = QtWidgets.QMenu()

        delete_action = menu.addAction(qta.icon("mdi6.trash-can"), "Delete")
        copy_url_action = menu.addAction(qta.icon("mdi6.content-copy"), "Copy URL")
        open_folder_action = menu.addAction(qta.icon("mdi6.folder-open"), "Open Folder")

        item = self.tw.itemAt(position)

        if item:
            item_path = item.data(0, ItemRoles.PathRole)
            item_link = item.data(0, ItemRoles.LinkRole)
            action = menu.exec(self.tw.viewport().mapToGlobal(position))

            if action == delete_action:
                self.remove_item(item, 0)
            elif action == copy_url_action:
                QtWidgets.QApplication.clipboard().setText(item_link)
                logger.info(f"Copied URL to clipboard: {item_link}")
            elif action == open_folder_action:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(item_path))
                logger.info(f"Opened folder: {item_path}")

    def remove_item(self, item, column):
        item_id = item.data(0, ItemRoles.IdRole)
        item_text = item.text(0)

        logger.debug(f"Removing download ({item_id}): {item_text}")

        if worker := self.worker.get(item_id):
            worker.stop()

        self.to_dl.pop(item_id, None)
        self.tw.takeTopLevelItem(
            self.tw.indexOfTopLevelItem(item)
        )  # remove and return a top-level item

    def button_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            self.le_path.text() or QtCore.QDir.homePath(),
            QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if path:
            self.le_path.setText(path)

    def button_add(self):
        missing = []
        preset = self.dd_preset.currentText()
        links = self.te_link.toPlainText()
        path = self.le_path.text()

        if not links:
            missing.append("Video URL")
        if not path:
            missing.append("Save to")

        if missing:
            missing_fields = ", ".join(missing)
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                f"Required field{'s' if len(missing) > 1 else ''} ({missing_fields}) missing.",
            )

        self.te_link.clear()

        for link in links.split("\n"):
            link = link.strip()
            item = QtWidgets.QTreeWidgetItem(
                self.tw, [link, preset, "-", "", "Queued", "-", "-"]
            )
            pb = QtWidgets.QProgressBar()
            pb.setStyleSheet("QProgressBar { margin-bottom: 3px; }")
            pb.setTextVisible(False)
            self.tw.setItemWidget(item, 3, pb)
            [item.setTextAlignment(i, QtCore.Qt.AlignCenter) for i in range(1, 6)]
            item.setData(0, ItemRoles.IdRole, self.index)
            item.setData(0, ItemRoles.LinkRole, link)
            item.setData(0, ItemRoles.PathRole, path)

            self.to_dl[self.index] = Worker(item, self.config, link, path, preset)
            logger.info(
                f"Queue download ({self.index}) added: {self.to_dl[self.index]}"
            )
            self.index += 1

    def button_clear(self):
        if self.worker:
            return QtWidgets.QMessageBox.critical(
                self,
                "Application Message",
                "Unable to clear list because there are active downloads in progress.\n"
                "Remove a download by right clicking on it and selecting delete.",
            )

        self.worker = {}
        self.to_dl = {}
        self.tw.clear()

    def button_download(self):
        if not self.to_dl:
            return QtWidgets.QMessageBox.information(
                self,
                "Application Message",
                "Unable to download because there are no links in the list.",
            )

        for k, v in self.to_dl.items():
            self.worker[k] = v
            self.worker[k].finished.connect(self.worker[k].deleteLater)
            self.worker[k].finished.connect(lambda x: self.worker.pop(x))
            self.worker[k].progress.connect(self.update_progress)
            self.worker[k].start()

        self.to_dl = {}

    def load_config(self):
        config_path = root / "config.toml"

        try:
            self.config = load_toml(config_path)
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                self,
                "Application Message",
                f"Config file not found at: {config_path}",
            )
            QtWidgets.QApplication.exit()
        except toml.decoder.TomlDecodeError:
            QtWidgets.QMessageBox.critical(
                self,
                "Application Message",
                "Config file TOML decoding failed, check the log file for more info.",
            )
            logger.error("Config file TOML decoding failed", exc_info=True)
            QtWidgets.QApplication.exit()

        self.dd_preset.addItems(self.config["presets"].keys())
        self.dd_preset.setCurrentIndex(self.config["general"]["current_preset"])
        self.le_path.setText(self.config["general"]["path"])

    def closeEvent(self, event):
        self.config["general"]["current_preset"] = self.dd_preset.currentIndex()
        self.config["general"]["path"] = self.le_path.text()
        save_toml(root / "config.toml", self.config)
        event.accept()

    def update_progress(self, item, emit_data):
        try:
            for data in emit_data:
                index, update = data
                if index != 3:
                    item.setText(index, update)
                else:
                    pb = self.tw.itemWidget(item, index)
                    pb.setValue(round(float(update.replace("%", ""))))
        except AttributeError:
            logger.info(f"Download ({item.data(0, ItemRoles.IdRole)}) no longer exists")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
