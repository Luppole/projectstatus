# Project Status CLI

A command-line tool for analyzing and monitoring project status, including code metrics, test coverage, security checks, and more.

## Features

- 📊 Code statistics by language
- 📄 Per-file code analysis
- 🌳 Project tree view with LOC information
- 🔍 Fuzzy file search
- 📊 Test coverage estimation
- 📆 Snapshot timeline
- 🔄 Snapshot comparison
- 💾 Export to JSON/CSV/Excel
- 🔒 Security scanning
- 🔎 Advanced code search
- ⚙️ Code quality metrics
- 🗂️ Git integration
- 🔗 Dependency analysis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd projectstatus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the tool:
```bash
python main.py
```

Follow the interactive prompts to:
1. Choose a theme
2. Select a directory to scan
3. Configure exclude directories and file extensions
4. Use the menu to access various features

## Project Structure

```
projectstatus/
├── main.py              # Main entry point
├── config.py            # Configuration and constants
├── requirements.txt     # Project dependencies
├── utils/              # Utility modules
│   ├── file_utils.py   # File operations
│   ├── git_utils.py    # Git integration
│   ├── export_utils.py # Export functionality
│   ├── security_utils.py # Security scanning
│   └── analysis_utils.py # Code analysis
└── ui/                 # UI components
    ├── menu.py         # Menu system
    └── theme.py        # Theme management
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
