from datetime import datetime
from typing import Optional, Union
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup, element, Tag

from .model import ModDependency, ModBase, ModRevision, ModCatalogueItem, FullMod
from .exceptions import NoResultError
from .utils import parse_time


def _get_mod_bs(sky_id_or_bs: Union[str, BeautifulSoup, Tag]) -> BeautifulSoup:
    """
    Analyze the input. If it is a Mod's id or a BeautifulSoup object, returns a BeautifulSoup object. Otherwise,
    throws an error.
    :param sky_id_or_bs: a Mod's id or a BeautifulSoup object of a Mod's html page
    :return: BeautifulSoup object of the given Mod
    """
    if isinstance(sky_id_or_bs, str):
        url = f"https://smods.ru/archives/{sky_id_or_bs}"

        page = requests.get(url)
        bs = BeautifulSoup(page.text, "html.parser")
    elif isinstance(sky_id_or_bs, BeautifulSoup) or isinstance(sky_id_or_bs, Tag):
        bs = sky_id_or_bs
    else:
        raise Exception("First argument must be a mod id or a BeautifulSoup object")

    return bs


def _is_mod_in_list(mod: ModBase, mods_list: list[ModBase]) -> int:
    """
    Return the index of the first mod in mods_list that match the id of the given mod.
    :param mod: Mod to search by id.
    :param mods_list: list of mods where to search.
    :return: The index of the first matching element, or -1 if no items found.
    """
    for i, item in enumerate(mods_list):
        if item.id == mod.id:
            return i

    return -1


def create_mod_base_from_catalogue_page(bs_article_element: Tag) -> ModBase:
    """
    Create a ModBase object from a BeautifulSoup Tag element. This Tag element must be the html "article" tag of a
    Skymod catalogue page
    :param bs_article_element: BeautifulSoup "article" Tag of the catalogue page
    :return: The ModBase object
    """
    metadata_box = bs_article_element.find("div", class_="skymods-excerpt-meta")
    metadata_items = metadata_box.find_all("p")  # metadata box has 4 paragraphs
    download_button = bs_article_element.find(text="Download").parent

    # name property
    name = bs_article_element.find("h2", class_="post-title").text.strip()

    # id property
    sky_id = bs_article_element["id"][5:]  # remove "post-" from id

    # steam id property
    steam_url = metadata_items[3].find("a")['href']  # 4th metadata paragraph contains the steam url
    steam_id = parse_qs(urlparse(steam_url).query)['id'][0]

    # authors property
    authors_paragraph = metadata_items[0]  # 1st metadata paragraph contains the authors list
    authors = [author.text for author in authors_paragraph.parent.parent.find_all("a")]

    # has dependencies property
    has_dependencies = "skymods-required-warning" in download_button["class"]

    # latest revision
    revision_text = metadata_box.find("span", class_="skymods-item-date").text.replace("UTC", "").strip()
    revision_date, matched_template = parse_time(revision_text, ["%d %b, %Y at %H:%M", "%d %b at %H:%M"])
    if "%Y" not in matched_template:
        revision_date = revision_date.replace(year=datetime.now().year)
    revision_url = download_button['href']
    revision = ModRevision(revision_text, revision_date, revision_url)

    # published date property
    published_date_text = bs_article_element.find("time", class_="published")["datetime"]
    published_date, _ = parse_time(published_date_text, ["%Y-%m-%d %H:%M:%S"])

    # size property
    size = metadata_box.find("span", class_="skymods-item-file-size").text

    # category property
    category = bs_article_element.find("a", rel="category tag").text

    return ModBase(name, sky_id, steam_id, authors, size, published_date, has_dependencies, revision, category)


def create_mod_base_from_steam_id(steam_id: str) -> ModBase:
    """
    Create a ModBase object of a Mod given its steam id
    :param steam_id: steam id of the Mod
    :return: ModBase object
    """
    search_url = f"https://smods.ru/?s={steam_id}"
    page = requests.get(search_url)
    bs = BeautifulSoup(page.text, "html.parser")
    article = bs.find("article")

    if not article:
        raise NoResultError(f"No item found with steam id {steam_id}")

    return create_mod_base_from_catalogue_page(article)


def create_mod_base_from_id(sky_id: str) -> ModBase:
    """
    Create a ModBase object of a Mod given its Skymod id
    :param sky_id: Skymod id of the Mod
    :return: ModBase object
    """
    bs = _get_mod_bs(sky_id)
    return create_mod_base_from_bs_page(bs)


