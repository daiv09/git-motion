# Git Motion: Project Intelligence

## Overview
Git Motion is a high-fidelity technical video generator that transforms GitHub repository history into cinematic stories using the **Manim** animation engine.

## Tech Stack
- **Frontend**: Next.js 16 (App Router), React 19, TailwindCSS 4, Framer Motion.
- **Data Pipeline**: Python 3.10+, PyGithub, Matplotlib.
- **Animation Engine**: Manim Community (Native animations, No-LaTeX optimized).

## Core Workflows

### 1. Data Fetching
```bash
python3 backend/fetch_repo_data.py <GITHUB_URL> <OUTPUT_DIR>
```
- Fetches metadata (stars, forks, topics, PRs).
- Extracts commit taxonomy (Features, Fixes, etc.).
- Generates `repo_data.json` and a timeline graph.

### 2. Video Rendering
```bash
export REPO_JSON_PATH="path/to/repo_data.json"
python3 -m manim backend/manim_engine.py ProjectBiography -ql --media_dir <DIR>
```
- Orchestrates 13 cinematic scenes.
- Use `-ql` for fast previews and `-qh` for final production.

### 3. Frontend Development
```bash
npm run dev
```
- Accessible at `http://localhost:3000`.

## Coding Guidelines

### Python (Backend)
- **Engine**: Avoid `DecimalNumber` and `MathTex` to ensure compatibility without a full TeX installation. Use `always_redraw` with `Text` instead.
- **Resiliency**: Wrap all GitHub API lazy-loaded properties in `try...except` to handle rate limits gracefully.
- **Theming**: Use `backend/themes.py` for consistent color palettes.

### TypeScript (Frontend)
- **UI**: High-contrast, premium "Glassmorphism" design.
- **Animations**: Use Framer Motion for web interactions to match the cinematic feel of the generated videos.

## MCP Integration
- This project supports the **Next.js 16 MCP Server** for real-time application diagnostics and state access.
- Configuration: `.mcp.json` in the root.
