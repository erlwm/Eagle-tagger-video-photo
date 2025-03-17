import os
import json
import csv
import sys
from pathlib import Path


def validate_directory(path):
    """验证输入路径有效性"""
    if not os.path.exists(path):
        raise NotADirectoryError(f"路径不存在: {path}")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"不是有效文件夹: {path}")


def process_metadata(json_path):
    """处理单个metadata.json文件"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        name = data.get('name', '')
        ext = data.get('ext', '')

        if not name or not ext:
            raise KeyError("缺少必要字段: name或ext")

        target_file = json_path.parent / f"{name}.{ext}"
        return str(target_file) if target_file.exists() else None

    except json.JSONDecodeError:
        sys.stderr.write(f"JSON解析失败: {json_path}\n")
    except Exception as e:
        sys.stderr.write(f"处理文件错误[{type(e).__name__}]: {json_path} - {str(e)}\n")
    return None


def main():
    try:
        # 获取用户输入
        target_dir = input("请输入目标文件夹地址：").strip()
        validate_directory(target_dir)

        # 初始化CSV
        csv_path = Path.cwd() / 'mainfile.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['文件路径'])

            total_count = 0
            record_count = 0

            # 遍历文件夹
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file == 'metadata.json':
                        total_count += 1
                        json_path = Path(root) / file

                        # 实时显示进度
                        sys.stdout.write(f"\r已遍历路径数: {total_count} | 最新记录路径: ")
                        sys.stdout.flush()

                        # 处理metadata文件
                        target_path = process_metadata(json_path)
                        if target_path:
                            record_count += 1
                            writer.writerow([target_path])
                            sys.stdout.write(f"{target_path[:50]}...")  # 截断长路径

            print(f"\n\n完成！共找到 {record_count} 个匹配文件")

    except Exception as e:
        sys.stderr.write(f"\n程序异常终止: {str(e)}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()