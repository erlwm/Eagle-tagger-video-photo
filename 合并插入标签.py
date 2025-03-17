import os
import csv
import json
import glob
from datetime import datetime
from collections import defaultdict


def process_txt_files(dir_path, base_name):
    """整合目录下所有txt文件内容"""
    try:
        all_tags = set()
        # 收集所有标签
        for txt_file in glob.glob(os.path.join(dir_path, '*.txt')):
            if os.path.basename(txt_file) == f"{base_name}.txt":
                continue
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        tags = [t.strip() for t in content.split(',')]
                        all_tags.update(tags)
            except Exception as e:
                print(f"[WARNING] 文件读取失败：{txt_file} - {str(e)}")

        # 写入新文件
        new_txt = os.path.join(dir_path, f"{base_name}.txt")
        with open(new_txt, 'w', encoding='utf-8') as f:
            f.write(','.join(sorted(all_tags)))

        # 删除旧文件（保留新文件）
        for txt_file in glob.glob(os.path.join(dir_path, '*.txt')):
            if os.path.basename(txt_file) != f"{base_name}.txt":
                try:
                    os.remove(txt_file)
                except Exception as e:
                    print(f"[WARNING] 文件删除失败：{txt_file} - {str(e)}")
        return True
    except Exception as e:
        print(f"[ERROR] TXT处理失败：{str(e)}")
        return False


def filter_tags(dir_path, base_name):
    """标签过滤功能（默认注释规则）"""
    try:
        import re  # 必须添加这个导入

        txt_path = os.path.join(dir_path, f"{base_name}.txt")
        with open(txt_path, 'r+', encoding='utf-8') as f:
            tags = [t.strip() for t in f.read().split(',')]

            ##################################################
            # 取消需要的过滤规则注释（保持其他行注释状态）     #
            ##################################################

            # 1. 正则表达式过滤（示例：删除所有带数字的标签）
            # import re
            # tags = [t for t in tags if not re.search(r'\d', t)]

            # 2. 删除单独指定标签（示例：删除ugly标签）
            # exclude_tags = {"ugly"}
            # tags = [t for t in tags if t not in exclude_tags]

            # 3. 删除数字+名词格式（示例：1boy, 2girls等）
            tags = [t for t in tags if not re.match(
                r'^\d+(?:boy|girl)s?$',
                t,
                flags=re.IGNORECASE  # 忽略大小写
            )]

            # 最终处理
            filtered_tags = list(set(tags))  # 去重
            f.seek(0)
            f.write(','.join(filtered_tags))
            f.truncate()
        return True
    except Exception as e:
        print(f"[ERROR] 标签过滤失败：{str(e)}")
        return False


