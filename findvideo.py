import os
import json
import configparser
from pathlib import Path


def main():
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    # 获取配置参数
    search_paths = [
        p.strip() for p in
        config.get('findvideo', 'search_paths').split(',')
    ]
    video_exts = [
        ext.strip().lower() for ext in
        config.get('findvideo', 'video_extensions').split(',')
    ]

    # 标记是否找到文件
    found = False

    # 遍历所有搜索路径
    for base_path in search_paths:
        for root, _, files in os.walk(base_path):
            if 'metadata.json' not in files:
                continue

            metadata_path = os.path.join(root, 'metadata.json')

            try:
                # 读取并解析元数据文件
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 检查标签状态
                if '已自动标注' not in metadata.get('tags', []):
                    file_ext = metadata.get('ext', '').lower().strip()

                    # 检查扩展类型
                    if file_ext in video_exts:
                        # 构造目标文件路径
                        target_file = Path(root) / f"{metadata['name']}.{file_ext}"

                        # 写入路径记录
                        output_path = Path(__file__).parent / 'path.txt'
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(str(target_file) + '\n')

                        # 创建标注状态文件
                        tag_file = Path(root) / '待标注为已标注.txt'
                        with open(tag_file, 'w', encoding='utf-8') as f:
                            f.write('已自动标注')

                        # 找到文件后设置标记并退出
                        found = True
                        return

            except (json.JSONDecodeError, KeyError, PermissionError) as e:
                print(f"Error processing {metadata_path}: {str(e)}")
                continue

    # 如果遍历完所有路径仍未找到文件，则删除 path.txt
    if not found:
        output_path = Path(__file__).parent / 'path.txt'
        output_path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()