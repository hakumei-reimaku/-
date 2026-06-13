"""主窗口模块 - PyQt5 图形界面
负责 UI 布局、播放列表管理、拖拽、用户交互。
业务逻辑(实际播放)委托给 player.AudioPlayer。
"""
import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSlider, QVBoxLayout, QWidget,
)

from player import AudioPlayer


# 深色主题样式表
DARK_STYLE = """
QMainWindow { background-color: #2b2b2b; }
QWidget { color: #e6e6e6; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
QLabel { color: #e6e6e6; }
QPushButton {
    background-color: #3c3f41; color: #e6e6e6;
    border: 1px solid #555; border-radius: 4px;
    padding: 6px 12px; min-width: 60px;
}
QPushButton:hover { background-color: #4c5052; }
QPushButton:pressed { background-color: #2f3133; }
QPushButton:disabled { background-color: #2f3133; color: #777; }
QSlider::groove:horizontal {
    height: 6px; background: #444; border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #1db954; border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff; width: 14px; margin: -5px 0;
    border-radius: 7px;
}
QListWidget {
    background-color: #1e1e1e; color: #e6e6e6;
    border: 1px solid #444; border-radius: 4px;
    padding: 4px;
}
QListWidget::item { padding: 6px 4px; }
QListWidget::item:selected { background-color: #1db954; color: #ffffff; }
QListWidget::item:hover { background-color: #353839; }
QStatusBar { background-color: #1e1e1e; color: #aaaaaa; }
"""


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self) -> None:
        super().__init__()
        # 业务对象
        self.player = AudioPlayer()
        self.playlist: list[str] = []     # 文件路径列表
        self.current_index: int = -1      # 当前播放曲目在列表中的索引
        self.total_duration: float = 0.0  # 当前曲目总时长(秒)
        self._slider_pressed: bool = False

        # 进度刷新定时器
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._on_timer_tick)

        # 窗口基础设置
        self.setWindowTitle("Simple Music Player")
        self.setMinimumSize(500, 420)
        self.resize(720, 520)
        self.setAcceptDrops(True)
        self.setStyleSheet(DARK_STYLE)

        self._build_ui()
        self._refresh_button_states()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ---- 顶部: 导入按钮 ----
        top_bar = QHBoxLayout()
        self.btn_import_files = QPushButton("📂  导入文件")
        self.btn_import_folder = QPushButton("📁  导入文件夹")
        self.btn_import_files.clicked.connect(self.action_import_files)
        self.btn_import_folder.clicked.connect(self.action_import_folder)
        top_bar.addWidget(self.btn_import_files)
        top_bar.addWidget(self.btn_import_folder)
        top_bar.addStretch()
        root.addLayout(top_bar)

        # ---- 当前播放信息 ----
        self.lbl_now_playing = QLabel("🎵 当前播放: 无")
        self.lbl_now_playing.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        root.addWidget(self.lbl_now_playing)

        # ---- 进度条 ----
        progress_row = QHBoxLayout()
        self.lbl_current_time = QLabel("00:00")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.lbl_total_time = QLabel("00:00")
        progress_row.addWidget(self.lbl_current_time)
        progress_row.addWidget(self.progress_slider, 1)
        progress_row.addWidget(self.lbl_total_time)
        root.addLayout(progress_row)

        # ---- 控制按钮 ----
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        self.btn_prev = QPushButton("⏮  上一曲")
        self.btn_play = QPushButton("▶  播放")
        self.btn_next = QPushButton("⏭  下一曲")
        self.btn_stop = QPushButton("⏹  停止")
        for btn in (self.btn_prev, self.btn_play, self.btn_next, self.btn_stop):
            btn.setMinimumHeight(36)
        self.btn_prev.clicked.connect(self.action_play_prev)
        self.btn_play.clicked.connect(self.action_toggle_play)
        self.btn_next.clicked.connect(self.action_play_next)
        self.btn_stop.clicked.connect(self.action_stop)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.btn_prev)
        ctrl_row.addWidget(self.btn_play)
        ctrl_row.addWidget(self.btn_next)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addStretch()
        root.addLayout(ctrl_row)

        # ---- 音量 ----
        volume_row = QHBoxLayout()
        lbl_volume_icon = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(220)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        lbl_volume = QLabel("音量")
        volume_row.addWidget(lbl_volume_icon)
        volume_row.addWidget(self.volume_slider)
        volume_row.addWidget(lbl_volume)
        volume_row.addStretch()
        root.addLayout(volume_row)

        # ---- 分割线 ----
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        root.addWidget(line)

        # ---- 播放列表标题 ----
        pl_header = QHBoxLayout()
        pl_title = QLabel("播放列表")
        pl_title.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.btn_clear = QPushButton("🗑  清空")
        self.btn_clear.clicked.connect(self.action_clear_playlist)
        pl_header.addWidget(pl_title)
        pl_header.addStretch()
        pl_header.addWidget(self.btn_clear)
        root.addLayout(pl_header)

        # ---- 播放列表 ----
        self.playlist_view = QListWidget()
        self.playlist_view.itemDoubleClicked.connect(self._on_playlist_activated)
        root.addWidget(self.playlist_view, 1)

        # 状态栏
        self.statusBar().showMessage("就绪 - 拖拽音频文件到窗口或点击 [导入文件] 按钮")

    # ------------------------------------------------------------- Drag&Drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        files: list[str] = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if os.path.isdir(path):
                # 把文件夹内所有支持的音频加入
                for name in os.listdir(path):
                    full = os.path.join(path, name)
                    if os.path.isfile(full) and AudioPlayer.is_supported(full):
                        files.append(full)
            elif os.path.isfile(path) and AudioPlayer.is_supported(path):
                files.append(path)
        if files:
            self._add_files(files)
        else:
            QMessageBox.information(
                self, "提示",
                "未发现受支持的音频文件 (MP3 / FLAC / WAV / OGG / M4A)"
            )

    # --------------------------------------------------------------- Actions
    def action_import_files(self) -> None:
        """通过对话框选择文件"""
        filt = "音频文件 (*.mp3 *.flac *.wav *.ogg *.m4a);;所有文件 (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "选择音频文件", "", filt)
        if files:
            self._add_files(files)

    def action_import_folder(self) -> None:
        """通过对话框选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        files = [
            os.path.join(folder, name)
            for name in os.listdir(folder)
            if AudioPlayer.is_supported(os.path.join(folder, name))
        ]
        if files:
            self._add_files(files)
        else:
            QMessageBox.information(self, "提示", "该文件夹中未发现受支持的音频文件")

    def _add_files(self, files: list[str]) -> None:
        """把一批文件追加到播放列表(去重)"""
        added, skipped, duplicated = 0, 0, 0
        for fp in files:
            if not AudioPlayer.is_supported(fp):
                skipped += 1
                continue
            if fp in self.playlist:
                duplicated += 1
                continue
            self.playlist.append(fp)
            self.playlist_view.addItem(os.path.basename(fp))
            added += 1

        msg = f"已添加 {added} 个文件"
        if duplicated:
            msg += f"，{duplicated} 个已存在"
        if skipped:
            msg += f"，{skipped} 个不支持"
        self.statusBar().showMessage(msg)

        if self.current_index == -1 and self.playlist:
            # 首次添加完成后,自动选中第一首,等待用户播放
            self.playlist_view.setCurrentRow(0)
        self._refresh_button_states()

    def action_clear_playlist(self) -> None:
        """清空播放列表"""
        if not self.playlist:
            return
        if QMessageBox.question(
            self, "确认", "确定清空播放列表?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.action_stop()
        self.playlist.clear()
        self.playlist_view.clear()
        self.current_index = -1
        self.total_duration = 0.0
        self.lbl_now_playing.setText("🎵 当前播放: 无")
        self.lbl_current_time.setText("00:00")
        self.lbl_total_time.setText("00:00")
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.statusBar().showMessage("播放列表已清空")
        self._refresh_button_states()

    def action_toggle_play(self) -> None:
        """播放/暂停切换"""
        if not self.playlist:
            return
        if self.current_index == -1:
            # 还没有选中任何曲目 -> 从第 0 首开始
            self._play_index(0)
            return

        status = self.player.toggle()
        if status == 'play':
            self.btn_play.setText("⏸  暂停")
            self.timer.start()
        else:
            self.btn_play.setText("▶  播放")
            self.timer.stop()

    def action_play_next(self) -> None:
        """下一曲"""
        if not self.playlist:
            return
        nxt = (self.current_index + 1) % len(self.playlist)
        self._play_index(nxt)

    def action_play_prev(self) -> None:
        """上一曲"""
        if not self.playlist:
            return
        prv = (self.current_index - 1) % len(self.playlist)
        self._play_index(prv)

    def action_stop(self) -> None:
        """停止"""
        self.player.stop()
        self.timer.stop()
        self.btn_play.setText("▶  播放")
        self.progress_slider.setValue(0)
        self.lbl_current_time.setText("00:00")
        # 总时长保持显示, 以便用户看到曲目信息

    # ----------------------------------------------------------- Playlist cb
    def _on_playlist_activated(self, item: QListWidgetItem) -> None:
        index = self.playlist_view.row(item)
        self._play_index(index)

    def _play_index(self, index: int) -> None:
        """实际播放指定索引的曲目"""
        if not (0 <= index < len(self.playlist)):
            return
        self.current_index = index
        file_path = self.playlist[index]
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lstrip('.').upper() or "AUDIO"

        # 在加载前先显示信息,给用户即时反馈
        self.lbl_now_playing.setText(f"🎵 当前播放: {file_name}  [{ext}]")
        self.playlist_view.setCurrentRow(index)

        if not self.player.load(file_path):
            QMessageBox.warning(self, "错误", f"无法播放文件: {file_name}")
            self._play_next_on_error()
            return

        self.player.set_volume(self.volume_slider.value() / 100.0)
        self.player.play(start=0.0)

        self.total_duration = AudioPlayer.get_duration(file_path)
        self.lbl_total_time.setText(self._fmt_time(self.total_duration))
        self.lbl_current_time.setText("00:00")
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(self.total_duration > 0)

        self.btn_play.setText("⏸  暂停")
        self.timer.start()
        self._refresh_button_states()
        self.statusBar().showMessage(f"正在播放: {file_name}")

    def _play_next_on_error(self) -> None:
        """当前文件出错时, 跳过并尝试播放下一首"""
        if not self.playlist:
            return
        nxt = (self.current_index + 1) % len(self.playlist)
        if nxt == self.current_index:
            # 只有一首,无法跳过
            return
        self._play_index(nxt)

    # -------------------------------------------------------------- Progress
    def _on_timer_tick(self) -> None:
        """定时器周期更新进度条"""
        if self.current_index == -1:
            return
        pos = self.player.get_position()
        if self.total_duration > 0 and not self._slider_pressed:
            value = int(min(1.0, pos / self.total_duration) * 1000)
            self.progress_slider.setValue(value)
        self.lbl_current_time.setText(self._fmt_time(pos))

        # 检测歌曲自然结束
        if not self.player.is_busy() and not self.player.is_paused:
            # pygame 报告停止, 但仍有 current_index => 播放结束
            self.action_play_next()

    def _on_slider_pressed(self) -> None:
        self._slider_pressed = True

    def _on_slider_released(self) -> None:
        if not self._slider_pressed:
            return
        self._slider_pressed = False
        if self.current_index == -1 or self.total_duration <= 0:
            return
        ratio = self.progress_slider.value() / 1000.0
        new_pos = ratio * self.total_duration
        # 重新加载并从 new_pos 播放(部分格式不支持 seek, 将退回从头)
        file_path = self.playlist[self.current_index]
        if self.player.load(file_path):
            self.player.set_volume(self.volume_slider.value() / 100.0)
            self.player.play(start=new_pos)
            self.btn_play.setText("⏸  暂停")
            self.timer.start()
            self.lbl_current_time.setText(self._fmt_time(new_pos))

    def _on_volume_changed(self, value: int) -> None:
        self.player.set_volume(value / 100.0)

    # -------------------------------------------------------------- Helpers
    @staticmethod
    def _fmt_time(seconds: float) -> str:
        """把秒数格式化为 mm:ss"""
        if seconds < 0 or seconds != seconds:  # NaN 保护
            seconds = 0
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def _refresh_button_states(self) -> None:
        """根据播放列表/当前状态启用/禁用按钮"""
        has_list = bool(self.playlist)
        has_current = self.current_index != -1
        self.btn_play.setEnabled(has_list)
        self.btn_prev.setEnabled(has_list and len(self.playlist) > 1)
        self.btn_next.setEnabled(has_list and len(self.playlist) > 1)
        self.btn_stop.setEnabled(has_current)
        self.btn_clear.setEnabled(has_list)
        self.btn_import_files.setEnabled(True)
        self.btn_import_folder.setEnabled(True)

    # ------------------------------------------------------------- Lifecycle
    def closeEvent(self, event) -> None:  # noqa: N802
        """窗口关闭前释放资源"""
        self.timer.stop()
        self.player.shutdown()
        super().closeEvent(event)
