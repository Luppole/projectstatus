#!/usr/bin/env python3
# Standard library imports
import os
import time
import json
import csv
import configparser
import subprocess
import signal
import importlib
import re
from datetime import datetime
from collections import defaultdict

# Third-party imports
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.tree import Tree
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.spinner import Spinner
from rich.box import SIMPLE
from rich.theme import Theme
from rich.markdown import Markdown
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
import ast
import networkx as nx

# Local imports
from config import EXT_LANG_MAP, COMMENT_SYNTAX, THEMES, TEST_PATTERNS
from utils.analysis_utils import (
    estimate_test_coverage,
    code_quality_metrics,
    dependency_analysis,
    generate_tree_view,
    fuzzy_search_file,
    advanced_search
)
from utils.export_utils import (
    export_to_json,
    export_to_csv,
    export_to_excel,
    save_snapshot,
    show_snapshot_timeline,
    compare_snapshots
)
from utils.git_utils import git_integration
from utils.security_utils import security_scan
from utils.file_utils import (
    is_binary,
    detect_shebang_language,
    count_lines,
    scan_directory
)
from ui.theme import choose_theme
from ui.menu import (
    interactive_menu,
    export_menu,
    show_dynamic_summary,
    show_info
)

# Initialize console
console = Console()

# Global variables
current_stats = None
current_file_stats = None
current_path = None
command_registry = {}   # plugin hooks

try:
    from radon.complexity import cc_visit
except ImportError:
    cc_visit = None

# 1) Theme support
def choose_theme():
    choice = Prompt.ask("🎨 Choose theme", choices=list(THEMES.keys()), default="dark")
    console.theme = THEMES[choice]

# 2) Plugin loader
def load_plugins():
    """Load plugin modules from the plugins directory."""
    if not os.path.isdir("plugins"):
        return
    for fn in os.listdir("plugins"):
        if fn.endswith(".py"):
            name = fn[:-3]
            mod = importlib.import_module(f"plugins.{name}")
            if hasattr(mod, "register"):
                mod.register(command_registry)

# 3) Dynamic summary badge
def show_dynamic_summary(elapsed, files_count, stats):
    total_loc = sum(v["code"] for v in stats.values())
    badges = [
        f"✅ Scanned {files_count} files",
        f"⏱️ {elapsed:.2f}s",
        f"🐍 Python: {stats.get('Python',{}).get('code',0)} LOC",
        f"🚀 Total LOC: {total_loc}"
    ]
    console.print("   ".join(f"[bold cyan]{b}[/]" for b in badges))

# 4) Snapshot timeline
def show_snapshot_timeline():
    history = sorted(os.listdir(".loc_history"), reverse=True)
    table = Table(title="📆 Snapshot Timeline")
    table.add_column("Date")
    table.add_column("Change")
    for fn in history:
        if fn.endswith(".json"):
            data = json.load(open(f".loc_history/{fn}"))
            ts = data.get("timestamp",fn)
            loc = sum(v["code"] for v in data.get("languages",{}).values())
            table.add_row(ts, str(loc))
    console.print(table)

# 5) Fuzzy file search
def fuzzy_search_file(file_stats):
    completer = FuzzyWordCompleter(list(file_stats.keys()))
    sel = prompt("🔍 Search file: ", completer=completer)
    info = file_stats.get(sel)
    if info:
        table = Table(title=f"Details for {sel}")
        for k,v in info.items():
            table.add_row(k, str(v))
        console.print(table)
    else:
        console.print(f"[red]No match for {sel}[/]")

# Advanced Search & Filtering
def advanced_search(file_stats):
    """Search code by regex across files."""
    pattern = Prompt.ask("🔎 Enter regex to search")
    table = Table(title=f"Matches for /{pattern}/", box=SIMPLE)
    table.add_column("File")
    table.add_column("Hits", justify="right")
    for rel, stats in file_stats.items():
        hits = 0
        try:
            with open(os.path.join(current_path, rel), 'r', errors='ignore') as f:
                for line in f:
                    if re.search(pattern, line):
                        hits += 1
        except:
            continue
        if hits:
            table.add_row(rel, str(hits))
    console.print(table)

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
        import magic
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

