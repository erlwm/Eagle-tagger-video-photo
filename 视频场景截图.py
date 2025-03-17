import csv
import os
import sys
import re
import subprocess
import datetime
from codecs import getincrementaldecoder
from pathlib import Path


def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SceneProgress:
    """实时进度处理器（支持跨平台路径和缓冲处理）"""

    def __init__(self):
        self.progress_pattern = re.compile(
            r'Progress:\s+(\d{1,3})%|(\d{1,3})%\s+Progress',
            re.IGNORECASE
        )
        self.decoder = getincrementaldecoder('utf-8')(errors='replace')
        self.buffer = ''

    def update(self, byte_chunk):
        """处理字节流并更新进度显示"""
        # 增量解码防止字符截断
        self.buffer += self.decoder.decode(byte_chunk)

        # 查找所有匹配的进度值
        matches = []
        for match in self.progress_pattern.finditer(self.buffer):
            percent = match.group(1) or match.group(2)
            matches.append((match.start(), int(percent)))

        if matches:
            # 使用最后一个有效进度值
            last_pos, percent = matches[-1]
            self._update_display(percent)
            # 保留最后100字符防止跨块截断
            self.buffer = self.buffer[last_pos:][-100:]

    def _update_display(self, percent):
        """更新终端进度条显示"""
        bar = '■' * (percent // 2) + ' ' * (50 - percent // 2)
        sys.stdout.write(f"\r场景分析: [{bar}] {percent}%")
        sys.stdout.flush()

    def clear(self):
        sys.stdout.write('\r' + ' ' * 70 + '\r')


def main():
    main_csv = "mainfile.csv"
    record_csv = "segmentation.csv"
    processed = set()

    # 初始化处理记录
    if Path(record_csv).exists():
        try:
            with open(record_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 1 and row[1] == "成功":
                        processed.add(Path(row[0]).resolve().as_posix())
        except Exception as e:
            print(f"读取记录文件警告：{str(e)}")

    # 获取有效任务列表
    valid_tasks = []
    supported_formats = ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm', '.wmv', '.gif', '.ts')
    with open(main_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                filepath = Path(row[0].strip()).resolve()
                if filepath.suffix.lower() in supported_formats:
                    file_key = filepath.as_posix()
                    if file_key not in processed and filepath.exists():
                        valid_tasks.append(filepath)

    if not valid_tasks:
        print("所有视频已处理完成")
        return

    total_tasks = len(valid_tasks)
    print(f"发现 {total_tasks} 个待处理视频")

    with open(record_csv, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        progress = SceneProgress()

        for idx, video_path in enumerate(valid_tasks, 1):
            try:
                print(f"\n▶ 处理进度：{idx}/{total_tasks}")
                print(f"当前文件：{video_path.name}")

                # 验证文件状态
                if not video_path.is_file():
                    raise FileNotFoundError("路径不是文件")

                # 准备处理环境
                target_dir = video_path.parent
                video_name = video_path.name

                # 构建跨平台安全命令
                cmd = [
                    'scenedetect',
                    '--input', video_name,  # 使用相对路径
                    'detect-content',
                    '--threshold','11',
                    '--min-scene-len','3',
                    'save-images',
                    '--output', '.',  # 确保输出到当前目录
                ]

                # 在视频目录执行命令
                process = subprocess.Popen(
                    cmd,
                    cwd=str(target_dir),  # 关键修改：指定工作目录
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=dict(os.environ, PYTHONUNBUFFERED='1'),
                    bufsize=0
                )

                # 实时处理输出流
                while True:
                    output = process.stdout.read(1024)
                    if not output and process.poll() is not None:
                        break
                    if output:
                        progress.update(output)

                # 检查执行结果
                return_code = process.poll()
                progress.clear()
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cmd)

                # 记录成功状态
                writer.writerow([
                    video_path.as_posix(),
                    "成功",
                    "",
                    get_timestamp()
                ])
                print(f"✅ 完成：{video_path.name}")

            except subprocess.CalledProcessError as e:
                error_msg = f"命令执行失败（代码 {e.returncode}）"
                writer.writerow([
                    video_path.as_posix(),
                    "失败",
                    error_msg,
                    get_timestamp()
                ])
                print(f"❌ 错误：{error_msg}")

            except Exception as e:
                error_type = type(e).__name__
                error_msg = f"{error_type}: {str(e)}"
                writer.writerow([
                    video_path.as_posix(),
                    "失败",
                    error_msg,
                    get_timestamp()
                ])
                print(f"❌ 系统错误：{error_msg}")

            # 强制写入磁盘
            outfile.flush()
            os.fsync(outfile.fileno())


if __name__ == "__main__":
    try:
        main()
        print("\n所有任务处理完成")
    except KeyboardInterrupt:
        print("\n操作已中止")
        sys.exit(130)
    except Exception as e:
        print(f"\n致命错误：{type(e).__name__} - {str(e)}")
        sys.exit(1)