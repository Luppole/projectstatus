# requirements:
# pip install tqdm rich python-magic

import os
import re
import json
import csv
import time
import magic
import configparser
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from collections import defaultdict

console = Console()

EXT_LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JSX',
    '.tsx': 'TSX', '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cs': 'C#',
    '.go': 'Go', '.rs': 'Rust', '.swift': 'Swift', '.kt': 'Kotlin', '.m': 'Objective-C',
    '.rb': 'Ruby', '.php': 'PHP', '.html': 'HTML', '.css': 'CSS',
    '.scss': 'Sass', '.vue': 'Vue', '.sh': 'Shell', '.lua': 'Lua'
}

COMMENT_SYNTAX = {
    'Python': '#', 'JavaScript': '//', 'TypeScript': '//', 'C++': '//', 'C': '//', 'Java': '//',
    'C#': '//', 'Go': '//', 'Rust': '//', 'Swift': '//', 'Kotlin': '//', 'Objective-C': '//',
    'Ruby': '#', 'PHP': '//', 'Shell': '#', 'Lua': '--'
}

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists('.locconfig'):
        config.read('.locconfig')
        exclude_dirs = config.get('settings', 'exclude_dirs', fallback='').split(',')
        include_exts = config.get('settings', 'include_exts', fallback='').split(',')
        output_format = config.get('settings', 'output_format', fallback='table')
        return set(map(str.strip, exclude_dirs)), set(map(str.strip, include_exts)), output_format
    return set(), set(), 'table'

def is_binary(file_path):
    try:
        mime = magic.from_file(file_path, mime=True)
        return not mime.startswith('text')
    except:
        return True

def detect_shebang_language(line):
    if 'python' in line:
        return 'Python'
    elif 'bash' in line or 'sh' in line:
        return 'Shell'
    return None

def count_lines(file_path, language):
    code = blank = comments = 0
    comment_token = COMMENT_SYNTAX.get(language, None)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            stripped = line.strip()
            if not stripped:
                blank += 1
            elif comment_token and stripped.startswith(comment_token):
                comments += 1
            elif idx == 0 and line.startswith("#!"):
                detected = detect_shebang_language(line)
                if detected:
                    language = detected
                    comment_token = COMMENT_SYNTAX.get(language, None)
            else:
                code += 1
    return code, blank, comments, language

def scan_directory(path, exclude_dirs, include_exts):
    stats = defaultdict(lambda: {'code': 0, 'blank': 0, 'comments': 0})
    files = []
    for root, dirs, filenames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append(file_path)

    with Progress() as progress:
        task = progress.add_task("Scanning files...", total=len(files))
        for file_path in files:
            progress.update(task, advance=1)
            if is_binary(file_path):
                continue
            ext = os.path.splitext(file_path)[1].lower()
            if include_exts and ext not in include_exts:
                continue
            language = EXT_LANG_MAP.get(ext)
            if not language:
                continue
            code, blank, comments, lang = count_lines(file_path, language)
            stats[lang]['code'] += code
            stats[lang]['blank'] += blank
            stats[lang]['comments'] += comments

    return stats

def print_table(stats):
    table = Table(title="Code Statistics")
    table.add_column("Language")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comment Lines", justify="right")

    for lang, data in sorted(stats.items(), key=lambda x: -x[1]['code']):
        table.add_row(lang, str(data['code']), str(data['blank']), str(data['comments']))

    console.print(table)

def export_to_json(stats, filename='loc_stats.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4)
    print(f"Exported to {filename}")

def export_to_csv(stats, filename='loc_stats.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Language', 'Code', 'Blank', 'Comments'])
        for lang, data in stats.items():
            writer.writerow([lang, data['code'], data['blank'], data['comments']])
    print(f"Exported to {filename}")

def generate_github_badge(stats):
    total = sum(data['code'] for data in stats.values())
    return f"https://img.shields.io/badge/Lines%20of%20Code-{total}-blue"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Count lines of code with extended CLI")
    parser.add_argument('path', help="Path to the project")
    parser.add_argument('--export', choices=['json', 'csv'], help="Export format")
    args = parser.parse_args()

    exclude_dirs, include_exts, _ = load_config()
    start = time.time()
    stats = scan_directory(args.path, exclude_dirs, include_exts)
    end = time.time()

    print_table(stats)
    console.print(f"[green]Scanned in {end - start:.2f} seconds.[/green]")

    if args.export == 'json':
        export_to_json(stats)
    elif args.export == 'csv':
        export_to_csv(stats)

    console.print("GitHub Badge URL:")
    console.print(generate_github_badge(stats))

if __name__ == "__main__":
    main()
