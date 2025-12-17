# Contributing to Alert Alchemy 🧪

First off, thank you for considering contributing to Alert Alchemy! It's people like you that make this project a great tool for learning incident response.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Writing Incidents](#writing-incidents)
  - [Submitting Code](#submitting-code)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs 🐛

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (incident ID, commands run, etc.)
- **Describe the behavior you observed and what you expected**
- **Include your Python version and OS**

### Suggesting Features 💡

Feature suggestions are tracked as GitHub issues. When suggesting a feature:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed feature**
- **Explain why this feature would be useful**
- **List any alternatives you've considered**

### Writing Incidents 📝

One of the best ways to contribute is by writing new incident scenarios! See [docs/write-an-incident.md](docs/write-an-incident.md) for the complete guide.

Quick checklist for incident contributions:
- [ ] Realistic scenario based on real-world incidents
- [ ] At least 4 timeline steps
- [ ] Multiple valid resolution paths
- [ ] Clear trade-offs for each action
- [ ] Realistic logs, metrics, and traces
- [ ] Proper YAML schema validation passes

### Submitting Code 💻

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/alert-alchemy.git
cd alert-alchemy

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run the CLI
alert-alchemy --help
```

## Style Guidelines

### Python Code

- Follow PEP 8
- Use type hints for function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

### Incident YAML

- Use realistic, production-like data
- Include varied log formats (JSON, plain text, structured)
- Make metrics change meaningfully between steps
- Provide helpful hints without giving away the answer

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add yourself to CONTRIBUTORS if you'd like
4. The PR will be reviewed by maintainers
5. Once approved, it will be merged

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated (if applicable)
- [ ] Incident YAML validates (if adding incidents)
- [ ] Commit messages are clear

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing!

---

Thank you for contributing! 🎉
