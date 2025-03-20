import os
import subprocess
import configparser
import csv
import cv2


def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    config.read('processvideo.ini')
    return {
        'threshold': config.getint('processvideo', 'threshold', fallback=10),
        'min_scene_len': config.getint('processvideo', 'min_scene_len', fallback=3),
        'max_image_size': config.getint('processvideo', 'max_image_size', fallback=2048),
        'video_types': [x.strip() for x in config.get('processvideo', 'video_types', fallback='gif,webm').split(',')]
    }


def get_video_dimensions(video_path):
    """获取视频尺寸"""
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height


def analyze_scenes(csv_path):
    """分析场景数据"""
    scenes = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        # 跳过非数据行
        for row in reader:
            if row and row[0] == 'Scene Number':
                headers = row
                break
        # 读取场景数据
        for row in reader:
            if row and len(row) == len(headers):
                scenes.append(float(row[headers.index('Length (seconds)')]))
    return len(scenes), scenes


def main():
    # 读取路径文件（增加异常处理）
    try:
        with open('path.txt', 'r', encoding='utf-8-sig') as f:  # 处理BOM头
            raw_path = f.read().strip()
            # 转换路径分隔符
            video_path = os.path.abspath(raw_path.replace('\\', '/'))
    except Exception as e:
        raise RuntimeError(f"读取路径文件失败: {str(e)}")

    print(f"[DEBUG] 解析后路径: {repr(video_path)}")  # 显示原始字符串

    if not os.path.exists(video_path):
        # 给出排查建议
        print("请手动验证路径是否存在：")
        print(f'1. 资源管理器打开: {os.path.dirname(video_path)}')
        print(f'2. 检查文件名是否包含隐藏字符')
        print(f'3. 尝试缩短路径层级')
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    # 处理目录切换（增加异常捕获）
    video_dir, video_file = os.path.split(video_path)
    try:
        os.chdir(video_dir)
        print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
    except Exception as e:
        raise RuntimeError(f"无法进入视频目录 {video_dir}: {str(e)}")

    config = load_config()
    video_dir, video_file = os.path.split(video_path)
    os.chdir(video_dir)

    # 获取视频信息
    width, height = get_video_dimensions(video_file)
    max_dim = max(width, height)
    image_args = []
    if max_dim > config['max_image_size']:
        if width > height:
            image_args = ['--image-width', str(config['max_image_size'])]
        else:
            image_args = ['--image-height', str(config['max_image_size'])]

    # 判断文件类型
    ext = os.path.splitext(video_file)[1][1:].lower()
    if ext in config['video_types']:
        # 直接使用增强检测
        cmd = [
                  'scenedetect', '-i', video_file,
                  'detect-content',
                  '--threshold', str(config['threshold']),
                  '--min-scene-len', str(config['min_scene_len']),
                  'save-images', '--output', '.'
              ] + image_args
        subprocess.run(cmd, check=True)
        return

    # 生成场景列表
    csv_cmd = ['scenedetect', '-i', video_file, 'list-scenes']
    subprocess.run(csv_cmd, check=True)

    # 分析CSV文件
    csv_name = f"{os.path.splitext(video_file)[0]}-Scenes.csv"
    scene_count, scene_durations = analyze_scenes(csv_name)

    # 判断检测模式
    if scene_count < 7 or any(d > 30 for d in scene_durations):
        detector = [
            'detect-content',
            '--threshold', str(config['threshold']),
            '--min-scene-len', str(config['min_scene_len'])
        ]
    else:
        detector = ['detect-adaptive']

    # 执行最终检测
    cmd = [
              'scenedetect', '-i', video_file,
              *detector,
              'save-images', '--output', '.'
          ] + image_args
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()