def scan_directory(path, exclude_dirs, include_exts, per_file=True):
    """
    Scan directory for code metrics, always collecting per-file stats for various features
    """
    global current_stats, current_file_stats, current_path
    
    stats = defaultdict(lambda: {'code': 0, 'blank': 0, 'comments': 0})
    file_stats = {}  # For per-file breakdown
    files = []
    
    for root, dirs, filenames in os.walk(path):
        # Skip excluded directories
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
            
            # Store per-file stats (always collect for use by other features)
            rel_path = os.path.relpath(file_path, path)
            file_stats[rel_path] = {
                'language': lang,
                'code': code,
                'blank': blank,
                'comments': comments,
                'total': code + blank + comments
            }

    # Store data for use across runs
    current_stats = stats
    current_file_stats = file_stats
    current_path = path
    
    return stats, file_stats

def print_table(stats):
    """Print language statistics table"""
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
    
    # Add totals row
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
    """Print per-file statistics table"""
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
    """Export statistics to JSON"""
    output = {
        'timestamp': datetime.now().isoformat(),
        'languages': stats,
        'files': file_stats if file_stats else {}
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
    console.print(f"[green]Exported to {filename}[/green]")

def export_to_csv(stats, filename='loc_stats.csv', file_stats=None):
    """Export statistics to CSV"""
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
        console.print(f"[green]Per-file breakdown exported to {file_csv}[/green]")
        
    console.print(f"[green]Language summary exported to {filename}[/green]")

def export_to_excel(stats, filename='loc_stats.xlsx', file_stats=None):
    """Export statistics to Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        console.print("[red]openpyxl package not found. Install it with: pip install openpyxl[/red]")
        return
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Language Summary"
    
    # Create header
    headers = ['Language', 'Code Lines', 'Blank Lines', 'Comment Lines', 'Total Lines']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    # Add language data
    row = 2
    for lang, data in sorted(stats.items(), key=lambda x: -x[1]['code']):
        total = data['code'] + data['blank'] + data['comments']
        ws.cell(row=row, column=1, value=lang)
        ws.cell(row=row, column=2, value=data['code'])
        ws.cell(row=row, column=3, value=data['blank'])
        ws.cell(row=row, column=4, value=data['comments'])
        ws.cell(row=row, column=5, value=total)
        row += 1
    
    # Add total row
    total_code = sum(data['code'] for data in stats.values())
    total_blank = sum(data['blank'] for data in stats.values())
    total_comments = sum(data['comments'] for data in stats.values())
    
    ws.cell(row=row, column=1, value="TOTAL")
    ws.cell(row=row, column=2, value=total_code)
    ws.cell(row=row, column=3, value=total_blank)
    ws.cell(row=row, column=4, value=total_comments)
    ws.cell(row=row, column=5, value=total_code + total_blank + total_comments)
    
    for col in range(1, 6):
        ws.cell(row=row, column=col).font = Font(bold=True)
    
    # Auto-size columns
    for col in range(1, 6):
        ws.column_dimensions[get_column_letter(col)].auto_size = True
    
    # Add per-file sheet if available
    if file_stats:
        ws_files = wb.create_sheet(title="Per-File Breakdown")
        
        # Create header
        headers = ['File Path', 'Language', 'Code Lines', 'Blank Lines', 'Comment Lines', 'Total Lines']
        for col, header in enumerate(headers, 1):
            cell = ws_files.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
        
        # Add file data
        row = 2
        for file_path, data in sorted(file_stats.items(), key=lambda x: -x[1]['code']):
            ws_files.cell(row=row, column=1, value=file_path)
            ws_files.cell(row=row, column=2, value=data['language'])
            ws_files.cell(row=row, column=3, value=data['code'])
            ws_files.cell(row=row, column=4, value=data['blank'])
            ws_files.cell(row=row, column=5, value=data['comments'])
            ws_files.cell(row=row, column=6, value=data['total'])
            row += 1
        
        # Auto-size columns
        for col in range(1, 7):
            ws_files.column_dimensions[get_column_letter(col)].auto_size = True
    
    wb.save(filename)
    console.print(f"[green]Exported to {filename}[/green]")

def generate_github_badge(stats):
    """Generate GitHub badge URL for lines of code"""
    total = sum(data['code'] for data in stats.values())
    return f"https://img.shields.io/badge/Lines%20of%20Code-{total}-blue"

def save_snapshot(stats, file_stats, timestamp=None):
    """Save a snapshot of the current code stats for comparison later"""
    if not timestamp:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    snapshot = {
        'timestamp': timestamp,
        'languages': stats,
        'files': file_stats
    }
    
    os.makedirs('.loc_history', exist_ok=True)
    with open(f'.loc_history/snapshot-{timestamp}.json', 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    # Also save as latest for quick comparison
    with open('.loc_history/latest.json', 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    console.print(f"[green]Snapshot saved at .loc_history/snapshot-{timestamp}.json[/green]")

def compare_snapshots(stats, file_stats):
    """Compare current stats with the latest saved snapshot"""
    if not os.path.exists('.loc_history/latest.json'):
        console.print("[yellow]No previous snapshot found. Creating one now.[/yellow]")
        save_snapshot(stats, file_stats)
        return
    
    with open('.loc_history/latest.json', 'r') as f:
        previous = json.load(f)
    
    prev_timestamp = previous.get('timestamp', 'unknown')
    prev_langs = previous.get('languages', {})
    
    # Convert keys to strings if they're not already
    prev_langs = {str(k): v for k, v in prev_langs.items()}
    
    table = Table(title=f"Code Growth Comparison (Previous: {prev_timestamp})")
    table.add_column("Language")
    table.add_column("Previous LOC", justify="right")
    table.add_column("Current LOC", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")
    
    # Get all languages from both current and previous
    all_languages = set(stats.keys()) | set(prev_langs.keys())
    
    total_prev = total_curr = 0
    
    for lang in all_languages:
        prev_loc = prev_langs.get(lang, {}).get('code', 0)
        curr_loc = stats.get(lang, {'code': 0})['code']
        
        total_prev += prev_loc
        total_curr += curr_loc
        
        change = curr_loc - prev_loc
        pct_change = (change / prev_loc * 100) if prev_loc > 0 else float('inf')
        
        # Format change and percentage
        change_str = f"{change:+}"
        if change > 0:
            change_str = f"[green]{change_str}[/green]"
        elif change < 0:
            change_str = f"[red]{change_str}[/red]"
        
        if pct_change == float('inf'):
            pct_str = "N/A"
        else:
            pct_str = f"{pct_change:+.2f}%"
            if pct_change > 0:
                pct_str = f"[green]{pct_str}[/green]"
            elif pct_change < 0:
                pct_str = f"[red]{pct_str}[/red]"
        
        table.add_row(lang, str(prev_loc), str(curr_loc), change_str, pct_str)
    
    # Add total row
    total_change = total_curr - total_prev
    total_pct = (total_change / total_prev * 100) if total_prev > 0 else float('inf')
    
    total_change_str = f"{total_change:+}"
    if total_change > 0:
        total_change_str = f"[green]{total_change_str}[/green]"
    elif total_change < 0:
        total_change_str = f"[red]{total_change_str}[/red]"
    
    if total_pct == float('inf'):
        total_pct_str = "N/A"
    else:
        total_pct_str = f"{total_pct:+.2f}%"
        if total_pct > 0:
            total_pct_str = f"[green]{total_pct_str}[/green]"
        elif total_pct < 0:
            total_pct_str = f"[red]{total_pct_str}[/red]"
    
    table.add_row("TOTAL", str(total_prev), str(total_curr), total_change_str, total_pct_str, style="bold")
    
    console.print(table)
    
    # Prompt to save current as new snapshot
    if Confirm.ask("Save current stats as new snapshot?"):
        save_snapshot(stats, file_stats)

def estimate_test_coverage(file_stats):
    """Heuristic estimation of test coverage based on file paths"""
    test_files = {}
    code_files = {}
    
    test_patterns = [
        r'test[s]?/', r'test[s]?\.', r'_test\.', 
        r'spec[s]?/', r'spec[s]?\.', r'_spec\.'
    ]
    
    for file_path, stats in file_stats.items():
        is_test = any(re.search(pattern, file_path, re.IGNORECASE) for pattern in test_patterns)
        
        if is_test:
            test_files[file_path] = stats
        else:
            code_files[file_path] = stats
    
    test_loc = sum(stats['code'] for stats in test_files.values())
    code_loc = sum(stats['code'] for stats in code_files.values())
    
    # Simple ratio of test code to production code
    ratio = test_loc / code_loc if code_loc > 0 else 0
    
    coverage = {
        'test_files_count': len(test_files),
        'code_files_count': len(code_files),
        'test_loc': test_loc,
        'code_loc': code_loc,
        'test_to_code_ratio': ratio,
        'coverage_estimate': min(ratio * 100, 100)  # Simple heuristic, cap at 100%
    }
    
    # Print the results
    table = Table(title="Test Coverage Estimation (Heuristic)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Test Files", str(coverage['test_files_count']))
    table.add_row("Code Files", str(coverage['code_files_count']))
    table.add_row("Test LOC", str(coverage['test_loc']))
    table.add_row("Code LOC", str(coverage['code_loc']))
    table.add_row("Test-to-Code Ratio", f"{coverage['test_to_code_ratio']:.2f}")
    
    coverage_pct = coverage['coverage_estimate']
    coverage_str = f"{coverage_pct:.2f}%"
    
    # Color code the coverage percentage
    if coverage_pct < 30:
        coverage_str = f"[red]{coverage_str}[/red]"
    elif coverage_pct < 70:
        coverage_str = f"[yellow]{coverage_str}[/yellow]"
    else:
        coverage_str = f"[green]{coverage_str}[/green]"
    
    table.add_row("Estimated Coverage", coverage_str)
    
    console.print(table)
    
    # Print test files list
    if test_files:
        console.print("\n[bold]Test Files:[/bold]")
        for file_path in sorted(test_files.keys()):
            console.print(f"  • {file_path}")
    
    return coverage

def security_scan(file_stats, path):
    """Perform basic security checks on files"""
    security_flags = []
    
    sensitive_patterns = {
        'environment_file': [r'\.env$', r'\.env\.[a-zA-Z0-9]+$'],
        'secret_file': [r'secret[s]?\.', r'credential[s]?\.', r'password[s]?\.'],
        'private_key': [r'id_rsa$', r'\.pem$', r'\.key$', r'\.pfx$'],
        'config_file': [r'config\.', r'settings\.']
    }
    
    large_script_threshold = 1000  # Lines of code
    
    console.print("[bold]Running security scan...[/bold]")
    
    with Progress() as progress:
        task = progress.add_task("Checking files...", total=len(file_stats))
        
        for file_path, stats in file_stats.items():
            progress.update(task, advance=1)
            absolute_path = os.path.join(path, file_path)
            
            # Check for sensitive files
            for category, patterns in sensitive_patterns.items():
                if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in patterns):
                    security_flags.append({
                        'file': file_path,
                        'issue': f'Potentially sensitive {category}',
                        'severity': 'medium'
                    })
            
            # Check for large script files
            if stats['language'] == 'Shell' and stats['code'] > large_script_threshold:
                security_flags.append({
                    'file': file_path,
                    'issue': f'Large shell script ({stats["code"]} lines)',
                    'severity': 'low'
                })
            
            # Check for potential hardcoded secrets in code files
            if os.path.exists(absolute_path) and not is_binary(absolute_path):
                try:
                    with open(absolute_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                        secret_keywords = [
                            'api_key', 'apikey', 'secret', 'password', 'credential', 
                            'token', 'aws_', 'azure_', 'auth_'
                        ]
                        
                        for keyword in secret_keywords:
                            if keyword in content:
                                security_flags.append({
                                    'file': file_path,
                                    'issue': f'Potential hardcoded secret ({keyword})',
                                    'severity': 'high'
                                })
                                break
                except Exception:
                    # Skip files we can't read
                    continue
    
    # Print results
    if security_flags:
        table = Table(title="Security Scan Results")
        table.add_column("File")
        table.add_column("Issue")
        table.add_column("Severity")
        
        for flag in security_flags:
            severity = flag['severity']
            severity_color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(severity, 'white')
            
            table.add_row(
                flag['file'],
                flag['issue'],
                f"[{severity_color}]{severity.upper()}[/{severity_color}]"
            )
        
        console.print(table)
        
        console.print(f"\n[yellow]Found {len(security_flags)} potential security issues.[/yellow]")
        console.print("[yellow]Note: This is a basic scan and may include false positives.[/yellow]")
    else:
        console.print("[green]No obvious security issues found.[/green]")
    
    return security_flags

# 6) Breadcrumb tree view
def generate_tree_view(file_stats, path):
    """Generate a tree view of the project with LOC information"""
    # Create a tree structure
    tree_structure = {}
    
    for file_path, stats in file_stats.items():
        parts = file_path.split(os.sep)
        current = tree_structure
        
        # Build directory structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # File
                current[part] = stats
            else:  # Directory
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    # Convert to Rich Tree
    tree = Tree(f"📁 {os.path.basename(path) or path}")
    
    def add_to_tree(tree, structure, prefix=""):
        for name, content in sorted(structure.items()):
            if isinstance(content, dict) and not any(k in content for k in ['code', 'blank', 'comments']):
                # This is a directory
                branch = tree.add(f"📁 {name}")
                add_to_tree(branch, content, f"{prefix}/{name}")
            else:
                # This is a file
                if isinstance(content, dict) and 'code' in content:
                    tree.add(f"📄 {name} ({content['code']} LOC)")
    
    add_to_tree(tree, tree_structure)
    console.print(tree)

# 8) Plugin command execution
def run_plugin(cmd):
    """Execute a plugin command."""
    if cmd in command_registry:
        command_registry[cmd]()

def main():
    """Main entry point for the application."""
    choose_theme()
    load_plugins()
    
    # Get scan parameters
    path = Prompt.ask("📂 Path to scan", default=".")
    exclude = Prompt.ask("🚫 Exclude dirs", default="")
    include = Prompt.ask("✅ Include exts", default="")
    exclude_dirs = set(exclude.split(",")) if exclude else set()
    include_exts = set(include.split(",")) if include else set()

    # Initial scan
    start_time = time.time()
    stats, file_stats = scan_directory(path, exclude_dirs, include_exts)
    elapsed = time.time() - start_time
    
    show_dynamic_summary(elapsed, len(file_stats), stats)

    while True:
        choice = interactive_menu()
        console.clear()

        if choice == "0":
            break
        elif choice == "1":
            print_table(stats)
        elif choice == "2":
            print_file_table(file_stats)
        elif choice == "3":
            generate_tree_view(file_stats, path)
        elif choice == "4":
            fuzzy_search_file(file_stats)
        elif choice == "5":
            estimate_test_coverage(file_stats)
        elif choice == "6":
            if not os.path.exists(".loc_history"):
                console.print("[yellow]No snapshots found. Creating first snapshot now.[/yellow]")
                save_snapshot(stats, file_stats)
            show_snapshot_timeline()
        elif choice == "7":
            compare_snapshots(stats, file_stats)
        elif choice == "8":
            exp_choice = export_menu()
            if exp_choice == "1":
                export_to_json(stats, file_stats=file_stats)
            elif exp_choice == "2":
                export_to_csv(stats, file_stats=file_stats)
            elif exp_choice == "3":
                export_to_excel(stats, file_stats=file_stats)
        elif choice == "9":
            security_scan(file_stats, path)
        elif choice == "A":
            advanced_search(file_stats)
        elif choice == "Q":
            code_quality_metrics(path)
        elif choice == "G":
            git_integration(path)
        elif choice == "D":
            dependency_analysis(path)
        elif choice == "T":
            choose_theme()
        elif choice == "R":
            console.print("[yellow]Rescanning directory...[/yellow]")
            start_time = time.time()
            stats, file_stats = scan_directory(path, exclude_dirs, include_exts)
            elapsed = time.time() - start_time
            show_dynamic_summary(elapsed, len(file_stats), stats)
        elif choice == "I":
            show_info(path, file_stats, stats, command_registry)

        if choice != "0":
            Prompt.ask("\n[grey]Press Enter to return to menu[/grey]", default="")
            
    console.clear()
    console.print("[bold green]👋 Thanks for using Project Status CLI![/bold green]")

if __name__ == "__main__":
    main()

