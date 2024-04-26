"""
cookiecutter.replay.

-------------------
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
import yaml

from cookiecutter.utils import make_sure_path_exists
from cookiecutter.variables import CookiecutterVariable

if TYPE_CHECKING:
    from pathlib import Path


def get_file_name(replay_dir: Path | str, template_name: str) -> str:
    """Get the name of file."""
    suffix = '.yaml' if not template_name.endswith('.yaml') else '.json'
    file_name = f'{template_name}{suffix}'
    return os.path.join(replay_dir, file_name)


def dump(replay_dir: Path | str, template_name: str, context: dict[str, Any]) -> None:
    """Write json data to file."""
    make_sure_path_exists(replay_dir)

    if 'cookiecutter' not in context:
        raise ValueError('Context is required to contain a cookiecutter key')

    replay_file = get_file_name(replay_dir, template_name)

    with open(replay_file, 'w', encoding="utf-8") as outfile:
        yaml.safe_dump(context, outfile, indent=2)


def load(replay_dir: Path | str, template_name: str) -> dict[str, Any]:
    """Read json data from file."""
    replay_file = get_file_name(replay_dir, template_name)

    with open(replay_file, encoding="utf-8") as infile:
        context: dict[str, Any] = yaml.safe_load(infile)

    if 'cookiecutter' not in context:
        raise ValueError('Context is required to contain a cookiecutter key')
    
    context['cookiecutter'] = CookiecutterVariable.from_dict(context['cookiecutter'])

    return context
