import logging
import subprocess as sp
import json
import sys

import qtawesome as qta
from PySide6 import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)


class PlaylistFetcher(QtCore.QThread):
    """Worker thread to fetch playlist information."""
    finished = QtCore.Signal(list)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            self.progress.emit("Fetching playlist information...")
            create_window = sp.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--no-warnings",
                self.url
            ]
            
            result = sp.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=create_window,
            )
            
            if result.returncode != 0:
                self.error.emit(f"Failed to fetch playlist: {result.stderr}")
                return
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        videos.append({
                            'id': data.get('id', ''),
                            'title': data.get('title', 'Unknown Title'),
                            'url': data.get('url') or data.get('webpage_url') or f"https://www.youtube.com/watch?v={data.get('id', '')}",
                            'duration': data.get('duration_string', data.get('duration', '')),
                            'index': len(videos) + 1
                        })
                    except json.JSONDecodeError:
                        continue
            
            if not videos:
                self.error.emit("No videos found in playlist")
                return
                
            self.finished.emit(videos)
            
        except Exception as e:
            logger.error(f"Error fetching playlist: {e}", exc_info=True)
            self.error.emit(str(e))


class PlaylistPickerDialog(QtWidgets.QDialog):
    """Dialog to select specific videos from a playlist."""
    
    def __init__(self, parent=None, url=""):
        super().__init__(parent)
        self.url = url
        self.selected_urls = []
        self.videos = []
        self.setup_ui()
        self.fetch_playlist()
    
    def setup_ui(self):
        self.setWindowTitle("Select Videos from Playlist")
        self.setMinimumSize(700, 500)
        self.resize(750, 550)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Status label
        self.status_label = QtWidgets.QLabel("Fetching playlist...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Video list with checkboxes
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.list_widget.hide()
        layout.addWidget(self.list_widget)
        
        # Selection buttons
        self.selection_layout = QtWidgets.QHBoxLayout()
        
        self.select_all_btn = QtWidgets.QPushButton("Select All")
        self.select_all_btn.setIcon(qta.icon("mdi6.checkbox-multiple-marked"))
        self.select_all_btn.clicked.connect(self.select_all)
        self.selection_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        self.deselect_all_btn.setIcon(qta.icon("mdi6.checkbox-multiple-blank-outline"))
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.selection_layout.addWidget(self.deselect_all_btn)
        
        self.selection_layout.addStretch()
        
        self.selected_count_label = QtWidgets.QLabel("0 videos selected")
        self.selection_layout.addWidget(self.selected_count_label)
        
        layout.addLayout(self.selection_layout)
        
        # Hide selection buttons initially
        self.select_all_btn.hide()
        self.deselect_all_btn.hide()
        self.selected_count_label.hide()
        
        # Dialog buttons
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.button_box)
    
    def fetch_playlist(self):
        self.fetcher = PlaylistFetcher(self.url)
        self.fetcher.finished.connect(self.on_playlist_fetched)
        self.fetcher.error.connect(self.on_fetch_error)
        self.fetcher.progress.connect(self.on_progress)
        self.fetcher.start()
    
    def on_progress(self, message):
        self.status_label.setText(message)
    
    def on_fetch_error(self, error_message):
        self.progress_bar.hide()
        self.status_label.setText(f"Error: {error_message}")
        logger.error(f"Playlist fetch error: {error_message}")
    
    def on_playlist_fetched(self, videos):
        self.videos = videos
        self.progress_bar.hide()
        self.status_label.setText(f"Found {len(videos)} videos in playlist")
        
        self.list_widget.show()
        self.select_all_btn.show()
        self.deselect_all_btn.show()
        self.selected_count_label.show()
        
        for video in videos:
            item = QtWidgets.QListWidgetItem()
            checkbox = QtWidgets.QCheckBox()
            
            # Format duration
            duration = video.get('duration', '')
            if isinstance(duration, (int, float)):
                mins, secs = divmod(int(duration), 60)
                hours, mins = divmod(mins, 60)
                if hours:
                    duration = f"{hours}:{mins:02d}:{secs:02d}"
                else:
                    duration = f"{mins}:{secs:02d}"
            
            duration_str = f" [{duration}]" if duration else ""
            checkbox.setText(f"{video['index']}. {video['title']}{duration_str}")
            checkbox.setProperty("video_url", video['url'])
            checkbox.stateChanged.connect(self.update_selection_count)
            
            item.setSizeHint(QtCore.QSize(0, 30))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, checkbox)
        
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        self.update_selection_count()
    
    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            checkbox.setChecked(True)
    
    def deselect_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            checkbox.setChecked(False)
    
    def update_selection_count(self):
        count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            if checkbox and checkbox.isChecked():
                count += 1
        
        self.selected_count_label.setText(f"{count} video{'s' if count != 1 else ''} selected")
    
    def get_selected_urls(self):
        """Return list of selected video URLs."""
        urls = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            if checkbox and checkbox.isChecked():
                url = checkbox.property("video_url")
                if url:
                    urls.append(url)
        return urls
    
    def accept(self):
        self.selected_urls = self.get_selected_urls()
        if not self.selected_urls:
            QtWidgets.QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one video to download."
            )
            return
        super().accept()
