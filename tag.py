import os
import re
import json
import configparser
from concurrent.futures import ThreadPoolExecutor


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return {
        'regex_filter': config.get('tag_filter', 'regex', fallback=''),
        'exact_tags': [t.strip() for t in config.get('tag_filter', 'exact_tags', fallback='').split(',') if t.strip()],
        'gender_regex': config.get('tag_filter', 'gender_regex', fallback=''),
        'threads': config.getint('tag', 'threads', fallback=1)
    }


def load_translations():
    translations = {}
    try:
        with open('Tags-zh.csv', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    print(f"警告: CSV第{line_num}行为空")
                    continue
                if ',' not in line:
                    raise ValueError(f"CSV第{line_num}行格式错误，缺少逗号")
                en, zh = map(str.strip, line.split(',', 1))
                if not en or not zh:
                    raise ValueError(f"CSV第{line_num}行存在空字段")
                translations[en] = zh
    except Exception as e:
        print(f"加载翻译文件失败: {e}")
        exit(1)
    return translations


def process_tags(tags, config, translations):
    filtered = []
    for tag in tags:
        tag_clean = tag.strip()
        if config['regex_filter'] and re.search(config['regex_filter'], tag_clean, re.I):
            continue
        if tag_clean in config['exact_tags']:
            continue
        if config['gender_regex'] and re.search(config['gender_regex'], tag_clean, re.I):
            continue
        filtered.append(translations.get(tag_clean, tag_clean))
    return list(set(filtered))


def process_directory(dir_path, config, translations):
    # 合并标签
    tags = set()
    for filename in os.listdir(dir_path):
        if filename.endswith('.txt'):
            with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    tags.update([t.strip() for t in re.split(r',+', content)])

    # 过滤翻译
    processed_tags = process_tags(tags, config, translations)

    # 更新metadata.json
    meta_path = os.path.join(dir_path, 'metadata.json')
    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                existing = set(data.get('tags', []))
                data['tags'] = list(existing.union(processed_tags))
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()
        else:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({'tags': processed_tags}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"更新metadata失败: {e}")

    # 清理文件
    for filename in os.listdir(dir_path):
        if any([filename.endswith(ext) for ext in ('.txt', '.csv')]) or '-Scene-' in filename:
            try:
                os.remove(os.path.join(dir_path, filename))
            except:
                pass


def main():
    config = load_config()
    translations = load_translations()

    with open('path.txt', 'r', encoding='utf-8') as f:
        paths = [os.path.dirname(os.path.normpath(line.strip())) for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=config['threads']) as executor:
        for path in paths:
            executor.submit(process_directory, path, config, translations)


if __name__ == '__main__':
    main()