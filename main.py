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

def scan_directory(path, exclude_dirs, include_exts, per_file=False):
    stats = defaultdict(lambda: {'code': 0, 'blank': 0, 'comments': 0})
    file_stats = {}  # For per-file breakdown
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
            
            # Update aggregate stats by language
            stats[lang]['code'] += code
            stats[lang]['blank'] += blank
            stats[lang]['comments'] += comments
            
            # Store per-file stats if requested
            if per_file:
                rel_path = os.path.relpath(file_path, path)
                file_stats[rel_path] = {
                    'language': lang,
                    'code': code,
                    'blank': blank,
                    'comments': comments,
                    'total': code + blank + comments
                }

    return stats, file_stats

def print_table(stats):
    table = Table(title="Code Statistics by Language")
    table.add_column("Language")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comment Lines", justify="right")
    table.add_column("Total Lines", justify="right")

    for lang, data in sorted(stats.items(), key=lambda x: -x[1]['code']):
        total = data['code'] + data['blank'] + data['comments']
        table.add_row(
            lang, 
            str(data['code']), 
            str(data['blank']), 
            str(data['comments']),
            str(total)
        )

    console.print(table)

def print_file_table(file_stats, sort_by='code', limit=None):
    table = Table(title=f"Per-File Code Statistics (Top {limit if limit else 'All'} Files by {sort_by.capitalize()} Lines)")
    table.add_column("File Path")
    table.add_column("Language")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comment Lines", justify="right")
    table.add_column("Total Lines", justify="right")

    # Sort files by the requested metric
    sorted_files = sorted(
        file_stats.items(), 
        key=lambda x: -x[1][sort_by]
    )
    
    # Apply limit if provided
    if limit:
        sorted_files = sorted_files[:limit]
    
    for file_path, data in sorted_files:
        table.add_row(
            file_path,
            data['language'],
            str(data['code']),
            str(data['blank']),
            str(data['comments']),
            str(data['total'])
        )

    console.print(table)

def export_to_json(stats, filename='loc_stats.json', file_stats=None):
    output = {
        'languages': stats,
        'files': file_stats if file_stats else {}
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
    print(f"Exported to {filename}")

def export_to_csv(stats, filename='loc_stats.csv', file_stats=None):
    # Export language summary
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Language', 'Code', 'Blank', 'Comments', 'Total'])
        for lang, data in stats.items():
            total = data['code'] + data['blank'] + data['comments']
            writer.writerow([lang, data['code'], data['blank'], data['comments'], total])
    
    # Export per-file breakdown if available
    if file_stats:
        file_csv = os.path.splitext(filename)[0] + '_per_file.csv'
        with open(file_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['File', 'Language', 'Code', 'Blank', 'Comments', 'Total'])
            for file_path, data in file_stats.items():
                writer.writerow([
                    file_path, 
                    data['language'], 
                    data['code'], 
                    data['blank'], 
                    data['comments'],
                    data['total']
                ])
        print(f"Per-file breakdown exported to {file_csv}")
        
    print(f"Language summary exported to {filename}")

def generate_github_badge(stats):
    total = sum(data['code'] for data in stats.values())
    return f"https://img.shields.io/badge/Lines%20of%20Code-{total}-blue"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Count lines of code with extended CLI")
    parser.add_argument('path', help="Path to the project")
    parser.add_argument('--export', choices=['json', 'csv'], help="Export format")
    parser.add_argument('--per-file', action='store_true', help="Generate per-file breakdown report")
    parser.add_argument('--sort-by', choices=['code', 'blank', 'comments', 'total'], 
                        default='code', help="Sort criterion for per-file report")
    parser.add_argument('--limit', type=int, help="Limit the number of files shown in per-file report")
    args = parser.parse_args()

    exclude_dirs, include_exts, _ = load_config()
    start = time.time()
    
    # Scan directory, gathering per-file stats if requested
    stats, file_stats = scan_directory(
        args.path, 
        exclude_dirs, 
        include_exts, 
        per_file=args.per_file
    )
    
    end = time.time()

    # Print language summary table
    print_table(stats)
    
    # Print per-file breakdown if requested
    if args.per_file and file_stats:
        print_file_table(file_stats, sort_by=args.sort_by, limit=args.limit)

    console.print(f"[green]Scanned in {end - start:.2f} seconds.[/green]")

    # Export if requested
    if args.export == 'json':
        export_to_json(stats, file_stats=file_stats if args.per_file else None)
    elif args.export == 'csv':
        export_to_csv(stats, file_stats=file_stats if args.per_file else None)

    console.print("GitHub Badge URL:")
    console.print(generate_github_badge(stats))

if __name__ == "__main__":
    main()