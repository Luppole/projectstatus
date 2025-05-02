# 🚀 Project Status CLI

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

A powerful command-line tool for analyzing and visualizing your project's codebase. Get instant insights into your code quality, test coverage, and project structure.

## ✨ Features

### 📊 Code Analysis
- **Language Statistics**: Detailed breakdown of code, blank, and comment lines by language
- **Per-File Analysis**: Granular statistics for each file in your project
- **Project Tree View**: Visual representation of your project structure with LOC information
- **Fuzzy File Search**: Quick file search with fuzzy matching
- **Advanced Search**: Regex-based code search across files

### 🧪 Quality Metrics
- **Test Coverage Estimation**: Heuristic-based test coverage analysis
- **Code Quality Metrics**: Cyclomatic complexity analysis using radon
- **Dependency Analysis**: Visualize import dependencies between files
- **Security Scanning**: Basic security checks for sensitive files and patterns

### 📈 Project Tracking
- **Snapshot System**: Save and compare code statistics over time
- **Git Integration**: View git contributions and file churn metrics
- **Export Options**: Export statistics to JSON, CSV, or Excel
- **Dynamic Summary**: Real-time project status with key metrics

### 🎨 UI Features
- **Interactive Menu**: User-friendly CLI interface
- **Theme Support**: Multiple color themes (dark, light, neon, matrix)
- **Plugin System**: Extend functionality with custom plugins
- **Progress Bars**: Visual feedback for long-running operations

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/project-status-cli.git
cd project-status-cli
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

Run the tool:
```bash
python main.py
```

### Basic Commands
- **1**: View summary table
- **2**: View per-file statistics
- **3**: Show project tree view
- **4**: Fuzzy search files
- **5**: Estimate test coverage
- **6**: View snapshot timeline
- **7**: Compare snapshots
- **8**: Export options
- **9**: Run security scan
- **A**: Advanced search
- **Q**: View code quality metrics
- **G**: Git integration
- **D**: Dependency analysis
- **T**: Change theme
- **R**: Rescan project
- **I**: Show info
- **0**: Exit

## 📁 Project Structure

```
project-status-cli/
├── main.py              # Main entry point
├── config.py            # Configuration and constants
├── requirements.txt     # Project dependencies
├── README.md           # This file
├── ui/                 # UI components
│   ├── menu.py         # Menu and UI functions
│   └── theme.py        # Theme management
└── utils/              # Utility functions
    ├── analysis_utils.py    # Code analysis
    ├── export_utils.py      # Export functionality
    ├── file_utils.py        # File operations
    ├── git_utils.py         # Git integration
    └── security_utils.py    # Security scanning
```

## 🔧 Configuration

Create a `.locconfig` file in your project root to customize behavior:

```ini
[settings]
exclude_dirs = .git,node_modules,venv
include_exts = .py,.js,.ts,.java
output_format = table
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting
- [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for interactive CLI
- [Radon](https://github.com/rubik/radon) for code metrics
- [NetworkX](https://github.com/networkx/networkx) for dependency analysis

## 📊 Example Output

```
📊 Code Statistics by Language
┌──────────┬────────────┬────────────┬───────────────┬────────────┐
│ Language │ Code Lines │ Blank Lines │ Comment Lines │ Total Lines │
├──────────┼────────────┼────────────┼───────────────┼────────────┤
│ Python   │ 1,234      │ 123        │ 456          │ 1,813      │
│ JavaScript│ 567       │ 45         │ 89           │ 701        │
└──────────┴────────────┴────────────┴───────────────┴────────────┘
```

## 🔮 Future Features

- [ ] Web dashboard for visualization
- [ ] CI/CD integration
- [ ] Custom metric plugins
- [ ] Team collaboration features
- [ ] Automated code review suggestions

## 📫 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - email@example.com

Project Link: [https://github.com/yourusername/project-status-cli](https://github.com/yourusername/project-status-cli)
