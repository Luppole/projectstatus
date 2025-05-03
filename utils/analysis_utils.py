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
    """Compute cyclomatic complexity, detect code smells, and find duplicate code."""
    if not cc_visit:
        console.print("[red]Install radon: pip install radon[/red]")
        return
        
    # Original cyclomatic complexity analysis
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
    
    # Code smell detection
    detect_code_smells(path)
    
    # Duplicate code detection  
    detect_duplicate_code(path)
    
    # Get the current directory to extract file statistics
    current_path = os.getcwd()
    file_stats = {}
    
    # Build a minimal file_stats dict for the new features
    for root, dirs, files in os.walk(path):
        for fn in files:
            if fn.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, fn), current_path)
                file_stats[rel_path] = {'language': 'Python'}
    
    # Run new features
    suggest_refactoring(file_stats, path)
    analyze_documentation_coverage(file_stats, path)

def detect_code_smells(path):
    """Detect various code smells beyond cyclomatic complexity."""
    console.print("\n[bold cyan]🔍 Code Smell Detection[/bold cyan]")
    
    # Define thresholds for code smells
    LONG_METHOD_THRESHOLD = 50  # lines
    LARGE_CLASS_THRESHOLD = 10  # methods
    MANY_PARAMS_THRESHOLD = 5   # parameters
    DEEP_NESTING_THRESHOLD = 4  # levels
    
    smells = []
    
    for root, dirs, files in os.walk(path):
        for fn in files:
            if not fn.endswith('.py'):
                continue
                
            fp = os.path.join(root, fn)
            try:
                # Parse the file
                with open(fp, 'r', errors='ignore') as f:
                    src = f.read()
                tree = ast.parse(src)
                lines = src.splitlines()
                
                # Check for various code smells
                for node in ast.walk(tree):
                    # Long methods/functions
                    if isinstance(node, ast.FunctionDef):
                        end_line = getattr(node, 'end_lineno', 0) or 0
                        if end_line - node.lineno > LONG_METHOD_THRESHOLD:
                            smells.append({
                                'file': fn,
                                'line': node.lineno,
                                'smell': f"Long method '{node.name}' ({end_line - node.lineno} lines)",
                                'severity': 'medium'
                            })
                        
                        # Too many parameters
                        param_count = len(node.args.args)
                        if param_count > MANY_PARAMS_THRESHOLD:
                            smells.append({
                                'file': fn,
                                'line': node.lineno,
                                'smell': f"Too many parameters in '{node.name}' ({param_count} params)",
                                'severity': 'medium'
                            })
                    
                    # Large classes (many methods)
                    if isinstance(node, ast.ClassDef):
                        method_count = sum(1 for n in ast.walk(node) 
                                          if isinstance(n, ast.FunctionDef))
                        if method_count > LARGE_CLASS_THRESHOLD:
                            smells.append({
                                'file': fn,
                                'line': node.lineno,
                                'smell': f"Large class '{node.name}' ({method_count} methods)",
                                'severity': 'high' 
                            })
                    
                    # Deeply nested code
                    if isinstance(node, (ast.For, ast.While, ast.If)):
                        depth = 0
                        current = node
                        while hasattr(current, 'parent'):
                            if isinstance(current.parent, (ast.For, ast.While, ast.If)):
                                depth += 1
                            current = current.parent
                        if depth > DEEP_NESTING_THRESHOLD:
                            smells.append({
                                'file': fn,
                                'line': node.lineno,
                                'smell': f"Deeply nested code (depth {depth})",
                                'severity': 'medium'
                            })
            except Exception as e:
                if os.environ.get('DEBUG'):
                    console.print(f"[dim]Error analyzing {fn}: {str(e)}[/dim]")
                continue
    
    # Display results
    if smells:
        table = Table(title="Code Smells Detected")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Issue")
        table.add_column("Severity")
        
        for smell in sorted(smells, key=lambda x: (x['file'], x['line'])):
            severity = smell['severity']
            severity_color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(severity, 'white')
            
            table.add_row(
                smell['file'],
                str(smell['line']),
                smell['smell'],
                f"[{severity_color}]{severity.upper()}[/{severity_color}]"
            )
        
        console.print(table)
        console.print(f"[yellow]Found {len(smells)} code smells.[/yellow]")
    else:
        console.print("[green]No significant code smells detected.[/green]")

