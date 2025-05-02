# 🤝 Contributing to Project Status CLI

We love your input! We want to make contributing to Project Status CLI as easy and transparent as possible, whether it's:

- 🐛 Reporting a bug
- 💡 Discussing the current state of the code
- 🔧 Submitting a fix
- ✨ Proposing new features
- 📚 Becoming a maintainer

## 🛠️ Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## 🧪 Testing

We use `pytest` for testing. To run the tests:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

## 📝 Code Style

We use `black` for code formatting and `ruff` for linting. To ensure your code follows our style:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Format code
black .

# Run linter
ruff check .
```

### Style Guide

- Use meaningful variable names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where possible
- Follow PEP 8 guidelines

## 📚 Documentation

- Update the README.md with details of changes to the interface
- Add comments to the code where necessary
- Update the docstrings for any new functions
- Add examples for new features

## 🐛 Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/project-status-cli/issues/new).

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10]
 - Python Version: [e.g. 3.9.0]
 - Project Status CLI Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

## 💡 Feature Requests

We love feature requests! Please use the feature request template when opening a new issue.

### Feature Request Template

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 🔄 Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the documentation with any new features
3. The PR will be merged once you have the sign-off of at least one other developer
4. Make sure all tests pass and code is properly formatted

### PR Template

```markdown
## Description
Please include a summary of the change and which issue is fixed.

## Type of change
Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] This change requires a documentation update

## How Has This Been Tested?
Please describe the tests that you ran to verify your changes.

## Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## 📦 Release Process

1. Update version numbers in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. Tag the release with the version number

## 📫 Questions?

Feel free to reach out to us at [email@example.com](mailto:email@example.com) or open an issue for any questions or concerns.

## 🙏 Acknowledgments

Thanks to all the people who have contributed to this project! 