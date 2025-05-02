#!/usr/bin/env python3
import subprocess
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE

console = Console()

def get_git_contributors(path):
    """Retrieve a list of contributors from the git repository."""
    try:
        result = subprocess.run(
            ['git', '-C', path, 'shortlog', '-sne', '--all'],
            stdout=subprocess.PIPE, text=True
        )
        contributors = []
        for line in result.stdout.splitlines():
            parts = line.strip().split("\t")
            if len(parts) == 2:
                contributors.append(parts[1])
        return contributors
    except Exception as e:
        console.print(f"[red]Error retrieving contributors: {e}[/red]")
        return []

def git_integration(path):
    """Show git contributions & churn metrics."""
    console.print("[bold]👥 Git Contributions[/bold]")
    contrib = get_git_contributors(path) or []
    
    # churn: count commits per file
    result = subprocess.run(
        ['git', '-C', path, 'log', '--pretty=format:', '--name-only'],
        stdout=subprocess.PIPE, text=True
    )
    churn = defaultdict(int)
    for f in result.stdout.splitlines():
        churn[f] += 1
    
    table = Table(title="File Churn (top 10)", box=SIMPLE)
    table.add_column("File")
    table.add_column("Commits", justify="right")
    for f, cnt in sorted(churn.items(), key=lambda x: -x[1])[:10]:
        table.add_row(f, str(cnt))
    console.print(table) 