def create_mod_base_from_bs_page(bs: BeautifulSoup) -> ModBase:
    """
    Create a ModBase object of a Mod given the BeautifulSoup object of the full Mod html page
    :param bs: BeautifulSoup object of the full Mod html page
    :return: ModBase object
    """
    # name property
    name = bs.find("h1", class_="post-title").text

    # id property
    sky_id = next((cla for cla in bs.find("article")['class'] if cla.startswith("post-")))[5:]

    # steam id property
    steam_url = bs.find("div", class_="skymods-single-before").find("a", string="On Steam Workshop")['href']
    steam_id = parse_qs(urlparse(steam_url).query)['id'][0]

    # authors property
    authors = get_mod_authors(bs)

    # has dependencies property
    has_dependencies = bs.find("div", id="required-items") is not None

    # latest revision
    revision, _ = get_mod_revisions(bs)

    # published date property
    published_date, _ = get_mod_dates(bs)

    # size property
    size = get_mod_size(bs)

    # category property
    category = get_mod_category(bs)

    return ModBase(name, sky_id, steam_id, authors, size, published_date, has_dependencies, revision, category)


def get_mod_id_by_steam_id(steam_id: str) -> str:
    """
    Retrieve the Skymod id of a Mod, given its Steam id. If the item is not present on skymods
    a NoResultException is raised.
    :param steam_id: Mod's Steam id
    :return: Mod's Skymod id, or NoResultException if item is not found
    """
    search_url = f"https://smods.ru/?s={steam_id}"
    page = requests.get(search_url)
    bs = BeautifulSoup(page.text, "html.parser")

    item = bs.find("article")

    if not item:
        raise NoResultError(f"No item found with steam id {steam_id}")

    sky_id = item["id"][5:]  # remove "post-" from id
    return sky_id


def get_mod_authors(sky_id_or_bs: Union[str, BeautifulSoup]) -> list[str]:
    """
    Fetch the authors list of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: Mod authors list
    """

    bs = _get_mod_bs(sky_id_or_bs)
    authors_paragraph = bs.find(string="Author:") or bs.find(string="Authors:")
    return [author.text for author in authors_paragraph.parent.parent.find_all("a")]


def get_mod_description(sky_id_or_bs: Union[str, BeautifulSoup]) -> tuple[str, str]:
    """
    Fetch the html and plain description of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page or infobox element, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: Html and plain description of the given Mod
    """
    bs = _get_mod_bs(sky_id_or_bs)

    if isinstance(bs, BeautifulSoup) or "skymods-single-before" not in bs['class']:
        # the argument is the full page, so we have to find the infobox
        bs = bs.find("div", class_="skymods-single-before")

    description = ""
    plain_description = ""

    for tag in bs.next_siblings:
        if isinstance(tag, element.Tag) and "class" in tag and tag["class"] == "skymods-single-after":
            break
        else:
            description += str(tag)
            plain_description += tag.get_text(separator="", strip=True)

    return description, plain_description


def get_mod_dates(sky_id_or_bs: Union[str, BeautifulSoup]) -> tuple[datetime, datetime]:
    """
    Fetch the published and updated date of the given Mod id or BeautifulSoup page. Can be None.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: published and updated date of the given Mod. Can be none if no one or both are not defined.
    """
    bs = _get_mod_bs(sky_id_or_bs)

    dates = bs.find("p", class_="post-byline").find_all("time")

    published_date, updated_date = None, None

    for date in dates:
        parsed_date, _ = parse_time(str(date["datetime"]), ["%B %d, %Y"])
        if "published" in date["class"]:
            published_date = parsed_date
        elif "updated" in date["class"]:
            updated_date = parsed_date

    return published_date, updated_date


def get_mod_size(sky_id_or_bs: Union[str, BeautifulSoup]) -> str:
    """
    Fetch the size of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: size of the given Mod.
    """
    bs = _get_mod_bs(sky_id_or_bs)

    return bs.find("span", class_="skymods-item-file-size").text


def get_mod_rating(sky_id_or_bs: Union[str, BeautifulSoup]) -> int:
    """
    Fetch the rating of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: rating of the given Mod.
    """
    bs = _get_mod_bs(sky_id_or_bs)

    return len(bs.find("p", class_="skymods-item-rating").find_all("path", fill="#3b8dbd"))


