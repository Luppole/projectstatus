#!/usr/bin/env python3
import os
import re
from collections import defaultdict
from rich.console import Console
from rich.progress import Progress
from config import EXT_LANG_MAP, COMMENT_SYNTAX

console = Console()

def is_binary(file_path):
    """Check if a file is binary."""
    try:
        mime = magic.from_file(file_path, mime=True)
        return not mime.startswith('text')
    except:
        return True

def detect_shebang_language(line):
    """Detect language from shebang line."""
    if 'python' in line:
        return 'Python'
    elif 'bash' in line or 'sh' in line:
        return 'Shell'
    return None

def count_lines(file_path, language):
    """Count lines of code, blank lines, and comments in a file."""
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

def scan_directory(path, exclude_dirs, include_exts, per_file=True):
    """Scan directory for code metrics."""
    global current_stats, current_file_stats, current_path
    
    stats = defaultdict(lambda: {'code': 0, 'blank': 0, 'comments': 0})
    file_stats = {}
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
            
            rel_path = os.path.relpath(file_path, path)
            file_stats[rel_path] = {
                'language': lang,
                'code': code,
                'blank': blank,
                'comments': comments,
                'total': code + blank + comments
            }

    current_stats = stats
    current_file_stats = file_stats
    current_path = path
    
    return stats, file_stats

def print_table(stats):
    """Print language statistics table."""
    table = Table(title="Code Statistics by Language")
    table.add_column("Language")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comment Lines", justify="right")
    table.add_column("Total Lines", justify="right")

    total_code = total_blank = total_comments = 0
    
    for lang, data in sorted(stats.items(), key=lambda x: -x[1]['code']):
        total = data['code'] + data['blank'] + data['comments']
        total_code += data['code']
        total_blank += data['blank']
        total_comments += data['comments']
        
        table.add_row(
            lang, 
            str(data['code']), 
            str(data['blank']), 
            str(data['comments']),
            str(total)
        )
    
    table.add_row(
        "TOTAL", 
        str(total_code), 
        str(total_blank), 
        str(total_comments),
        str(total_code + total_blank + total_comments),
        style="bold"
    )

    console.print(table)

def print_file_table(file_stats, sort_by='code', limit=None):
    """Print per-file statistics table."""
    title = f"Per-File Code Statistics"
    if limit:
        title += f" (Top {limit} Files by {sort_by.capitalize()} Lines)"
    
    table = Table(title=title)
    table.add_column("File Path")
    table.add_column("Language")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comment Lines", justify="right")
    table.add_column("Total Lines", justify="right")

    sorted_files = sorted(
        file_stats.items(), 
        key=lambda x: -x[1][sort_by]
    )
    
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