"""SimpleMusicPlayer 程序入口
使用 PyQt5 创建 GUI 应用程序并启动主窗口。
"""
import sys

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Simple Music Player")
    app.setOrganizationName("SimpleMusicPlayer")

    window = MainWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
