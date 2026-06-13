"""音频播放模块
使用 Pygame 的 mixer.music 进行音频播放，使用 Mutagen 读取音频元数据(时长等)。
"""
import os
import time

import pygame
import mutagen


class AudioPlayer:
    """基于 pygame.mixer.music 的简易音频播放器封装"""

    # 支持的音频格式(小写后缀)
    SUPPORTED_FORMATS = {'.mp3', '.flac', '.wav', '.ogg', '.m4a'}

    def __init__(self):
        # 初始化 pygame 的音频混音器
        pygame.mixer.init()
        self.current_file = None      # 当前加载的文件路径
        self.is_paused = False        # 是否处于暂停状态
        self.volume = 0.7             # 当前音量 (0.0 ~ 1.0)

        # 内部用于精确计算播放位置
        self._pos_offset = 0.0        # 暂停/重新播放时累计的偏移
        self._last_play_start = 0.0   # 最近一次 play() 调用的时间戳

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """判断文件后缀是否为支持的音频格式"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.SUPPORTED_FORMATS

    def load(self, file_path: str) -> bool:
        """加载音频文件到播放器(并未开始播放)"""
        try:
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.is_paused = False
            self._pos_offset = 0.0
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[AudioPlayer] 加载失败: {file_path} -> {exc}")
            return False

    def play(self, start: float = 0.0) -> None:
        """开始播放(可指定起始时间，单位:秒)"""
        pygame.mixer.music.play(start=start)
        self.is_paused = False
        self._last_play_start = time.time()
        self._pos_offset = start

    def pause(self) -> None:
        """暂停当前播放"""
        if pygame.mixer.music.get_busy() and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            # 累计已播放时间到 offset
            self._pos_offset += time.time() - self._last_play_start

    def unpause(self) -> None:
        """从暂停中恢复"""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self._last_play_start = time.time()

    def toggle(self) -> str:
        """切换播放/暂停, 返回切换后的状态 'play' 或 'pause'"""
        if self.is_paused:
            self.unpause()
            return 'play'
        if pygame.mixer.music.get_busy():
            self.pause()
            return 'pause'
        # 当前没有播放 -> 重新从头开始
        if self.current_file:
            self.play(start=self._pos_offset)
            return 'play'
        return 'pause'

    def stop(self) -> None:
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_paused = False
        self._pos_offset = 0.0

    def get_position(self) -> float:
        """获取当前播放位置(秒)，不计入暂停时间"""
        if self.is_paused:
            return self._pos_offset
        if pygame.mixer.music.get_busy():
            return self._pos_offset + (time.time() - self._last_play_start)
        return 0.0

    def is_busy(self) -> bool:
        """是否有音乐在播放或暂停中"""
        return pygame.mixer.music.get_busy() or self.is_paused

    def set_volume(self, volume: float) -> None:
        """设置音量, 取值范围 0.0 ~ 1.0"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

    @staticmethod
    def get_duration(file_path: str) -> float:
        """读取音频文件的总时长(秒); 无法读取则返回 0.0"""
        try:
            audio = mutagen.File(file_path)
            if audio is not None and audio.info is not None:
                return float(audio.info.length)
        except Exception as exc:  # noqa: BLE001
            print(f"[AudioPlayer] 读取时长失败: {file_path} -> {exc}")
        return 0.0

    def shutdown(self) -> None:
        """关闭播放器, 释放资源"""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:  # noqa: BLE001
            pass
