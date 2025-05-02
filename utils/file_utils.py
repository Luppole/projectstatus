#!/usr/bin/env python3
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from .file_type_utils import is_binary_file, get_file_info

console = Console()

def count_lines(file_path: str) -> Tuple[int, int, int]:
    """Count lines of code, blank lines, and comments in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        code_lines = 0
        blank_lines = 0
        comment_lines = 0
        in_multiline_comment = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                blank_lines += 1
                continue
                
            # Handle multiline comments
            if in_multiline_comment:
                comment_lines += 1
                if '*/' in line:
                    in_multiline_comment = False
                continue
                
            # Check for multiline comment start
            if '/*' in line:
                in_multiline_comment = True
                comment_lines += 1
                continue
                
            # Check for single line comments
            if line.startswith(('//', '#', '--', ';')):
                comment_lines += 1
                continue
                
            code_lines += 1
            
        return code_lines, blank_lines, comment_lines
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {str(e)}[/]")
        return 0, 0, 0

def scan_directory(
    path: str,
    exclude_dirs: Optional[List[str]] = None,
    include_extensions: Optional[List[str]] = None
) -> Tuple[Dict[str, Dict], Dict[str, int]]:
    """
    Scan directory for code metrics.
    Returns: (file_stats, language_stats)
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', 'node_modules', 'venv', '.venv']
    if include_extensions is None:
        include_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.ts', '.jsx', '.tsx']
        
    file_stats = {}
    language_stats = defaultdict(lambda: {'code': 0, 'blank': 0, 'comment': 0, 'files': 0})
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning files...", total=None)
        
        for root, dirs, files in os.walk(path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)
                
                # Skip binary files
                if is_binary_file(file_path):
                    continue
                    
                # Get file info
                _, _, language = get_file_info(file_path)
                if not language:
                    continue
                    
                # Count lines
                code, blank, comment = count_lines(file_path)
                if code + blank + comment == 0:
                    continue
                    
                # Update stats
                file_stats[rel_path] = {
                    'language': language,
                    'code': code,
                    'blank': blank,
                    'comment': comment,
                    'total': code + blank + comment
                }
                
                language_stats[language]['code'] += code
                language_stats[language]['blank'] += blank
                language_stats[language]['comment'] += comment
                language_stats[language]['files'] += 1
                
                progress.update(task, advance=1)
                
    return file_stats, dict(language_stats)

def print_table(stats: Dict[str, Dict], title: str = "Language Statistics") -> None:
    """Print language statistics in a table."""
    table = Table(title=title)
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right", style="green")
    table.add_column("Code", justify="right", style="blue")
    table.add_column("Blank", justify="right", style="yellow")
    table.add_column("Comment", justify="right", style="magenta")
    table.add_column("Total", justify="right", style="red")
    
    for lang, data in sorted(stats.items(), key=lambda x: x[1]['code'], reverse=True):
        table.add_row(
            lang,
            str(data['files']),
            str(data['code']),
            str(data['blank']),
            str(data['comment']),
            str(data['code'] + data['blank'] + data['comment'])
        )
        
    console.print(table)

def print_file_table(
    file_stats: Dict[str, Dict],
    sort_by: str = 'code',
    limit: Optional[int] = None
) -> None:
    """Print per-file statistics in a table."""
    table = Table(title="File Statistics")
    table.add_column("File", style="cyan")
    table.add_column("Language", style="green")
    table.add_column("Code", justify="right", style="blue")
    table.add_column("Blank", justify="right", style="yellow")
    table.add_column("Comment", justify="right", style="magenta")
    table.add_column("Total", justify="right", style="red")
    
    # Sort files
    sorted_files = sorted(
        file_stats.items(),
        key=lambda x: x[1][sort_by],
        reverse=True
    )
    
    # Apply limit if specified
    if limit:
        sorted_files = sorted_files[:limit]
        
    for file, data in sorted_files:
        table.add_row(
            file,
            data['language'],
            str(data['code']),
            str(data['blank']),
            str(data['comment']),
            str(data['total'])
        )
        
    console.print(table) 