def detect_duplicate_code(path, min_lines=5):
    """Detect duplicate code blocks across files."""
    console.print("\n[bold cyan]🔄 Duplicate Code Detection[/bold cyan]")
    
    # Store code blocks by their hash
    code_blocks = {}
    duplicates = []
    
    for root, dirs, files in os.walk(path):
        for fn in files:
            if not fn.endswith(('.py', '.js', '.java', '.cpp', '.c', '.h')):
                continue
                
            fp = os.path.join(root, fn)
            try:
                with open(fp, 'r', errors='ignore') as f:
                    lines = f.readlines()
                
                # Process blocks of code
                for i in range(len(lines) - min_lines + 1):
                    # Get a block of min_lines lines
                    block = ''.join(lines[i:i+min_lines])
                    # Skip if block is too short after stripping whitespace
                    if len(block.strip()) < 50:
                        continue
                        
                    # Normalize whitespace to find similar blocks
                    normalized = re.sub(r'\s+', ' ', block.strip())
                    block_hash = hash(normalized)
                    
                    if block_hash in code_blocks:
                        # Found a duplicate!
                        source = code_blocks[block_hash]
                        duplicates.append({
                            'source_file': source['file'],
                            'source_line': source['line'],
                            'duplicate_file': fn,
                            'duplicate_line': i + 1,
                            'size': min_lines,
                            'code': block[:50] + '...' if len(block) > 50 else block
                        })
                    else:
                        code_blocks[block_hash] = {
                            'file': fn,
                            'line': i + 1,
                            'code': block
                        }
                        
            except Exception as e:
                if os.environ.get('DEBUG'):
                    console.print(f"[dim]Error analyzing {fn}: {str(e)}[/dim]")
                continue
    
    # Display results
    if duplicates:
        table = Table(title=f"Duplicate Code Blocks (min {min_lines} lines)")
        table.add_column("Original")
        table.add_column("Line", justify="right")
        table.add_column("Duplicate In")
        table.add_column("Line", justify="right")
        table.add_column("Size", justify="right")
        
        # Group duplicates by source to avoid repetition
        grouped_dupes = {}
        for dupe in duplicates:
            key = (dupe['source_file'], dupe['source_line'])
            if key not in grouped_dupes:
                grouped_dupes[key] = []
            grouped_dupes[key].append(dupe)
        
        # Display top 20 duplicate groups
        for (src_file, src_line), dupes in list(grouped_dupes.items())[:20]:
            first_dupe = dupes[0]
            table.add_row(
                src_file, 
                str(src_line),
                first_dupe['duplicate_file'],
                str(first_dupe['duplicate_line']),
                str(first_dupe['size'])
            )
            
            # Add additional dupes as sub-rows
            for dupe in dupes[1:]:
                table.add_row(
                    "", "", 
                    dupe['duplicate_file'],
                    str(dupe['duplicate_line']),
                    str(dupe['size'])
                )
        
        console.print(table)
        console.print(f"[yellow]Found {len(duplicates)} duplicate code blocks across {len(grouped_dupes)} sources.[/yellow]")
        
        # Show a snippet example of the first duplicate
        if duplicates:
            console.print("\n[bold]Example duplicate code:[/bold]")
            code_snippet = duplicates[0]['code'].strip()
            if len(code_snippet) > 300:
                code_snippet = code_snippet[:300] + "..."
            console.print(f"```\n{code_snippet}\n```")
    else:
        console.print("[green]No significant duplicate code detected.[/green]")

