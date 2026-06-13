"""一键构建脚本 (Windows)

在 Windows 上:
    python -m pip install -r requirements.txt
    python build.py

完成后在 dist/SimpleMusicPlayer.exe 即可得到单文件可执行程序。
"""
import shutil
import subprocess
import sys


def main() -> int:
    # 1. 清理旧产物
    for folder in ('build', 'dist'):
        shutil.rmtree(folder, ignore_errors=True)
    for fname in ('SimpleMusicPlayer.spec',):
        # 保留 spec 由 PyInstaller 使用, 这里不删除
        pass

    # 2. 调用 PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'SimpleMusicPlayer.spec', '--clean', '--noconfirm',
    ]
    print('[build] 执行:', ' '.join(cmd))
    code = subprocess.call(cmd)
    if code != 0:
        print('[build] PyInstaller 失败, 退出码:', code)
        return code

    print('[build] 完成 -> dist/SimpleMusicPlayer.exe')
    return 0


if __name__ == '__main__':
    sys.exit(main())
