import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
    }
)

console = Console(theme=custom_theme)


def get_config_dir() -> Path:
    """Return the per-user configuration directory for jmrec."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "jmrec"


def get_env_paths() -> list[Path]:
    """Return the supported .env locations, highest precedence first."""
    return [Path.cwd() / ".env", get_config_dir() / ".env"]


def load_env() -> None:
    """Load credentials from .env files without overriding existing variables.

    Precedence: process environment, then ./.env, then the per-user config
    directory. Variables already set in the environment always win.
    """
    for path in get_env_paths():
        if path.is_file():
            load_dotenv(dotenv_path=path, override=False)


def pandoc_install_hint() -> str:
    """Return a platform-specific command for installing Pandoc."""
    if sys.platform == "darwin":
        return "brew install pandoc"
    if sys.platform == "win32":
        return "winget install JohnMacFarlane.Pandoc"
    return "sudo apt install pandoc (or your distribution's package manager)"