def suggest_refactoring(file_stats, path):
    """Provide automated refactoring suggestions based on detected code issues.
    
    Args:
        file_stats: Dictionary with file statistics information
        path: Path to the project directory
        
    Returns:
        Dictionary with refactoring suggestions by file
    """
    console.print("\n[bold cyan]🔄 Automated Refactoring Suggestions[/bold cyan]")
    
    # Dict to store refactoring suggestions
    suggestions = {}
    
    # Get code smells first
    smells = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            if not fn.endswith('.py'):
                continue
                
            fp = os.path.join(root, fn)
            try:
                # Parse the file
                with open(fp, 'r', errors='ignore') as f:
                    src = f.read()
                tree = ast.parse(src)
                
                # Define thresholds (same as in detect_code_smells)
                LONG_METHOD_THRESHOLD = 50
                LARGE_CLASS_THRESHOLD = 10
                MANY_PARAMS_THRESHOLD = 5
                DEEP_NESTING_THRESHOLD = 4
                
                file_suggestions = []
                
                # Check for various code smells and provide refactoring suggestions
                for node in ast.walk(tree):
                    # Long methods/functions
                    if isinstance(node, ast.FunctionDef):
                        end_line = getattr(node, 'end_lineno', 0) or 0
                        lines_count = end_line - node.lineno
                        
                        if lines_count > LONG_METHOD_THRESHOLD:
                            suggestion = {
                                'issue': f"Long method '{node.name}' ({lines_count} lines)",
                                'line': node.lineno,
                                'recommendation': "Extract smaller, focused methods from this long function.",
                                'refactoring_type': 'extract_method',
                                'example': f"# Instead of one long method\ndef {node.name}(...):\n    # 50+ lines of code\n\n# Split into smaller methods\ndef {node.name}(...):\n    result1 = do_first_thing(...)\n    result2 = do_second_thing(...)\n    return combine_results(result1, result2)\n\ndef do_first_thing(...):\n    # ~15-20 lines\n\ndef do_second_thing(...):\n    # ~15-20 lines"
                            }
                            file_suggestions.append(suggestion)
                        
                        # Too many parameters
                        param_count = len(node.args.args)
                        if param_count > MANY_PARAMS_THRESHOLD:
                            param_names = [a.arg for a in node.args.args if a.arg != 'self']
                            suggestion = {
                                'issue': f"Too many parameters in '{node.name}' ({param_count} params)",
                                'line': node.lineno,
                                'recommendation': "Use a configuration object or data class to group related parameters.",
                                'refactoring_type': 'introduce_parameter_object',
                                'example': f"# Instead of many parameters\ndef {node.name}({', '.join(param_names[:3])}, ...):\n    # method body\n\n# Use a configuration object\nfrom dataclasses import dataclass\n\n@dataclass\nclass {node.name.capitalize()}Config:\n    {param_names[0]}: type\n    {param_names[1]}: type\n    # ...\n\ndef {node.name}(config: {node.name.capitalize()}Config):\n    # Use config.{param_name}"
                            }
                            file_suggestions.append(suggestion)
                    
                    # Large classes
                    elif isinstance(node, ast.ClassDef):
                        method_count = sum(1 for n in ast.walk(node) 
                                          if isinstance(n, ast.FunctionDef))
                        if method_count > LARGE_CLASS_THRESHOLD:
                            suggestion = {
                                'issue': f"Large class '{node.name}' ({method_count} methods)",
                                'line': node.lineno,
                                'recommendation': "Split into smaller, more focused classes following the Single Responsibility Principle.",
                                'refactoring_type': 'extract_class',
                                'example': f"# Instead of one large class\nclass {node.name}:\n    # Many methods handling different responsibilities\n\n# Split into multiple focused classes\nclass {node.name}Core:\n    # Core functionality\n\nclass {node.name}Helper:\n    # Helper functions\n\nclass {node.name}IO:\n    # I/O operations"
                            }
                            file_suggestions.append(suggestion)
                    
                    # Deeply nested code
                    elif isinstance(node, (ast.For, ast.While, ast.If)) and hasattr(node, 'parent'):
                        depth = 0
                        current = node
                        while hasattr(current, 'parent'):
                            if isinstance(current.parent, (ast.For, ast.While, ast.If)):
                                depth += 1
                            current = current.parent
                        
                        if depth > DEEP_NESTING_THRESHOLD:
                            suggestion = {
                                'issue': f"Deeply nested code (depth {depth})",
                                'line': node.lineno,
                                'recommendation': "Extract nested blocks into separate methods or use early returns to reduce nesting.",
                                'refactoring_type': 'extract_method',
                                'example': f"# Instead of deep nesting\nif condition1:\n    # code\n    if condition2:\n        # more code\n        if condition3:\n            # even more code\n\n# Use early returns or guard clauses\nif not condition1:\n    return\n# code\nif not condition2:\n    return\n# more code\nif not condition3:\n    return\n# even more code"
                            }
                            file_suggestions.append(suggestion)
                
                if file_suggestions:
                    suggestions[fn] = file_suggestions
                    
            except Exception as e:
                if os.environ.get('DEBUG'):
                    console.print(f"[dim]Error analyzing {fn}: {str(e)}[/dim]")
                continue
    
    # Display refactoring suggestions
    if suggestions:
        table = Table(title="Refactoring Suggestions")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Issue")
        table.add_column("Recommendation")
        
        suggestion_count = 0
        for file, file_suggestions in sorted(suggestions.items()):
            for i, suggestion in enumerate(file_suggestions):
                table.add_row(
                    file if i == 0 else "",
                    str(suggestion['line']),
                    suggestion['issue'],
                    suggestion['recommendation']
                )
                suggestion_count += 1
                
                # Show examples for the first occurrence of each refactoring type
                if i == 0:
                    table.add_row(
                        "", "", "",
                        f"[dim cyan]Example:[/dim cyan]\n[dim]{suggestion['example']}[/dim]"
                    )
        
        console.print(table)
        console.print(f"[yellow]Found {suggestion_count} refactoring opportunities across {len(suggestions)} files.[/yellow]")
    else:
        console.print("[green]No significant refactoring opportunities detected.[/green]")
    
    return suggestions

