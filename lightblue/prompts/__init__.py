from datetime import datetime
from functools import partial
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_HERE = Path(__file__).parent
env = Environment(loader=FileSystemLoader(_HERE / "templates"), autoescape=True)

SYSTEM_PROMPT_TEMPLATE = "system_prompt.md"
CONTEXT_TEMPLATE = "context.md"


def render_template(template_file_name: str, **kwargs):
    template = env.get_template(template_file_name)
    return template.render(**kwargs)


render_context = partial(render_template, CONTEXT_TEMPLATE)
render_system_prompt = partial(render_template, SYSTEM_PROMPT_TEMPLATE)


def get_system_prompt(**kwargs):
    return render_system_prompt(**kwargs)


def get_context():
    return render_context(
        today=datetime.now().strftime("%Y-%m-%d"),
        cwd=Path.cwd().resolve().absolute().as_posix(),
    )
