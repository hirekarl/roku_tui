# Customization & Themes

**roku-tui** uses Textual's theme engine to provide a consistent, high-contrast visual experience.

## 🎨 Current Themes

You can switch between these themes instantly using the `theme` command:
- `theme roku-night`: Our flagship Tokyo Night-inspired palette (Default).
- `theme catppuccin`: A soft, pastel-focused palette.
- `theme nord`: An arctic, blue-tinted theme.
- `theme gruvbox`: A retro, "retro-groove" color scheme.

---

## 🛠️ Defining a New Theme

Themes are defined in `roku_tui/themes.py` using the Textual `Theme` object. If you want to contribute a new theme, follow this structure:

```python
MY_THEME = Theme(
    name="my-custom-theme",
    primary="#7aa2f7",    # Main accent color (e.g., Command names)
    secondary="#bb9af7",  # Secondary accent (e.g., Aliases)
    foreground="#c0caf5", # Primary text
    background="#1a1b26", # Main workspace background
    dark=True,
    variables={
        "surface": "#24283b",       # Command input and panel backgrounds
        "panel": "#1f2335",         # Right panel (Network) background
        "success": "#9ece6a",       # Success indicators (green)
        "warning": "#e0af68",       # Warnings (yellow)
        "error": "#f7768e",         # Errors (red)
        "accent": "#73daca",        # Miscellaneous highlights
        "bg-dark": "#16161e",       # Deep background (e.g., Status Bar)
        "muted-border": "#414868",  # Border color for inactive panels
    },
)
```

### Key Requirements
- **High Contrast**: Ensure text remains readable against the `surface` and `panel` colors.
- **Black Backgrounds**: The Remote Panel and Console Panel often use `black` for the primary work area; ensure your `primary` and `secondary` colors pop against it.

---

## 🧪 Testing Your Theme

1.  Add your `Theme` object to `roku_tui/themes.py`.
2.  Register it in the `THEMES` dictionary at the bottom of the file.
3.  Run the app in dev mode to see your changes immediately:
    ```bash
    uv run textual run --dev roku_tui/__main__.py
    ```
4.  Type `theme <your-theme-name>` in the console.
