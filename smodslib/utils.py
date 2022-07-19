from datetime import datetime
from enum import Enum


class StrEnum(str, Enum):
    pass


def parse_time(text: str, templates: list[str]) -> tuple[datetime, str]:
    """
    Try to parse the input text string to transform it to a date, according to a list of templates
    :param text: Text to parse
    :param templates: list of time templates. The string will be parsed with the first template that match
    :return: The datetime resulted from parsing and the matched template or raise ValueError if no template matches
    """
    for template in templates:
        try:
            return datetime.strptime(text, template), template
        except ValueError:
            continue

    raise ValueError(f"{text} doesnt match with no one of the templates {str(templates)}")
