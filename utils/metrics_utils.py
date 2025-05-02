#!/usr/bin/env python3
import os
import ast
import re
import json
import hashlib
import asyncio
import aiofiles
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.box import SIMPLE
import math

console = Console()

class CodeHealthCache:
    """Cache for code health analysis results."""
    
    def __init__(self, cache_dir: str = ".projectstatus/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, file_path: Path) -> Path:
        """Get cache file path for a given file."""
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return self.cache_dir / f"health_{file_hash}.json"
        
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file contents and modification time."""
        stat = file_path.stat()
        return hashlib.md5(f"{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()
        
    def get_cached_health(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get cached health metrics if they exist and are valid."""
        cache_path = self._get_cache_path(file_path)
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            # Check if file has changed
            if cache_data.get('file_hash') != self._get_file_hash(file_path):
                return None
                
            return cache_data.get('health_metrics')
        except Exception:
            return None
            
    def save_health_metrics(self, file_path: Path, health_metrics: Dict[str, Any]) -> None:
        """Save health metrics to cache."""
        cache_path = self._get_cache_path(file_path)
        cache_data = {
            'file_hash': self._get_file_hash(file_path),
            'health_metrics': health_metrics,
            'timestamp': time.time()
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
            
    def clear_cache(self) -> None:
        """Clear all cached health metrics."""
        for cache_file in self.cache_dir.glob("health_*.json"):
            cache_file.unlink()

class ParallelAnalyzer:
    """Parallel code health analyzer."""
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = True):
        self.max_workers = max_workers or os.cpu_count()
        self.use_processes = use_processes
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers) if use_processes else ThreadPoolExecutor(max_workers=self.max_workers)
        
    async def analyze_file(self, file_path: Path, language: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze a single file's health metrics."""
        try:
            health = calculate_code_health(file_path, language)
            return str(file_path), health
        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {str(e)}[/red]")
            return str(file_path), {}
            
    async def analyze_files(self, base_path: Path, files: List[str], cache: CodeHealthCache) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple files in parallel."""
        results = {}
        
        for rel_path in files:
            file_path = base_path / rel_path
            language = 'Python'  # We're focusing on Python files for now
            
            # Check cache first
            cached_health = cache.get_cached_health(file_path)
            if cached_health:
                results[rel_path] = cached_health
                continue
                
            # Analyze file
            try:
                health = calculate_code_health(file_path, language)
                results[rel_path] = health
                cache.save_health_metrics(file_path, health)
            except Exception as e:
                console.print(f"[red]Error analyzing {rel_path}: {str(e)}[/red]")
                continue
                
        return results
        
    def __del__(self):
        """Cleanup executor on deletion."""
        self.executor.shutdown(wait=False)

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

def analyze_codebase(path: str, file_stats: Dict[str, Dict]) -> Dict:
    """Analyze codebase for health and technical debt."""
    console = Console()
    cache = CodeHealthCache()
    analyzer = ParallelAnalyzer()
    
    # Convert path to Path object
    base_path = Path(path)
    
    # Get all Python files
    files_to_analyze = []
    for rel_path, stats in file_stats.items():
        if stats.get('language') == 'Python' and not stats.get('is_binary', False):
            # Convert to relative path if needed
            if Path(rel_path).is_absolute():
                try:
                    rel_path = str(Path(rel_path).relative_to(base_path))
                except ValueError:
                    continue
            files_to_analyze.append(rel_path)
    
    if not files_to_analyze:
        return {
            'overall': {
                'health_score': 0,
                'technical_debt': 0,
                'maintainability': 0,
                'total_files': 0
            },
            'languages': {},
            'best_files': [],
            'worst_files': []
        }
    
    # Analyze files in parallel
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing code health...", total=len(files_to_analyze))
        
        async def analyze_files():
            results = await analyzer.analyze_files(base_path, files_to_analyze, cache)
            progress.update(task, completed=len(files_to_analyze))
            return results
        
        results = asyncio.run(analyze_files())
    
    # Calculate overall metrics
    total_files = len(results)
    if total_files == 0:
        return {
            'overall': {
                'health_score': 0,
                'technical_debt': 0,
                'maintainability': 0,
                'total_files': 0
            },
            'languages': {},
            'best_files': [],
            'worst_files': []
        }
    
    # Calculate averages
    avg_health = sum(r['overall_health'] for r in results.values()) / total_files
    avg_debt = sum(r['technical_debt']['total_debt'] for r in results.values()) / total_files
    avg_maintainability = sum(r['technical_debt']['maintainability_index'] for r in results.values()) / total_files
    
    # Sort files by health score
    sorted_files = sorted(
        results.items(),
        key=lambda x: x[1]['overall_health'],
        reverse=True
    )
    
    return {
        'overall': {
            'health_score': avg_health,
            'technical_debt': avg_debt,
            'maintainability': avg_maintainability,
            'total_files': total_files
        },
        'languages': {
            'Python': {
                'files': total_files,
                'avg_health': avg_health,
                'avg_debt': avg_debt
            }
        },
        'best_files': sorted_files[:5],
        'worst_files': sorted_files[-5:]
    }

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
    
    table.add_row("Files Analyzed", str(results['overall']['total_files']))
    table.add_row("Average Health", f"{results['overall']['health_score']:.1f}%")
    table.add_row("Total Technical Debt", f"{results['overall']['technical_debt']:.1f}")
    table.add_row("Average Maintainability", f"{results['overall']['maintainability']:.1f}")
    
    console.print(table)
    
    # Language breakdown
    if results['languages']:
        table = Table(title="Language Statistics", box=SIMPLE)
        table.add_column("Language", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Avg Health", justify="right")
        table.add_column("Avg Debt", justify="right")
        
        for lang, stats in sorted(results['languages'].items()):
            table.add_row(
                lang,
                str(stats['files']),
                f"{stats['avg_health']:.1f}%",
                f"{stats['avg_debt']:.1f}"
            )
        
        console.print(table)
    
    # Best and worst files
    if results['best_files']:
        table = Table(title="Best Performing Files", box=SIMPLE)
        table.add_column("File", style="cyan")
        table.add_column("Health Score", justify="right")
        
        for file, metrics in results['best_files']:
            table.add_row(file, f"{metrics['overall_health']:.1f}%")
        
        console.print(table)
    
    if results['worst_files']:
        table = Table(title="Files Needing Attention", box=SIMPLE)
        table.add_column("File", style="cyan")
        table.add_column("Health Score", justify="right")
        
        for file, metrics in results['worst_files']:
            table.add_row(file, f"{metrics['overall_health']:.1f}%")
        
        console.print(table) 