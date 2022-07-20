from urllib.parse import urlencode, urlunsplit
from bs4 import BeautifulSoup

import requests

from .model import CatalogueParameters, ModCatalogueItem
from .smods import create_catalogue_item_from_catalogue_result


def search(query: str, page: int = 0, filters: CatalogueParameters = None) -> list[ModCatalogueItem]:
    """
    Performs a search into the catalogue using keywords of the query parameters.
    The result can boe filtered using filters parameters.

    The result is always paginated: the method returns only the first 10 results. If more results are needed, so a new
    call of this method must be performed, incrementing the page parameter
    :param query: Keyword to search
    :param page: pagination page
    :param filters: filters to apply to the results
    :return: up to 10 catalogue items
    """

    parameters = {
        "s": query,
    }

    if filters:
        for key, value in filters.items():
            if value:
                parameters[key] = value.value

    url_path = "/" if not page else f"/page/{page}"
    url_query = urlencode(parameters)

    search_endpoint = urlunsplit(("https", "smods.ru", url_path, url_query, ""))

    page = requests.get(search_endpoint)
    bs = BeautifulSoup(page.text, "html.parser")

    return [create_catalogue_item_from_catalogue_result(article_item) for article_item in bs.find_all("article")]
