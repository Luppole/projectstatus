#!/usr/bin/env python3
import json
import csv
import os
import time
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.box import SIMPLE

console = Console()

def export_to_json(stats, filename='loc_stats.json', file_stats=None):
    """Export statistics to JSON."""
    output = {
        'timestamp': datetime.now().isoformat(),
        'languages': stats,
        'files': file_stats if file_stats else {}
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
    console.print(f"[green]Exported to {filename}[/green]")

def export_to_csv(stats, filename='loc_stats.csv', file_stats=None):
    """Export statistics to CSV."""
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
    """Export statistics to Excel."""
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

def save_snapshot(stats, file_stats, timestamp=None):
    """Save a snapshot of the current code stats for comparison later."""
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

def show_snapshot_timeline():
    """Show timeline of saved snapshots."""
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

def compare_snapshots(current_stats, current_file_stats):
    """Compare current stats with the latest saved snapshot."""
    if not os.path.exists('.loc_history/latest.json'):
        console.print("[yellow]No previous snapshot found. Creating one now.[/yellow]")
        save_snapshot(current_stats, current_file_stats)
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
    all_languages = set(current_stats.keys()) | set(prev_langs.keys())
    
    total_prev = total_curr = 0
    
    for lang in all_languages:
        prev_loc = prev_langs.get(lang, {}).get('code', 0)
        curr_loc = current_stats.get(lang, {'code': 0})['code']
        
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
        save_snapshot(current_stats, current_file_stats) 