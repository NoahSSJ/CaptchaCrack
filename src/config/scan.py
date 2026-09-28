import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"修改文件：{event.src_path}")

if __name__ == "__main__":
    # 要监控的文件夹，必须存在
    watch_path = Path(r"D:\CrackCaptcha\src\config")

    if not watch_path.is_dir():
        raise FileNotFoundError(f"文件夹不存在：{watch_path}")

    # 1. 创建处理员
    handler = MyHandler()

    # 2. 创建观察员
    observer = Observer()

    # 3. 安排监控任务
    observer.schedule(
        handler,
        path=str(watch_path),
        recursive=True,  # 同时监控子文件夹
    )

    # 4. 开始监控
    observer.start()
    print(f"正在监控：{watch_path}")
    print("按 Ctrl+C 停止")

    try:
        # 保持程序运行，监控由后台线程负责
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监控")
    finally:
        observer.stop()  # 通知监控线程停止
        observer.join()  # 等待监控线程结束