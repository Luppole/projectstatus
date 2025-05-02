#!/usr/bin/env python3
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.box import SIMPLE
import math

console = Console()

def calculate_maintainability_index(cc: float, loc: int, comments: int) -> float:
    """Calculate the maintainability index using the standard formula.
    
    MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(LOC)
    
    Args:
        cc: Cyclomatic complexity
        loc: Lines of code
        comments: Number of comment lines
        
    Returns:
        Maintainability index (0-100)
    """
    if loc == 0:
        return 100.0
        
    # Simplified version using just CC and LOC
    mi = 171 - 5.2 * math.log(loc) - 0.23 * cc - 16.2 * math.log(loc)
    
    # Normalize to 0-100 scale
    mi = max(0, min(100, mi))
    
    # Bonus for good documentation
    if comments > 0:
        doc_ratio = comments / loc
        if doc_ratio > 0.2:  # More than 20% comments
            mi += 5
        elif doc_ratio > 0.1:  # More than 10% comments
            mi += 2
            
    return mi

def estimate_technical_debt(file_path: Path, language: str) -> Dict[str, float]:
    """Estimate technical debt for a file.
    
    Args:
        file_path: Path to the file
        language: Programming language
        
    Returns:
        Dictionary with debt metrics
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Basic metrics
        loc = len(content.splitlines())
        comment_lines = len([l for l in content.splitlines() if l.strip().startswith(('#', '//', '/*', '*', '*/'))])
        code_lines = loc - comment_lines
        
        # Calculate cyclomatic complexity
        cc = 1  # Base complexity
        if language == 'Python':
            # Count control flow statements
            cc += content.count('if ') + content.count('elif ') + content.count('else:')
            cc += content.count('for ') + content.count('while ')
            cc += content.count('try:') + content.count('except ')
            cc += content.count('with ')
        elif language in ('JavaScript', 'TypeScript'):
            cc += content.count('if (') + content.count('else if (') + content.count('else {')
            cc += content.count('for (') + content.count('while (')
            cc += content.count('switch (') + content.count('case ')
            cc += content.count('try {') + content.count('catch (')
            
        # Calculate maintainability index
        mi = calculate_maintainability_index(cc, code_lines, comment_lines)
        
        # Estimate technical debt
        debt_factors = {
            'complexity': max(0, (cc - 10) * 0.5),  # Penalty for high complexity
            'size': max(0, (code_lines - 500) * 0.01),  # Penalty for large files
            'documentation': max(0, (0.1 - (comment_lines / code_lines)) * 10) if code_lines > 0 else 0,  # Penalty for low documentation
            'maintainability': max(0, (50 - mi) * 0.2)  # Penalty for low maintainability
        }
        
        total_debt = sum(debt_factors.values())
        
        return {
            'cyclomatic_complexity': cc,
            'maintainability_index': mi,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'debt_factors': debt_factors,
            'total_debt': total_debt
        }
        
    except Exception as e:
        console.print(f"[red]Error analyzing {file_path}: {str(e)}[/red]")
        return {
            'cyclomatic_complexity': 0,
            'maintainability_index': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'debt_factors': {},
            'total_debt': 0
        }

def calculate_code_health(file_path: Path, language: str) -> Dict[str, float]:
    """Calculate code health metrics for a file.
    
    Args:
        file_path: Path to the file
        language: Programming language
        
    Returns:
        Dictionary with health metrics
    """
    debt = estimate_technical_debt(file_path, language)
    
    # Calculate health score (0-100)
    health_score = 100 - min(100, debt['total_debt'] * 10)
    
    # Calculate individual health factors
    health_factors = {
        'complexity': max(0, 100 - (debt['cyclomatic_complexity'] * 5)),
        'maintainability': debt['maintainability_index'],
        'documentation': min(100, (debt['comment_lines'] / max(1, debt['code_lines'])) * 200),
        'size': max(0, 100 - (debt['code_lines'] / 1000) * 100)
    }
    
    return {
        'overall_health': health_score,
        'health_factors': health_factors,
        'technical_debt': debt
    }

def analyze_codebase(path: str, file_stats: Dict[str, Dict]) -> Dict[str, any]:
    """Analyze the entire codebase for code health and technical debt.
    
    Args:
        path: Root path of the codebase
        file_stats: Dictionary of file statistics
        
    Returns:
        Dictionary with codebase analysis results
    """
    results = {
        'files_analyzed': 0,
        'total_debt': 0,
        'average_health': 0,
        'language_stats': {},
        'worst_files': [],
        'best_files': []
    }
    
    file_health_scores = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing code health...", total=len(file_stats))
        
        for rel_path, stats in file_stats.items():
            progress.update(task, advance=1)
            
            file_path = Path(path) / rel_path
            language = stats['language']
            
            # Skip binary and non-code files
            if not language or language in ('Binary', 'Text', 'Markdown'):
                continue
                
            # Calculate health metrics
            health = calculate_code_health(file_path, language)
            
            # Update language stats
            if language not in results['language_stats']:
                results['language_stats'][language] = {
                    'files': 0,
                    'total_debt': 0,
                    'average_health': 0,
                    'total_loc': 0
                }
            
            lang_stats = results['language_stats'][language]
            lang_stats['files'] += 1
            lang_stats['total_debt'] += health['technical_debt']['total_debt']
            lang_stats['total_loc'] += health['technical_debt']['code_lines']
            
            # Track file scores
            file_health_scores.append((rel_path, health['overall_health']))
            results['total_debt'] += health['technical_debt']['total_debt']
            results['files_analyzed'] += 1
    
    # Calculate averages and sort files
    if results['files_analyzed'] > 0:
        results['average_health'] = sum(score for _, score in file_health_scores) / len(file_health_scores)
        
        # Sort files by health score
        file_health_scores.sort(key=lambda x: x[1])
        results['worst_files'] = file_health_scores[:5]  # 5 worst files
        results['best_files'] = file_health_scores[-5:][::-1]  # 5 best files
        
        # Calculate language averages
        for lang_stats in results['language_stats'].values():
            if lang_stats['files'] > 0:
                lang_stats['average_health'] = 100 - (lang_stats['total_debt'] / lang_stats['files'] * 10)
    
    return results

def print_code_health_report(results: Dict[str, any]) -> None:
    """Print a detailed code health report.
    
    Args:
        results: Codebase analysis results
    """
    console.print("\n[bold cyan]📊 Code Health Report[/bold cyan]")
    
    # Overall metrics
    table = Table(title="Overall Code Health", box=SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Files Analyzed", str(results['files_analyzed']))
    table.add_row("Average Health", f"{results['average_health']:.1f}%")
    table.add_row("Total Technical Debt", f"{results['total_debt']:.1f}")
    
    console.print(table)
    
    # Language breakdown
    if results['language_stats']:
        table = Table(title="Language Statistics", box=SIMPLE)
        table.add_column("Language", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("LOC", justify="right")
        table.add_column("Avg Health", justify="right")
        table.add_column("Total Debt", justify="right")
        
        for lang, stats in sorted(results['language_stats'].items()):
            table.add_row(
                lang,
                str(stats['files']),
                str(stats['total_loc']),
                f"{stats['average_health']:.1f}%",
                f"{stats['total_debt']:.1f}"
            )
        
        console.print(table)
    
    # Best and worst files
    if results['best_files']:
        table = Table(title="Best Performing Files", box=SIMPLE)
        table.add_column("File", style="cyan")
        table.add_column("Health Score", justify="right")
        
        for file, score in results['best_files']:
            table.add_row(file, f"{score:.1f}%")
        
        console.print(table)
    
    if results['worst_files']:
        table = Table(title="Files Needing Attention", box=SIMPLE)
        table.add_column("File", style="cyan")
        table.add_column("Health Score", justify="right")
        
        for file, score in results['worst_files']:
            table.add_row(file, f"{score:.1f}%")
        
        console.print(table) 