def translate_tags(dir_path, base_name):
    """标签翻译功能"""
    try:
        # 加载翻译字典
        trans_dict = {}
        with open('Tags-zh.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2 or not row[0].strip() or not row[1].strip():
                    print(f"[WARNING] 跳过无效行：{row}")
                    continue
                trans_dict[row[0].strip().lower()] = row[1].strip()

        # 执行翻译
        txt_path = os.path.join(dir_path, f"{base_name}.txt")
        with open(txt_path, 'r+', encoding='utf-8') as f:
            tags = [t.strip() for t in f.read().split(',')]
            translated = []
            for tag in tags:
                if any('\u4e00' <= c <= '\u9fff' for c in tag):
                    translated.append(tag)
                else:
                    translated.append(trans_dict.get(tag.lower(), tag))

            # 去重和保存
            final_tags = list(set(translated))
            f.seek(0)
            f.write(','.join(final_tags))
            f.truncate()
        return True
    except Exception as e:
        print(f"[ERROR] 翻译失败：{str(e)}")
        return False


def update_metadata(dir_path, base_name):
    """更新JSON元数据（保留原始内容）"""
    try:
        json_path = os.path.join(dir_path, 'metadata.json')
        txt_path = os.path.join(dir_path, f"{base_name}.txt")

        # 读取现有数据
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        # 读取新标签
        with open(txt_path, 'r', encoding='utf-8') as f:
            new_tags = [t.strip() for t in f.read().split(',') if t.strip()]

        # 合并标签
        existing_tags = set(data.get('tags', []))
        merged_tags = list(existing_tags.union(set(new_tags)))

        # 更新数据
        data['tags'] = merged_tags

        # 写入文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] JSON更新失败：{str(e)}")
        return False


def delete_scene_jpg(dir_path):
    """改进的JPG清理函数"""
    try:
        jpg_files = glob.glob(os.path.join(dir_path, '*-Scene-*.jpg'))
        if not jpg_files:
            print(f"[INFO] 无可删除的JPG文件：{dir_path}")
            return True  # 无文件视为成功

        deleted = False
        for jpg_file in jpg_files:
            try:
                os.remove(jpg_file)
                deleted = True
                print(f"[INFO] 已删除：{os.path.basename(jpg_file)}")
            except Exception as e:
                print(f"[WARNING] 删除失败：{jpg_file} - {str(e)}")

        # 只要没有发生异常即视为成功
        return True
    except Exception as e:
        print(f"[ERROR] JPG清理异常：{str(e)}")
        return False


def update_integration(path, status, message):
    """更新集成记录（带去重功能）"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_record = [path, status, message, timestamp]

        # 读取现有记录
        existing = []
        if os.path.exists('Integration.csv'):
            with open('Integration.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                existing = [row for row in reader if row]

        # 去重逻辑：相同路径保留最新状态
        filtered = []
        path_exists = False
        for row in existing:
            if row and row[0] == path:
                if not path_exists:
                    filtered.append(new_record)
                    path_exists = True
            else:
                filtered.append(row)
        if not path_exists:
            filtered.append(new_record)

        # 写入新记录
        with open('Integration.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(filtered)
    except Exception as e:
        print(f"[ERROR] 记录更新失败：{str(e)}")


def process_directory(dir_path, video_path):
    """更新处理流程判断逻辑"""
    try:
        base_name = os.path.basename(video_path).split('.')[0]

        steps = [
            (lambda d: process_txt_files(d, base_name), "TXT整合"),
            (lambda d: filter_tags(d, base_name), "标签过滤"),  # 新增的过滤步骤
            (lambda d: translate_tags(d, base_name), "标签翻译"),
            (lambda d: update_metadata(d, base_name), "JSON更新"),
            (lambda d: delete_scene_jpg(d), "JPG清理")
        ]

        all_success = True
        for func, step_name in steps:
            result = func(dir_path)
            if not result:
                print(f"[FAIL] 步骤失败：{step_name}")
                all_success = False
            else:
                print(f"[OK] 步骤完成：{step_name}")

        return all_success
    except Exception as e:
        print(f"[ERROR] 目录处理失败：{str(e)}")
        return False

def process_mainfile(mainfile_path):
    """主处理程序"""
    processed = set()

    # 加载历史记录
    if os.path.exists('Integration.csv'):
        with open('Integration.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 1 and row[1] == '成功':
                    processed.add(row[0])

    try:
        with open(mainfile_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0]:
                    continue

                video_path = row[0].strip()
                if video_path in processed:
                    print(f"[SKIP] 跳过已处理：{video_path}")
                    continue

                dir_path = os.path.dirname(video_path)
                if not os.path.exists(dir_path):
                    print(f"[ERROR] 目录不存在：{dir_path}")
                    update_integration(video_path, '失败', '目录不存在')
                    continue

                success = process_directory(dir_path, video_path)
                if success:
                    update_integration(video_path, '成功', '')
                    print(f"[SUCCESS] 完成处理：{video_path}")
                else:
                    update_integration(video_path, '失败', '处理流程中断')
    except Exception as e:
        print(f"[FATAL] 主流程崩溃：{str(e)}")


if __name__ == '__main__':
    process_mainfile('mainfile.csv')