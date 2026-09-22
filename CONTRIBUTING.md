# Contributing to OTUI Editor

Thanks for taking the time to improve OTUI Editor. Contributions are most useful when they solve a reproducible problem, keep the editing workflow understandable, and remain compatible with real OTClient modules.

## Before starting

- Search existing issues and pull requests before opening a duplicate.
- For a larger behavior change, open a feature request before investing in the implementation.
- Never include private server assets, credentials, access tokens, or proprietary client files in a report or commit.
- Reduce format-specific bugs to the smallest OTUI/OTMD sample that still reproduces the problem.

## Local setup

```bash
git clone https://github.com/lehnox/Otui-Editor---Tibia.git
cd Otui-Editor---Tibia

python -m venv .venv
```

Activate the environment and install the development dependencies:

```bash
# Windows
.venv\Scripts\activate

# Linux or macOS
source .venv/bin/activate

python -m pip install -r requirements-dev.txt
```

## Validate a change

Run the same checks used by continuous integration:

```bash
python -m py_compile Otui.py
python -m pytest -q
```

For visual or serialization changes, also verify the behavior manually:

1. Open a small test module.
2. Load the affected OTUI/OTMD file.
3. Exercise the changed behavior in the canvas and property editor.
4. Save the file.
5. Review the generated diff and load it in the target OTClient distribution.

## Pull requests

- Keep each pull request focused on one problem.
- Explain the user-facing reason for the change, not only the implementation.
- Include reproduction steps for fixes and screenshots for visible UI changes.
- Add or update tests when changing parsing, path handling, serialization, or other testable logic.
- Preserve existing files and behavior outside the intended scope.
- Use accurate co-author attribution when a commit was genuinely produced by more than one person.

Maintainers may ask for a smaller reproduction, additional compatibility information, or a narrower change before merging.
