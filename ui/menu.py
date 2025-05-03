#!/usr/bin/env python3
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.box import SIMPLE

console = Console()

def show_dynamic_summary(elapsed, files_count, stats):
    """Show a dynamic summary of the scan results."""
    total_loc = sum(v["code"] for v in stats.values())
    badges = [
        f"✅ Scanned {files_count} files",
        f"⏱️ {elapsed:.2f}s",
        f"🐍 Python: {stats.get('Python',{}).get('code',0)} LOC",
        f"🚀 Total LOC: {total_loc}"
    ]
    console.print("   ".join(f"[bold cyan]{b}[/]" for b in badges))

def interactive_menu():
    """Display the main interactive menu."""
    console.clear()
    console.rule("[bold magenta]🚀 Project Status CLI 🚀[/bold magenta]")
    menu = Table(box=SIMPLE)
    menu.add_column("Key", style="cyan bold", width=3)
    menu.add_column("Action")
    menu.add_row("1", "📊 Summary table")
    menu.add_row("2", "📄 Per‑file stats")
    menu.add_row("3", "🌳 Tree view")
    menu.add_row("4", "🔍 Fuzzy search file")
    menu.add_row("5", "📊 Test coverage")
    menu.add_row("6", "📆 Snapshot timeline")
    menu.add_row("7", "🔄 Compare snapshots")
    menu.add_row("8", "💾 Export options")
    menu.add_row("9", "🔒 Security scan")
    menu.add_row("A", "🔎 Advanced search")
    menu.add_row("Q", "⚙️ Code quality metrics")
    menu.add_row("G", "🗂️ Git integration")
    menu.add_row("D", "🔗 Dependency analysis")
    menu.add_row("H", "🏥 Code health analysis")
    menu.add_row("T", "🎨 Change theme")
    menu.add_row("R", "🔄 Rescan")
    menu.add_row("I", "ℹ️ Info")
    menu.add_row("0", "❌ Exit")
    console.print(menu)
    return Prompt.ask(
        "➡️ Choice",
        choices=["0","1","2","3","4","5","6","7","8","9","A","Q","G","D","H","T","R","I"],
        default="1"
    ).upper()

def export_menu():
    """Display the export options menu."""
    console.clear()
    console.rule("[bold blue]💾 Export Options[/bold blue]")
    menu = Table(box=SIMPLE)
    menu.add_column("Key", style="cyan bold", width=3)
    menu.add_column("Action")
    menu.add_row("1", "📄 Export to JSON")
    menu.add_row("2", "📝 Export to CSV")
    menu.add_row("3", "📊 Export to Excel")
    menu.add_row("0", "↩️ Back to main menu")
    console.print(menu)
    return Prompt.ask("➡️ Choose export format", choices=["0","1","2","3"], default="1")

# Define available themes
THEMES = {
    "default": "Default theme",
    "dark": "Dark theme",
    "light": "Light theme"
}

def show_info(path, file_stats, stats, command_registry):
    """Display information about the current scan."""
    console.print(
        Panel(
            f"[bold]Project Status CLI Info[/bold]\n\n"
            f"• Path scanned: [cyan]{path}[/cyan]\n"
            f"• Files scanned: [cyan]{len(file_stats)}[/cyan]\n"
            f"• Languages detected: [cyan]{', '.join(sorted(stats.keys()))}[/cyan]\n"
            f"• Available themes: [cyan]{', '.join(THEMES.keys())}[/cyan]\n"
            f"• Plugins loaded: [cyan]{', '.join(command_registry.keys()) or 'none'}[/cyan]",
            title="ℹ️  Info", box=SIMPLE
        )
    ) 