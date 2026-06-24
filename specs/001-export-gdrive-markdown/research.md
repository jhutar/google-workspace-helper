# Research: Google Drive Markdown Exporter

## 1. CLI Framework & Subcommands
- **Decision**: Python standard library `argparse` with subcommands capability, defining the command structure as `google-workspace-helper export <id>`.
- **Rationale**: Keeps the application lightweight with zero third-party library dependencies (as requested "minimal dependencies"), while allowing easy scaling to future subcommands.
- **Alternatives Considered**: Click, Typer (rejected to avoid external dependencies).

## 2. Google Workspace Integration Interface
- **Decision**: Subprocess execution of the local `gws` CLI tool via `subprocess.run` with proper error capturing and check filters.
- **Rationale**: Thin wrapper around an already authenticated and working command‑line utility (`gws`), avoiding complex OAuth2 flow implementation in this script.
- **Alternatives Considered**: Google APIs Client Library (rejected because it requires OAuth client secrets, token cache management, and heavy dependencies).

## 3. Base64 Image Processing
- **Decision**: Regular expression matching (`re` module) to extract `data:image/<mime>;base64,<data>` inline URIs from exported markdown, binary base64 decoding via `base64` module, and disk write to `/tmp/<doc_id>/`.
- **Rationale**: Highly performant, completely offline processing of exported content without network roundtrips, using standard library modules.
- **Alternatives Considered**: Inline HTML parsing with Beautiful Soup (rejected to preserve zero-dependency standard).

## 4. Development & Code Quality Tools
- **Decision**: pre-commit hooks featuring `ruff`, `ruff-format`, `bandit`, `gitleaks`, `yamllint`, and static analysis tools. `Makefile` for automated bootstrap and quality checks.
- **Rationale**: Matches the user's explicit design parameters, ensures strict adherence to PEP 8 standards, and provides a streamlined developer environment.
- **Alternatives Considered**: Manual script checking (rejected as error-prone).
