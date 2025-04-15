import sys
from datetime import datetime
from functools import partial
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_HERE = Path(__file__).parent
pwd_env = Environment(loader=FileSystemLoader(Path.cwd()), autoescape=True)
env = Environment(loader=FileSystemLoader(_HERE / "templates"), autoescape=True)

SYSTEM_PROMPT_TEMPLATE = "system_prompt.md"
CONTEXT_TEMPLATE = "context.md"


def _render_template(template_file_name: str, **kwargs) -> str:
    try:
        template = pwd_env.get_template(template_file_name)
    except Exception:
        template = env.get_template(template_file_name)
    return template.render(**kwargs)


render_context = partial(_render_template, CONTEXT_TEMPLATE)
render_system_prompt = partial(_render_template, SYSTEM_PROMPT_TEMPLATE)


def get_system_prompt(**kwargs) -> str:
    return f"""{render_system_prompt(**kwargs)}
<Context>
{get_context()}
</Context>
"""


def _get_filetree(path: Path) -> str:
    """Generate a string representation of a file tree for the given path.

    Only includes one level of directories without expanding subdirectories
    to avoid including large directories like node_modules.

    Args:
        path: Path to generate file tree for

    Returns:
        String representation of the file tree
    """
    if not path.exists() or not path.is_dir():
        return f"Directory not found: {path}"

    # Directories to skip
    skip_dirs = {"node_modules", "dist", "build", ".git", ".venv", "__pycache__"}

    result = []
    result.append(f"{path.name}/")

    # Get all items in the directory
    items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))

    for item in items:
        # Skip hidden files and directories
        if item.name.startswith(".") and item.name != ".env":
            continue

        # Skip directories in the skip list
        if item.is_dir() and item.name in skip_dirs:
            continue

        # Add directory with trailing slash or file
        prefix = "  "
        if item.is_dir():
            result.append(f"{prefix}├── {item.name}/")
        else:
            result.append(f"{prefix}├── {item.name}")

    # Replace the last item's prefix
    if len(result) > 1:
        result[-1] = result[-1].replace("├──", "└──")

    return "\n".join(result)


def get_context() -> str:
    return render_context(
        date=datetime.now().strftime("%Y-%m-%d"),
        cwd=Path.cwd().resolve().absolute().as_posix(),
        platform=sys.platform,
        filetree=_get_filetree(Path.cwd()),
    )
