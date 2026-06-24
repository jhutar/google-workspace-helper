<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/002-support-sheets-slides-export/plan.md
<!-- SPECKIT END -->

## Development Workflows

Before submitting changes, ensure that all linting, formatting, security checks, and test suites pass successfully.

### Quality Checks & Linting

Run all pre-commit quality checks (including ruff, bandit, yamllint):
```bash
make check-all
```

### Running Tests

Run the full pytest suite:
```bash
make test
```