def get_mod_dlcs(sky_id_or_bs: Union[str, BeautifulSoup]) -> Optional[list[str]]:
    """
    Fetch the dlcs list required by the given Mod id or BeautifulSoup page. Can be None.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page or the download box element,
     otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: list of dlcs required by the given Mod.
    """
    bs = _get_mod_bs(sky_id_or_bs)

    required_items_box = bs.find("div", id="required-items")
    if required_items_box:
        for section in required_items_box.find_all("div", recursive=False):
            if "Required DLC" in section.text:
                dlcs = []
                for item in section.find_all("a"):
                    dlcs.append(item.text)

                return dlcs

    return None


def get_mod_dependencies(sky_id_or_bs: Union[str, BeautifulSoup]) -> Optional[list[ModDependency]]:
    """
    This is a shorthand for create_mod_dependencies_tree(sky_id_or_bs, [ ], False)

    Fetch the mods dependencies list required by the given Mod id or BeautifulSoup page. Can be None. This list doesn't
    contain nested dependencies of the listed Mods.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: list of mod dependencies required by the given Mod.
    """
    bs = _get_mod_bs(sky_id_or_bs)

    required_items_box = bs.find("div", id="required-items")
    if required_items_box:
        for section in required_items_box.find_all("div", recursive=False):
            if "Required items" in section.text:
                return create_mod_dependencies_tree(bs, [])

    return None


def get_mod_revisions(sky_id_or_bs: Union[str, BeautifulSoup]) -> tuple[ModRevision, Union[list[ModRevision], None]]:
    """
    Fetch the revisions list of the given Mod id or BeautifulSoup page. The latest revision will be returned as separate
    object
    contain nested dependencies of the listed Mods.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: two elements: the latest revision (always not null) and the old revisions (if any, otherwise None)
    """

    bs = _get_mod_bs(sky_id_or_bs)
    infobox = bs.find("div", class_="skymods-single-before")
    download_box = bs.find("div", class_="skymods-single-after")

    old_revisions: Optional[list[ModRevision]] = None

    revisions_box = download_box.find("div", id="revisions")
    if revisions_box:
        old_revisions = []
        links_items = revisions_box.find_all("a")
        for item in links_items:
            name = item.text.replace("UTC", "").strip()
            date, matched_template = parse_time(name, ["%d %b, %Y at %H:%M", "%d %b at %H:%M"])
            if "%Y" not in matched_template:
                date = date.replace(year=datetime.now().year)

            download_url = item['href']
            revision = ModRevision(name, date, download_url)
            old_revisions.append(revision)

    old_revisions = sorted(old_revisions, key=lambda itm: itm.date) if old_revisions else None

    # last revision
    name = infobox.find(text="Last revision:").parent.parent.find("span", class_="skymods-item-date").text.replace(
        "UTC", "").strip()
    date, matched_template = parse_time(name, ["%d %b, %Y at %H:%M", "%d %b at %H:%M"])
    if "%Y" not in matched_template:
        date = date.replace(year=datetime.now().year)
    download_url = download_box.find("a", class_="skymods-excerpt-btn")['href']
    latest_revision = ModRevision(name, date, download_url)

    return latest_revision, old_revisions


def get_mod_image_url(sky_id_or_bs: Union[str, BeautifulSoup]) -> str:
    """
    Fetch the image url of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: Mod's image url
    """

    bs = _get_mod_bs(sky_id_or_bs)
    return bs.find("div", class_="skymods-single-preview-wrap").find("img")['src']


def get_mod_tags(sky_id_or_bs: Union[str, BeautifulSoup]) -> list[str]:
    """
    Fetch the tags of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: Mod's tags
    """

    bs = _get_mod_bs(sky_id_or_bs)
    tags_box = bs.find("p", class_="post-tags")
    return [a['href'] for a in tags_box.find_all("a")] if tags_box else []


def get_mod_category(sky_id_or_bs: Union[str, BeautifulSoup]) -> str:
    """
    Fetch the category of the given Mod id or BeautifulSoup page.

    NB: If a BeautifulSoup page is given, make sure it is the full Mod page, otherwise result will be unpredictable!

    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :return: Mod's category
    """
    bs = _get_mod_bs(sky_id_or_bs)
    return bs.find("a", rel="category tag").text


