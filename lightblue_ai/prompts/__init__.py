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


def get_context() -> str:
    return render_context(
        date=datetime.now().strftime("%Y-%m-%d"),
        cwd=Path.cwd().resolve().absolute().as_posix(),
        platform=sys.platform,
    )