def analyze_documentation_coverage(file_stats, path):
    """Analyze documentation coverage across the codebase.
    
    Args:
        file_stats: Dictionary with file statistics information
        path: Path to the project directory
        
    Returns:
        Dictionary with documentation coverage metrics
    """
    console.print("\n[bold cyan]📚 Documentation Coverage Analysis[/bold cyan]")
    
    # Store documentation metrics
    doc_metrics = {
        'total_functions': 0,
        'documented_functions': 0,
        'total_classes': 0,
        'documented_classes': 0,
        'total_modules': 0,
        'documented_modules': 0,
        'files': {}
    }
    
    # Process each Python file
    for root, dirs, files in os.walk(path):
        for fn in files:
            if not fn.endswith('.py'):
                continue
            
            fp = os.path.join(root, fn)
            file_metrics = {
                'functions': {'total': 0, 'documented': 0},
                'classes': {'total': 0, 'documented': 0},
                'module_docstring': False,
                'doc_coverage': 0.0,
                'quality_score': 0.0,
                'missing_docs': []
            }
            
            try:
                # Parse the file
                with open(fp, 'r', errors='ignore') as f:
                    source = f.read()
                tree = ast.parse(source)
                
                # Check for module docstring
                module_docstring = ast.get_docstring(tree)
                file_metrics['module_docstring'] = bool(module_docstring)
                if module_docstring:
                    doc_metrics['documented_modules'] += 1
                else:
                    file_metrics['missing_docs'].append(('module', 'Module', 1))
                
                doc_metrics['total_modules'] += 1
                
                # Process classes and functions
                for node in ast.walk(tree):
                    # Check classes
                    if isinstance(node, ast.ClassDef):
                        file_metrics['classes']['total'] += 1
                        doc_metrics['total_classes'] += 1
                        
                        class_docstring = ast.get_docstring(node)
                        if class_docstring:
                            file_metrics['classes']['documented'] += 1
                            doc_metrics['documented_classes'] += 1
                            
                            # Basic quality check
                            quality = evaluate_docstring_quality(class_docstring)
                            file_metrics['quality_score'] += quality
                        else:
                            file_metrics['missing_docs'].append(('class', node.name, node.lineno))
                    
                    # Check functions/methods        
                    elif isinstance(node, ast.FunctionDef):
                        # Skip special methods like __init__
                        if not node.name.startswith('__') or node.name.endswith('__'):
                            file_metrics['functions']['total'] += 1
                            doc_metrics['total_functions'] += 1
                            
                            func_docstring = ast.get_docstring(node)
                            if func_docstring:
                                file_metrics['functions']['documented'] += 1
                                doc_metrics['documented_functions'] += 1
                                
                                # Basic quality check
                                quality = evaluate_docstring_quality(func_docstring)
                                file_metrics['quality_score'] += quality
                            else:
                                file_metrics['missing_docs'].append(('function', node.name, node.lineno))
                
                # Calculate file coverage percentage
                total_items = file_metrics['classes']['total'] + file_metrics['functions']['total'] + 1  # +1 for module
                documented_items = file_metrics['classes']['documented'] + file_metrics['functions']['documented']
                documented_items += 1 if file_metrics['module_docstring'] else 0
                
                if total_items > 0:
                    file_metrics['doc_coverage'] = (documented_items / total_items) * 100
                    
                    # Normalize quality score
                    if documented_items > 0:
                        file_metrics['quality_score'] = file_metrics['quality_score'] / documented_items
                    else:
                        file_metrics['quality_score'] = 0
                
                doc_metrics['files'][fn] = file_metrics
                
            except Exception as e:
                if os.environ.get('DEBUG'):
                    console.print(f"[dim]Error analyzing documentation in {fn}: {str(e)}[/dim]")
                continue
    
    # Calculate overall metrics
    total_items = doc_metrics['total_classes'] + doc_metrics['total_functions'] + doc_metrics['total_modules']
    documented_items = doc_metrics['documented_classes'] + doc_metrics['documented_functions'] + doc_metrics['documented_modules']
    
    overall_coverage = 0
    if total_items > 0:
        overall_coverage = (documented_items / total_items) * 100
    
    doc_metrics['overall_coverage'] = overall_coverage
    
    # Display documentation coverage
    table = Table(title="Documentation Coverage Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Documented", justify="right")
    table.add_column("Coverage", justify="right")
    
    # Add rows for modules, classes, and functions
    table.add_row(
        "Modules",
        str(doc_metrics['total_modules']),
        str(doc_metrics['documented_modules']),
        format_percentage(doc_metrics['total_modules'], doc_metrics['documented_modules'])
    )
    
    table.add_row(
        "Classes",
        str(doc_metrics['total_classes']),
        str(doc_metrics['documented_classes']),
        format_percentage(doc_metrics['total_classes'], doc_metrics['documented_classes'])
    )
    
    table.add_row(
        "Functions",
        str(doc_metrics['total_functions']),
        str(doc_metrics['documented_functions']),
        format_percentage(doc_metrics['total_functions'], doc_metrics['documented_functions'])
    )
    
    # Add overall coverage row
    table.add_row(
        "Overall",
        str(total_items),
        str(documented_items),
        format_coverage_percentage(overall_coverage)
    )
    
    console.print(table)
    
    # Display files with poor documentation
    if doc_metrics['files']:
        # Sort files by documentation coverage
        sorted_files = sorted(
            doc_metrics['files'].items(),
            key=lambda x: x[1]['doc_coverage']
        )
        
        # Show the worst 10 files
        if len(sorted_files) > 0:
            console.print("\n[bold]Top 10 Files Needing Documentation:[/bold]")
            
            files_table = Table(box=SIMPLE)
            files_table.add_column("File")
            files_table.add_column("Coverage", justify="right")
            files_table.add_column("Missing Docs")
            
            for fn, metrics in sorted_files[:10]:
                missing = ", ".join([f"{type_} '{name}'" for type_, name, _ in metrics['missing_docs'][:5]])
                if len(metrics['missing_docs']) > 5:
                    missing += f" and {len(metrics['missing_docs']) - 5} more..."
                    
                files_table.add_row(
                    fn,
                    format_coverage_percentage(metrics['doc_coverage']),
                    missing or "N/A"
                )
                
            console.print(files_table)
    
    return doc_metrics

