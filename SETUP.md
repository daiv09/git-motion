# GitHub-to-Video Setup Guide

To run the Manim engine, you will need a few system-level dependencies depending on your operating system.

## 1. System Dependencies (Required for Manim)

### macOS (via Homebrew)
```bash
brew install cairo pango pkg-config ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential python3-dev libcairo2-dev libpango1.0-dev ffmpeg
```

### Windows
You can install dependencies using [Chocolatey](https://chocolatey.org/):
```powershell
choco install ffmpeg
```
Please consult the [Manim Installation Guide](https://docs.manim.community/en/stable/installation.html) for detailed Windows instructions (including LaTeX if you plan to use complex formulas).

## 2. Python Dependencies

Once your system dependencies are installed, you can install the Python packages:
```bash
pip install -r backend/requirements.txt
```

This will install:
- `PyGithub` for fetching repository details
- `manim` for video generation
- `python-dotenv` for API token management
