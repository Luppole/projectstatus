#!/usr/bin/env python3
import os
import re
import ast
import networkx as nx
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.box import SIMPLE
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from config import TEST_PATTERNS, EXT_LANG_MAP
try:
    from radon.complexity import cc_visit
except ImportError:
    cc_visit = None

console = Console()

def estimate_test_coverage(file_stats):
    """Heuristic estimation of test coverage based on file paths."""
    test_files = {}
    code_files = {}
    
    for file_path, stats in file_stats.items():
        is_test = any(re.search(pattern, file_path, re.IGNORECASE) for pattern in TEST_PATTERNS)
        
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

def code_quality_metrics(path):
    """Compute cyclomatic complexity via radon, color‑coded."""
    if not cc_visit:
        console.print("[red]Install radon: pip install radon[/red]")
        return
    report = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            if fn.endswith('.py'):
                fp = os.path.join(root, fn)
                try:
                    src = open(fp, 'r', errors='ignore').read()
                    for b in cc_visit(src):
                        report.append((fn, b.name.split('.')[-1], b.complexity, b.lineno))
                except:
                    continue
    if not report:
        console.print("[yellow]No Python files found for complexity analysis.[/yellow]")
        return
    table = Table(title="Cyclomatic Complexity (top 20)", box=SIMPLE)
    table.add_column("File", no_wrap=True)
    table.add_column("Block", no_wrap=True)
    table.add_column("CC", justify="right")
    table.add_column("Line", justify="right")
    for fn, name, cc, ln in sorted(report, key=lambda x: -x[2])[:20]:
        color = "green" if cc < 5 else "yellow" if cc < 10 else "red"
        table.add_row(fn, name, f"[{color}]{cc}[/{color}]", str(ln))
    console.print(table)

_js_import_re = re.compile(r"""import\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]""")
_js_require_re = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")

def dependency_analysis(path):
    """Build import/require dependency graph for Python and JS/TS."""
    G = nx.DiGraph()
    for root, dirs, files in os.walk(path):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in EXT_LANG_MAP:
                continue
            fp = os.path.join(root, fn)
            G.add_node(fn)
            if ext == '.py':
                try:
                    tree = ast.parse(open(fp, 'r', errors='ignore').read())
                except:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod = alias.name.split('.')[0] + ('.py')
                            G.add_edge(fn, mod)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        mod = module.split('.')[0] + ('.py')
                        G.add_edge(fn, mod)
            else:  # JS/TS support
                try:
                    content = open(fp, 'r', errors='ignore').read()
                except:
                    continue
                for m in _js_import_re.findall(content) + _js_require_re.findall(content):
                    name = os.path.basename(m)
                    if not name.endswith(tuple(EXT_LANG_MAP.keys())):
                        # assume .js if no extension
                        name = name + ext
                    G.add_edge(fn, name)
    console.print("[bold]🔗 Dependency Graph (adjacency)[/bold]")
    if not G.nodes:
        console.print("[yellow]No supported files detected.[/yellow]")
        return
    for src in sorted(G.nodes):
        nbrs = sorted(n for n in G.adj[src] if n in G.nodes)
        if nbrs:
            console.print(f"{src} → {', '.join(nbrs)}")
        else:
            console.print(f"{src} → (no deps)")

def generate_tree_view(file_stats, path):
    """Generate a tree view of the project with LOC information."""
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

def fuzzy_search_file(file_stats):
    """Search for files using fuzzy matching."""
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