def evaluate_docstring_quality(docstring):
    """Evaluate the quality of a docstring.
    
    Args:
        docstring: The docstring to evaluate
        
    Returns:
        float: Quality score between 0.0 and 1.0
    """
    if not docstring:
        return 0.0
    
    score = 0.0
    max_score = 4.0  # Maximum possible score
    
    # Check length (min 10 characters)
    if len(docstring) >= 10:
        score += 1.0
    
    # Check if it contains parameter descriptions (Args, Parameters, etc.)
    if any(marker in docstring for marker in ['Args:', 'Parameters:', 'param ']):
        score += 1.0
    
    # Check if it contains return value description
    if any(marker in docstring for marker in ['Returns:', 'Return:', 'rtype:', 'return:']):
        score += 1.0
    
    # Check if there's a description beyond one line
    if docstring.count('\n') >= 1:
        score += 1.0
    
    return score / max_score

def format_percentage(total, documented):
    """Format a coverage percentage with color coding.
    
    Args:
        total: Total number of items
        documented: Number of documented items
        
    Returns:
        str: Formatted percentage string with color
    """
    if total == 0:
        return "N/A"
    
    percentage = (documented / total) * 100
    return format_coverage_percentage(percentage)

def format_coverage_percentage(percentage):
    """Format a coverage percentage with color coding.
    
    Args:
        percentage: The percentage to format
        
    Returns:
        str: Formatted percentage string with color
    """
    if percentage >= 80:
        return f"[green]{percentage:.1f}%[/green]"
    elif percentage >= 50:
        return f"[yellow]{percentage:.1f}%[/yellow]"
    else:
        return f"[red]{percentage:.1f}%[/red]"

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
    
    console.print("[bold]🔗 Dependency Graph[/bold]")
    if not G.nodes:
        console.print("[yellow]No supported files detected.[/yellow]")
        return
    
    # Create a table for dependencies
    table = Table(title="File Dependencies", box=SIMPLE)
    table.add_column("Source File", style="cyan")
    table.add_column("Dependencies")
    
    for src in sorted(G.nodes):
        nbrs = sorted(n for n in G.adj[src] if n in G.nodes)
        deps = ", ".join(nbrs) if nbrs else "(no deps)"
        table.add_row(src, deps)
            
    console.print(table)

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

