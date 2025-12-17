# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Alert Alchemy, please report it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email us at: **security@alert-alchemy.dev** (or open a [private security advisory](https://github.com/ThanhNguyxn/alert-alchemy/security/advisories/new))
3. Include:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

### What to Expect

| Timeline | Action |
|----------|--------|
| 24-48 hours | Initial acknowledgment of your report |
| 7 days | Assessment and severity classification |
| 30 days | Fix developed and tested (for confirmed issues) |
| 90 days | Public disclosure (coordinated with reporter) |

### Scope

This security policy covers:
- The `alert-alchemy` Python package
- CLI commands and their behavior
- State file handling (`.alert_alchemy_state.json`)

### Out of Scope

- Incident YAML files (user-generated content)
- Third-party dependencies (report to upstream maintainers)

## Security Best Practices

When using Alert Alchemy:
- Only load incident YAML files from trusted sources
- Don't commit `.alert_alchemy_state.json` to version control
- Keep your Python environment updated

---

Thank you for helping keep Alert Alchemy secure! 🔐
