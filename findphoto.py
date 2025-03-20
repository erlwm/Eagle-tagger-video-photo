import configparser
import os
import json


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    params = {
        "paths": [p.strip() for p in config.get('FindPhoto', 'paths').split(';')],
        "image_exts": [ext.strip() for ext in config.get('FindPhoto', 'image_exts').split(',')]
    }
    return params

def process_metadata(filepath, valid_exts):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if "已自动标注" not in metadata.get("tags", []):
            ext = metadata.get("ext", "").lower()
            if ext in valid_exts:
                # 记录文件路径
                img_path = os.path.join(
                    os.path.dirname(filepath),
                    f"{metadata['name']}.{metadata['ext']}"
                )
                with open('path.txt', 'a', encoding='utf-8') as log:  # 网页2][网页5]
                    log.write(img_path + '\n')

                # 生成标注提示文件
                flag_file = os.path.join(
                    os.path.dirname(filepath),
                    "待标注为已标注.txt"
                )
                with open(flag_file, 'w', encoding='utf-8') as f:
                    f.write("已自动标注")
                return True
    except Exception as e:
        print(f"处理 {filepath} 时发生错误: {str(e)}")
    return False


def main():
    config = load_config()
    for root_path in config["paths"]:
        for root, dirs, files in os.walk(root_path):
            if "metadata.json" in files:
                metadata_path = os.path.join(root, "metadata.json")
                process_metadata(metadata_path, config["image_exts"])


if __name__ == "__main__":
    if os.path.exists("path.txt"):
        os.remove("path.txt")
    main()