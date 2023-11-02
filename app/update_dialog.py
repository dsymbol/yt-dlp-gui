from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QWidget

from ui.update_ui import Ui_w_autoupdate

class UpdateUi(QWidget, Ui_w_autoupdate):
    finished = Signal()
    selected = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.b_confirm.clicked.connect(self.on_b_confirm_clicked)

    def on_b_confirm_clicked(self):
        if self.cb_autoupdate.isChecked():
            self.selected.emit(True)
        else:
            self.selected.emit(False)
        self.finished.emit()
