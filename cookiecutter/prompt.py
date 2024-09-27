"""Functions for prompting the user for project info."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import OrderedDict
from itertools import starmap
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Union

from jinja2 import Environment
from jinja2.exceptions import UndefinedError
from rich.prompt import Confirm, InvalidResponse, Prompt, PromptBase
from typing_extensions import TypeAlias

from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.utils import create_env_with_context, rmtree
from cookiecutter.environment import StrictEnvironment
from cookiecutter.variables import CookiecutterVariable

def read_user_variable(var_name: str, default_value, prompts=None, prefix: str = ""):
    """Prompt user for variable and return the entered value or given default.

    :param str var_name: Variable of the context to query the user
    :param default_value: Value that will be returned if no input happens
    """
    question = (
        prompts[var_name]
        if prompts and var_name in prompts and prompts[var_name]
        else var_name
    )

    while True:
        variable = Prompt.ask(f"{prefix}{question}", default=default_value)
        if variable is not None:
            break

    return variable


class YesNoPrompt(Confirm):
    """A prompt that returns a boolean for yes/no questions."""

    yes_choices = ["1", "true", "t", "yes", "y", "on"]
    no_choices = ["0", "false", "f", "no", "n", "off"]

    def process_response(self, value: str) -> bool:
        """Convert choices to a bool."""
        value = value.strip().lower()
        if value in self.yes_choices:
            return True
        elif value in self.no_choices:
            return False
        else:
            raise InvalidResponse(self.validate_error_message)


def read_user_yes_no(var_name, default_value, prompts=None, prefix: str = ""):
    """Prompt the user to reply with 'yes' or 'no' (or equivalent values).

    - These input values will be converted to ``True``:
      "1", "true", "t", "yes", "y", "on"
    - These input values will be converted to ``False``:
      "0", "false", "f", "no", "n", "off"

    Actual parsing done by :func:`prompt`; Check this function codebase change in
    case of unexpected behaviour.

    :param str question: Question to the user
    :param default_value: Value that will be returned if no input happens
    """
    question = (
        prompts[var_name]
        if prompts and var_name in prompts and prompts[var_name]
        else var_name
    )
    return YesNoPrompt.ask(f"{prefix}{question}", default=default_value)


def read_repo_password(question: str) -> str:
    """Prompt the user to enter a password.

    :param question: Question to the user
    """
    return Prompt.ask(question, password=True)


def read_user_choice(var_name: str, options: list, prompts=None, prefix: str = ""):
    """Prompt the user to choose from several options for the given variable.

    The first item will be returned if no input happens.

    :param var_name: Variable as specified in the context
    :param list options: Sequence of options that are available to select from
    :return: Exactly one item of ``options`` that has been chosen by the user
    """
    if not options:
        raise ValueError

    choice_map = OrderedDict((f'{i}', value) for i, value in enumerate(options, 1))
    choices = choice_map.keys()

    question = f"Select {var_name}"

    choice_lines: Iterator[str] = starmap(
        "    [bold magenta]{}[/] - [bold]{}[/]".format, [(k, v["name"]) for k, v in choice_map.items()]
    )

    # Handle if human-readable prompt is provided
    if prompts and var_name in prompts:
        if isinstance(prompts[var_name], str):
            question = prompts[var_name]
        else:
            if "__prompt__" in prompts[var_name]:
                question = prompts[var_name]["__prompt__"]
            choice_lines = (
                f"    [bold magenta]{i}[/] - [bold]{prompts[var_name][p['name']]}[/]"
                if p["name"] in prompts[var_name]
                else f"    [bold magenta]{i}[/] - [bold]{p['name']}[/]"
                for i, p in choice_map.items()
            )
    prompt = '\n'.join(
        (
            f"{prefix}{question}",
            "\n".join(choice_lines),
            "    Choose from",
        )
    )

    user_choice = Prompt.ask(prompt, choices=list(choices), default=next(iter(choices)))
    return choice_map[user_choice]


DEFAULT_DISPLAY = 'default'


def process_json(user_value: str):
    """Load user-supplied value as a JSON dict.

    :param user_value: User-supplied value to load as a JSON dict
    """
    try:
        user_dict = json.loads(user_value, object_pairs_hook=OrderedDict)
    except Exception as error:
        # Leave it up to click to ask the user again
        raise InvalidResponse('Unable to decode to JSON.') from error

    if not isinstance(user_dict, dict):
        # Leave it up to click to ask the user again
        raise InvalidResponse('Requires JSON dict.')

    return user_dict


class JsonPrompt(PromptBase[dict]):
    """A prompt that returns a dict from JSON string."""

    default = None
    response_type = dict
    validate_error_message = "[prompt.invalid]  Please enter a valid JSON string"

    @staticmethod
    def process_response(value: str) -> dict[str, Any]:
        """Convert choices to a dict."""
        return process_json(value)


def read_user_dict(var_name: str, default_value, prompts=None, prefix: str = ""):
    """Prompt the user to provide a dictionary of data.

    :param var_name: Variable as specified in the context
    :param default_value: Value that will be returned if no input is provided
    :return: A Python dictionary to use in the context.
    """
    if not isinstance(default_value, dict):
        raise TypeError

    question = (
        prompts[var_name]
        if prompts and var_name in prompts and prompts[var_name]
        else var_name
    )
    user_value = JsonPrompt.ask(
        f"{prefix}{question} [cyan bold]({DEFAULT_DISPLAY})[/]",
        default=default_value,
        show_default=False,
    )
    return user_value


def read_user_variable_json(
    var_name: str,
    exit_condition: str,
    prefix: str = "",
    inner_func: Callable = None,
    inner_func_args: Dict[str, Any] = [],
):
    """
    Prompt user for multiple elements and return as dict.

    :param var_name: name of dict variable
    :param exit_condition: input string to stop the loop
    :param inner_func: function to call during loop
    :param inner_func_args: arguments of inner function
    :return: dict of strings to empty dict or inner func result
    """
    variables = dict()
    loop = True

    while loop:
        var = read_user_variable(
            var_name=var_name, default_value=exit_condition, prefix=prefix
        )
        if var != exit_condition:
            variables[var] = dict()
            if inner_func is not None:
                variables[var] = inner_func(prefix=prefix, **inner_func_args)
        else:
            loop = prompt_loop_exit(prefix=prefix)

    return variables


def read_user_variable_list(var_name: str, exit_condition: str, prefix: str = ""):
    """
    Prompt user for multiple elements and return as list.

    :param var_name: name of dict variable
    :param exit_condition: input string to stop the loop
    :return: list of strings
    """
    return list(read_user_variable_json(var_name, exit_condition, prefix).keys())


def prompt_loop_exit(prefix: str = ""):
    """
    Prompts the user for input to exit a loop.

    :return: True to continue looping, False to stop loop
    """
    stop_loop = read_user_yes_no(
        var_name="Exit?", default_value="Yes", prefix=prefix
    )
    return not stop_loop


_Raw: TypeAlias = Union[bool, Dict["_Raw", "_Raw"], List["_Raw"], str, None]


def render_variable(
    env: Environment,
    raw: _Raw,
    cookiecutter_dict: dict[str, Any],
) -> str:
    """Render the next variable to be displayed in the user prompt.

    Inside the prompting taken from the cookiecutter.json file, this renders
    the next variable. For example, if a project_name is "Peanut Butter
    Cookie", the repo_name could be be rendered with:

        `{{ cookiecutter.project_name.replace(" ", "_") }}`.

    This is then presented to the user as the default.

    :param Environment env: A Jinja2 Environment object.
    :param raw: The next value to be prompted for by the user.
    :param dict cookiecutter_dict: The current context as it's gradually
        being populated with variables.
    :return: The rendered value for the default variable.
    """
    if raw is None or isinstance(raw, bool):
        return raw
    elif isinstance(raw, dict):
        return {
            render_variable(env, k, cookiecutter_dict): render_variable(
                env, v, cookiecutter_dict
            )
            for k, v in raw.items()
        }
    elif isinstance(raw, list):
        return [render_variable(env, v, cookiecutter_dict) for v in raw]
    elif not isinstance(raw, str):
        raw = str(raw)

    template = env.from_string(raw)

    return template.render(cookiecutter=cookiecutter_dict)


def _prompts_from_options(options: Dict[str, Any]) -> dict:
    """Process template options and return friendly prompt information."""
    prompts = {"__prompt__": "Select a template"}
    for opt in options:
        title = opt["name"]
        description = opt.get("description", "")
        label = title if title == description else f"{title} ({description})"
        prompts[title] = label
    return prompts


def prompt_choice_for_template(options: Dict[str, Any], no_input: bool):
    """Prompt user with a set of options to choose from.

    :param no_input: Do not prompt for user input and return the first available option.
    """
    prompts = {"template": _prompts_from_options(options)}
    return options[0] if no_input else read_user_choice("template", options, prompts, "")


def prompt_choice_for_config(
    cookiecutter_dict: dict[str, Any],
    env: Environment,
    key: str,
    options,
    no_input: bool,
    prompts=None,
    prefix: str = "",
) -> OrderedDict[str, Any] | str:
    """Prompt user with a set of options to choose from.

    :param no_input: Do not prompt for user input and return the first available option.
    """
    rendered_options = [render_variable(env, raw, cookiecutter_dict) for raw in options]
    if no_input:
        return rendered_options[0]
    return read_user_choice(key, rendered_options, prompts, prefix)


def prompt_for_config(
    context: dict[str, Any], no_input: bool = False
) -> OrderedDict[str, Any]:
    """Prompt user to enter a new config.

    :param dict context: Source for field names and sample values.
    :param no_input: Do not prompt for user input and use only values from context.
    """
    cookiecutter_dict = OrderedDict([])
    env = create_env_with_context(context)

    # First pass: Handle simple and raw variables, plus choices.
    # These must be done first because the dictionaries keys and
    # values might refer to them.
    count = 0
    visible_prompts = [v.prompt for v in context['cookiecutter'].variables if not v.name.startswith("_")]
    size = len(visible_prompts)
    for v in context['cookiecutter'].variables:
        if v.name.startswith('_') and not v.name.startswith('__'):
            cookiecutter_dict[v.name] = v.value
            continue
        elif v.name.startswith('__'):
            cookiecutter_dict[v.name] = render_variable(env, v.value, cookiecutter_dict)
            continue

        prefix = ""
        if not isinstance(v.value, dict):
            count += 1
            prefix = f"  [dim][{count}/{size}][/] "

        try:
            cookiecutter_dict = get_cookiecutter_values(
                v, cookiecutter_dict, env, no_input, prefix
            )
        except UndefinedError as err:
            msg = f"Unable to render variable '{v.name}'"
            raise UndefinedVariableInTemplate(msg, err, context) from err

    # Second pass; handle the dictionaries.
    for v in context['cookiecutter'].variables:
        # Skip private type dicts not to be rendered.
        if v.name.startswith('_') and not v.name.startswith('__'):
            continue

        else:
            try:
                if isinstance(v.value, dict):
                    # We are dealing with a dict variable
                    count += 1
                    prefix = f"  [dim][{count}/{size}][/] "
                    val = render_variable(env, v.value, cookiecutter_dict)

                    if not no_input and not v.name.startswith('__'):
                        val = read_user_dict(v.name, val, {v.name: v.prompt}, prefix)

                    cookiecutter_dict[v.name] = val
            except UndefinedError as err:
                msg = f"Unable to render variable '{v.name}'"
                raise UndefinedVariableInTemplate(msg, err, context) from err

    return cookiecutter_dict


def choose_nested_template(template_variable: CookiecutterVariable, repo_dir: str, no_input: bool = False) -> str:
    """Prompt user to select the nested template to use.

    :param context: Source for field names and sample values.
    :param repo_dir: Repository directory.
    :param no_input: Do not prompt for user input and use only values from context.
    :returns: Path to the selected template.
    """
    val = prompt_choice_for_template(template_variable.get_metadata(), no_input)
    template = val["path"]

    template = Path(template) if template else None
    if not (template and not template.is_absolute()):
        raise ValueError("Illegal template path")

    repo_dir = Path(repo_dir).resolve()
    template_path = (repo_dir / template).resolve()
    # Return path as string
    return f"{template_path}"


def prompt_and_delete(path: Path | str, no_input: bool = False) -> bool:
    """
    Ask user if it's okay to delete the previously-downloaded file/directory.

    If yes, delete it. If no, checks to see if the old version should be
    reused. If yes, it's reused; otherwise, Cookiecutter exits.

    :param path: Previously downloaded zipfile.
    :param no_input: Suppress prompt to delete repo and just delete it.
    :return: True if the content was deleted
    """
    # Suppress prompt if called via API
    if no_input:
        ok_to_delete = True
    else:
        question = (
            f"You've downloaded {path} before. Is it okay to delete and re-download it?"
        )

        ok_to_delete = read_user_yes_no(question, 'yes')

    if ok_to_delete:
        if os.path.isdir(path):
            rmtree(path)
        else:
            os.remove(path)
        return True
    else:
        ok_to_reuse = read_user_yes_no(
            "Do you want to re-use the existing version?", 'yes'
        )

        if ok_to_reuse:
            return False

        sys.exit()

def get_cookiecutter_values(v: CookiecutterVariable, cookiecutter_dict: dict, env: StrictEnvironment, no_input: bool, prefix: str, parent: str = ""):
    """Get cookiecutter values from keys.

    :param key: key to retrieve value for
    :param value: raw value to get
    :param cookiecutter_dict: current cookiecutter dict
    :param env: jinja environment
    :param no_input:  do not prompt for user input and use only values from context
    :param prompts: dictionary of prompts
    :param prefix: prefix for prompt
    """
    name = parent + v.name
    if isinstance(v.value, list):
        # We are dealing with a choice variable
        val = prompt_choice_for_config(
            cookiecutter_dict, env, v.name, v.value, no_input, {v.name: v.prompt}, prefix
        )
        cookiecutter_dict[name] = val["name"]
    elif isinstance(v.value, bool):
        # We are dealing with a boolean variable
        if no_input:
            cookiecutter_dict[name] = render_variable(
                env, v.value, cookiecutter_dict
            )
        else:
            cookiecutter_dict[name] = read_user_yes_no(v.name, v.value, {v.name: v.prompt}, prefix)
    elif not isinstance(v.value, dict):
        # We are dealing with a regular variable
        val = render_variable(env, v.value, cookiecutter_dict)

        if not no_input:
            val = read_user_variable(v.name, val, {v.name: v.prompt}, prefix)

        cookiecutter_dict[name] = val
    for branch in v.variables:
        if branch.matches == cookiecutter_dict[name]:
            cookiecutter_dict = get_cookiecutter_values(branch, cookiecutter_dict, env, no_input, prefix, name + "/")
    return cookiecutter_dict