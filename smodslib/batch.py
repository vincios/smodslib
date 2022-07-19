from typing import Union

from .model import ModDependency
from .smods import create_mod_dependencies_tree


def generate_dependency_tree(mods_ids: Union[str, list[str]], recursive=False) -> list[ModDependency]:
    """
    Generate the dependency tree list of all given mods.

    Note that if multiple mods are passed as the first parameter, the dependency list will merge all dependencies
    together, so it will not be possible to separate individual mod trees.

    :param mods_ids: one o more mods to analyze
    :param recursive: Whether to go recursively in depth and also analyze dependencies or not
    :return: The list of dependencies of the given mods
    """
    if not isinstance(mods_ids, list):
        mods_ids = [mods_ids]

    dependencies_list: list[ModDependency] = []

    for mod_id in mods_ids:
        dependencies_list = create_mod_dependencies_tree(mod_id, dependencies_list, recursive=recursive)

    return dependencies_list
