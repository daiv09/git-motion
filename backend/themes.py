# themes.py
def get_theme(name="github_dark"):
    themes = {
        "github_dark": {
            "bg": "#0d1117",
            "primary": "#58a6ff",
            "secondary": "#30363d",
            "accent": "#f0883e",
            "text": "#c9d1d9",
            "sub": "#8b949e",
            "green": "#3fb950",
            "red": "#f85149"
        },
        "emerald": {
            "bg": "#064e3b",
            "primary": "#10b981",
            "secondary": "#065f46",
            "accent": "#f59e0b",
            "text": "#ecfdf5",
            "sub": "#a7f3d0",
            "green": "#34d399",
            "red": "#fb7185"
        }
    }
    return themes.get(name, themes["github_dark"])