def create_mod_dependencies_tree(sky_id_or_bs: Union[str, BeautifulSoup], dependencies_list: list[ModDependency],
                                 recursive=False) -> list[ModDependency]:
    """
    Creates all the dependencies' tree of a given Mod (it's id or BS page object).
    :param sky_id_or_bs: Mod's skymod id or the BeautifulSoup object of a Mod's html page
    :param dependencies_list: starting dependencies list, useful for a batch mode. Should be an empty list on the first run.
    :param recursive: if recursive children dependencies should be added to the result
    :return: a list of ModDependency objects, one for each Mod dependency
    """
    bs = _get_mod_bs(sky_id_or_bs)

    root: ModBase = create_mod_base_from_bs_page(bs)

    # first, we scrape the requirements list from the requirements box of the html page...
    requirements_list: list[ModBase] = []
    dependencies_box = bs.find(text="Required items:")
    if dependencies_box:
        dependencies_box = dependencies_box.parent.parent

        for dependency in dependencies_box.find_all("a"):
            if "https://smods.ru/" in dependency['href']:
                try:
                    steam_id = parse_qs(urlparse(dependency['href']).query)['s'][0]
                    mod = create_mod_base_from_steam_id(steam_id)
                    requirements_list.append(mod)
                except NoResultError:
                    pass

    # ... then, for each mod into the requirements box we create a ModDependency object...
    for mod in requirements_list:
        search_index = _is_mod_in_list(mod, dependencies_list)
        if search_index >= 0:
            # we check that the root mod is not already into the required_by list, to avoid duplicates
            if _is_mod_in_list(root, dependencies_list[search_index].required_by) < 0:
                dependencies_list[search_index].required_by.append(root)
        else:
            dependency = ModDependency.from_mod(mod)
            dependency.required_by.append(root)
            dependencies_list.append(dependency)

        # ... and, if recursive is True, we repeat the whole process for each dependency
        if recursive:
            dependencies_list = create_mod_dependencies_tree(mod.id, dependencies_list, recursive=True)

    return dependencies_list


def create_full_mod_by_id(sky_id: str) -> FullMod:
    """
    Get the FullMod object of a mod, given its id
    :param sky_id: mod's Skymod id
    :return: FullMod object
    """
    return create_full_mod(f"https://smods.ru/archives/{sky_id}")


def create_full_mod(url: str) -> FullMod:
    """
    Get the FullMod object of a mod, given its url
    :param url: mod's url
    :return: FullMod object
    """
    page = requests.get(url)
    bs = BeautifulSoup(page.text, "html.parser")
    infobox = bs.find("div", class_="skymods-single-before")
    download_box = bs.find("div", class_="skymods-single-after")

    base_mod = create_mod_base_from_bs_page(bs)
    mod = FullMod.from_mod(base_mod)

    # description
    description, plain_description = get_mod_description(infobox)
    mod.description = description
    mod.plain_description = plain_description

    # dates
    published_date, updated_date = get_mod_dates(bs)
    mod.updated_date = updated_date

    # rating
    mod.rating = get_mod_rating(bs)

    # required items
    mod.dlc_requirements = get_mod_dlcs(download_box)
    mod.mod_requirements = get_mod_dependencies(bs)

    # revisions
    latest_revision, old_revisions = get_mod_revisions(bs)
    mod.other_revisions = old_revisions

    # image
    mod.image_url = get_mod_image_url(bs)

    # tags
    mod.tags = get_mod_tags(bs)

    # category
    mod.category = get_mod_category(bs)

    return mod


def create_catalogue_item_from_catalogue_result(bs_article_element: Tag) -> ModCatalogueItem:
    """
    Create a ModCatalogueItem object from a BeautifulSoup Tag element. This Tag element must be the html "article" tag
    of a Skymod catalogue page
    :param bs_article_element: BeautifulSoup "article" Tag of the catalogue page
    :return: The ModCatalogueItem object
    """

    base_mod = create_mod_base_from_catalogue_page(bs_article_element)
    catalogue_mod = ModCatalogueItem.from_mod(base_mod)

    catalogue_mod.rating = len(bs_article_element.find("p", class_="skymods-item-rating")
                               .find_all("path", fill="#3b8dbd"))

    catalogue_mod.image_url = bs_article_element.find("div", class_="post-thumbnail").find("img")['src']

    return catalogue_mod
