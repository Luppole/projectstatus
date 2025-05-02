# 🚀 Project Status CLI

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![Lines of Code](https://img.shields.io/badge/lines%20of%20code-1.2k-blue)](https://github.com/yourusername/project-status-cli)

A powerful command-line tool for analyzing and visualizing your project's codebase. Get instant insights into your code quality, test coverage, and project structure.

## ✨ Features

### 📊 Code Analysis
- **📈 Language Statistics**: Detailed breakdown of code, blank, and comment lines by language
- **📑 Per-File Analysis**: Granular statistics for each file in your project
- **🌳 Project Tree View**: Visual representation of your project structure with LOC information
- **🔍 Fuzzy File Search**: Quick file search with fuzzy matching
- **🔎 Advanced Search**: Regex-based code search across files

### 🧪 Quality Metrics
- **🧪 Test Coverage Estimation**: Heuristic-based test coverage analysis
- **📊 Code Quality Metrics**: Cyclomatic complexity analysis using radon
- **🔗 Dependency Analysis**: Visualize import dependencies between files
- **🔒 Security Scanning**: Basic security checks for sensitive files and patterns

### 📈 Project Tracking
- **📸 Snapshot System**: Save and compare code statistics over time
- **🔄 Git Integration**: View git contributions and file churn metrics
- **💾 Export Options**: Export statistics to JSON, CSV, or Excel
- **📊 Dynamic Summary**: Real-time project status with key metrics

### 🎨 UI Features
- **🎯 Interactive Menu**: User-friendly CLI interface
- **🎨 Theme Support**: Multiple color themes (dark, light, neon, matrix)
- **🔌 Plugin System**: Extend functionality with custom plugins
- **⏳ Progress Bars**: Visual feedback for long-running operations

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

### Basic Usage
```bash
# Interactive mode
python main.py

# CLI mode with options
python main.py --path . --sort lines --export json
```

### Command Line Options
```bash
Options:
  --path PATH           Path to scan (default: current directory)
  --sort {lines,code,blank,comments}
                       Sort files by metric
  --export {json,csv,excel,html}
                       Export format
  --save-badge PATH    Save LOC badge as SVG
  --report PATH        Generate markdown report
  --web               Launch web dashboard
  --ignore PATH       Path to .projectstatusignore file
  --theme {dark,light,neon,matrix}
                       UI theme
  --no-progress       Disable progress bars
  --version           Show version and exit
  --help              Show this help message
```

### Examples
```bash
# Generate JSON report for current directory
python main.py --export json

# Scan specific path and sort by code lines
python main.py --path src/ --sort code

# Launch web dashboard
python main.py --web

# Generate markdown report
python main.py --report analysis.md
```

## 📁 Project Structure

```
project-status-cli/
├── 📄 main.py              # Main entry point
├── ⚙️ config.py            # Configuration and constants
├── 📦 requirements.txt     # Project dependencies
├── 📚 README.md           # This file
├── 🎨 ui/                 # UI components
│   ├── 📋 menu.py         # Menu and UI functions
│   └── 🎨 theme.py        # Theme management
└── 🛠️ utils/              # Utility functions
    ├── 📊 analysis_utils.py    # Code analysis
    ├── 💾 export_utils.py      # Export functionality
    ├── 📁 file_utils.py        # File operations
    ├── 🔄 git_utils.py         # Git integration
    └── 🔒 security_utils.py    # Security scanning
```

## 🔧 Configuration

Create a `.locconfig` file in your project root to customize behavior:

```ini
[settings]
exclude_dirs = .git,node_modules,venv
include_exts = .py,.js,.ts,.java
output_format = table
```

## 📊 Example Outputs

### 📈 Language Statistics
```
📊 Code Statistics by Language
┌───────────┬────────────┬────────────┬───────────────┬────────────┐
│ Language  │ Code Lines │ Blank Lines│ Comment Lines │ Total Lines│
├───────────┼────────────┼────────────┼───────────────┼────────────┤
│ Python    │ 1,234      │ 123        │ 456           │ 1,813      │
│ JavaScript│ 567        │ 45         │ 89            │ 701        │
└───────────┴────────────┴────────────┴───────────────┴────────────┘
```

### 🌳 Project Tree View
```
📁 project-status-cli
├── 📁 src
│   ├── 📄 main.py (1,234 LOC)
│   └── 📄 utils.py (567 LOC)
└── 📁 tests
    └── 📄 test_main.py (89 LOC)
```

### 📊 Test Coverage
```
🧪 Test Coverage: 85.5%
├── ✅ Test Files: 12
├── 📝 Code Files: 45
├── 📊 Test LOC: 1,234
└── 📝 Code LOC: 5,678
```

### 🔒 Security Scan
```
🔒 Security Scan Results
┌──────────────┬─────────────────────────┬──────────┐
│ File         │ Issue                   │ Severity │
├──────────────┼─────────────────────────┼──────────┤
│ config.py    │ Potential API key       │ 🔴 HIGH  │
│ .env         │ Sensitive file          │ 🟡 MEDIUM│
│ script.sh    │ Large shell script      │ 🟢 LOW   │
└──────────────┴─────────────────────────┴──────────┘
```

### 📈 Code Growth
```
📈 Code Growth (Last 30 Days)
┌───────────┬──────────┬──────────┬──────────┬──────────┐
│ Language  │ Previous │ Current  │ Change   │ % Change │
├───────────┼──────────┼──────────┼──────────┼──────────┤
│ Python    │ 1,000    │ 1,234    │ +234     │ +23.4%   │
│ JavaScript│ 500      │ 567      │ +67      │ +13.4%   │
└───────────┴──────────┴──────────┴──────────┴──────────┘
```

## 🚀 Roadmap

### 🎯 Planned Features
- [ ] 🌐 Web Dashboard
  - [ ] Interactive charts and graphs
  - [ ] Real-time updates
  - [ ] Team collaboration features

- [ ] 🔍 Enhanced Analysis
  - [ ] Smart language detection
  - [ ] Code duplication analysis
  - [ ] Architecture visualization

- [ ] 🛠️ Developer Tools
  - [ ] VS Code extension
  - [ ] CI/CD integration
  - [ ] Custom metric plugins

- [ ] 📊 Advanced Metrics
  - [ ] Code health scoring
  - [ ] Technical debt estimation
  - [ ] Maintainability index

### 🔧 Improvements
- [ ] Performance optimization
  - [ ] Parallel file scanning
  - [ ] Incremental analysis
  - [ ] File caching

- [ ] Better binary file handling
  - [ ] MIME type detection
  - [ ] Extension-based filtering
  - [ ] Custom ignore patterns

- [ ] Enhanced GitHub integration
  - [ ] Contributor statistics
  - [ ] Commit analysis
  - [ ] Bus factor calculation

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting
- [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for interactive CLI
- [Radon](https://github.com/rubik/radon) for code metrics
- [NetworkX](https://github.com/networkx/networkx) for dependency analysis

## 📫 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - email@example.com

Project Link: [https://github.com/yourusername/project-status-cli](https://github.com/yourusername/project-status-cli)
