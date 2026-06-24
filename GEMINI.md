<!-- SPECKIT START -->
Read active implementation plan: specs/001-export-gdrive-markdown/plan.md
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
