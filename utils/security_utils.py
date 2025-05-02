#!/usr/bin/env python3
import os
import re
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from config import SECURITY_PATTERNS, LARGE_SCRIPT_THRESHOLD
from .file_type_utils import is_binary_file

console = Console()

def security_scan(file_stats, path):
    """Perform basic security checks on files."""
    security_flags = []
    
    console.print("[bold]Running security scan...[/bold]")
    
    with Progress() as progress:
        task = progress.add_task("Checking files...", total=len(file_stats))
        
        for file_path, stats in file_stats.items():
            progress.update(task, advance=1)
            absolute_path = os.path.join(path, file_path)
            
            # Check for sensitive files
            for category, patterns in SECURITY_PATTERNS.items():
                if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in patterns):
                    security_flags.append({
                        'file': file_path,
                        'issue': f'Potentially sensitive {category}',
                        'severity': 'medium'
                    })
            
            # Check for large script files
            if stats['language'] == 'Shell' and stats['code'] > LARGE_SCRIPT_THRESHOLD:
                security_flags.append({
                    'file': file_path,
                    'issue': f'Large shell script ({stats["code"]} lines)',
                    'severity': 'low'
                })
            
            # Check for potential hardcoded secrets in code files
            if os.path.exists(absolute_path) and not is_binary_file(absolute_path):
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