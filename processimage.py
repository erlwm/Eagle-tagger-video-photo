import os
import configparser
import subprocess
import mimetypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# 全局变量和锁
CONFIG = None
log_lock = threading.Lock()
config_lock = threading.Lock()

def load_config():
    """读取配置文件（带缓存和线程安全）"""
    global CONFIG
    with config_lock:
        if CONFIG is None:
            try:
                config = configparser.ConfigParser()
                config.read('config.ini', encoding='utf-8')
                CONFIG = {
                    'image_types': config['FileTypes']['type1'].split(','),
                    'video_types': config['FileTypes']['type2'].split(','),
                    'api_url': config['Server']['api_url'],
                    'log_file': config.get('Logging', 'log_file', fallback='process.log')
                }
            except Exception as e:
                log_error(f"配置文件读取失败: {str(e)}")
                exit(1)
    return CONFIG


def process_path(path_line):
    """处理单个文件路径（多线程兼容版）"""
    try:
        # 允许接收已处理过的路径字符串
        full_path = Path(path_line.strip()).resolve()
        if not full_path.exists():
            log_error(f"路径不存在: {full_path}")
            return

        file_type = determine_file_type(full_path)
        if file_type == "image":
            process_single_file(full_path)
        elif file_type == "video":
            process_video_directory(full_path.parent)
    except Exception as e:
        log_error(f"路径处理异常: {str(e)}")


def determine_file_type(file_path):
    """文件类型判断（基于扩展名和MIME类型）"""
    config = load_config()
    ext = file_path.suffix[1:].lower()

    if ext in config['image_types']:
        return "image"
    elif ext in config['video_types']:
        return "video"
    else:
        log_error(f"未识别的文件类型: {file_path}")
        return "unknown"


def process_single_file(file_path):
    """处理单个文件"""
    try:
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        curl_command = [
            'curl', '-X', 'POST',
            '-H', 'accept: application/json',
            '-F', f'file=@{file_path};type={mime_type}',
            load_config()['api_url']
        ]
        result = subprocess.run(curl_command, capture_output=True, text=True)
        save_result(file_path, result.stdout)
    except Exception as e:
        log_error(f"CURL请求失败: {str(e)}")


def process_video_directory(directory):
    """处理视频目录下的所有图片文件"""
    config = load_config()
    for item in directory.iterdir():
        if item.is_file() and item.suffix[1:].lower() in config['image_types']:
            process_single_file(item)


def save_result(file_path, curl_output):
    """结果保存与异常处理"""
    try:
        target_dir = file_path.parent
        output_file = target_dir / f"{file_path.stem}.txt"

        # 提取有效内容
        content = extract_content(curl_output)

        # 确保目录存在
        target_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    except PermissionError:
        log_error(f"写入权限不足: {output_file}")
    except IOError as e:
        log_error(f"文件写入失败: {str(e)}")


def extract_content(curl_output):
    """提取有效内容"""
    try:
        start = curl_output.find('"') + 1
        end = curl_output.rfind('"')
        return curl_output[start:end].replace('，', ',')
    except Exception:
        return "内容解析失败"


def log_error(message):
    """线程安全的日志记录"""
    with log_lock:
        config = load_config()
        with open(config['log_file'], 'a', encoding='utf-8') as f:
            f.write(f"[ERROR] {message}\n")


if __name__ == "__main__":
    try:
        # 读取所有路径并预处理
        with open('path.txt', 'r', encoding='utf-8') as f:
            paths = [line.strip() for line in f if line.strip()]

        # 创建线程池（可根据CPU核心数调整max_workers）
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(process_path, paths)

    except FileNotFoundError:
        log_error("path.txt文件不存在")
    except UnicodeDecodeError:
        log_error("文件编码错误（需UTF-8格式）")
    except Exception as e:
        log_error(f"主程序异常: {str(e)}")