def advanced_search(file_stats, current_path):
    """Search code by regex across files."""
    pattern = prompt("🔎 Enter regex to search: ")
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

def display_language_stats(file_stats):
    """Display language statistics with a pie chart."""
    # Import plotext as plt, or disable if missing
    try:
        import plotext as plt
        console.print("[green]✓ Plotext library loaded successfully[/green]")
    except ImportError:
        console.print("[yellow]⚠ Install plotext for pie charts: pip install plotext[/yellow]")
        plt = None

    from rich.panel import Panel
    
    # Calculate lines of code per language
    lang_stats = {}
    for file_path, stats in file_stats.items():
        lang = stats.get('language', 'Unknown')
        if lang not in lang_stats:
            lang_stats[lang] = {'files': 0, 'code': 0, 'blank': 0, 'comments': 0}
        lang_stats[lang]['files'] += 1
        lang_stats[lang]['code'] += stats.get('code', 0)
        lang_stats[lang]['blank'] += stats.get('blank', 0)
        lang_stats[lang]['comments'] += stats.get('comments', 0)
    
    # Create a table for language stats
    table = Table(title="Language Statistics", box=SIMPLE)
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Code Lines", justify="right")
    table.add_column("Blank Lines", justify="right")
    table.add_column("Comments", justify="right")
    table.add_column("Total Lines", justify="right")
    
    languages = []
    code_counts = []
    
    for lang, stats in sorted(lang_stats.items(), key=lambda x: x[1]['code'], reverse=True):
        total = stats['code'] + stats['blank'] + stats['comments']
        table.add_row(
            lang,
            str(stats['files']),
            str(stats['code']),
            str(stats['blank']),
            str(stats['comments']),
            str(total)
        )
        # Only include non-zero values in the pie chart
        if stats['code'] > 0:
            languages.append(lang)
            code_counts.append(stats['code'])
    
    # Display language statistics table
    console.print(table)
    
    # Create a pie chart using plotext if available
    if plt:
        try:
            plt.clf()
            plt.theme("dracula")
            console.print("[green]✓ Creating pie chart...[/green]")
            plt.pie(code_counts, labels=languages, title="Code Distribution by Language")
            chart = plt.build()
            console.print(Panel(chart, title="[bold]LOC by Language[/bold]"))
        except Exception as e:
            console.print(f"[red]❌ Error generating pie chart: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")