#!/usr/bin/env python3
from rich.console import Console
from rich.prompt import Prompt
from config import THEMES

console = Console()

def choose_theme():
    """Allow user to choose a theme for the application."""
    choice = Prompt.ask("🎨 Choose theme", choices=list(THEMES.keys()), default="dark")
    console.theme = THEMES[choice]
    return choice 