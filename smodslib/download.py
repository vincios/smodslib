from urllib.parse import urlparse

import requests

from .exceptions import UnsupportedHostError
from .model import ModBase

SUPPORTED_HOSTS = ["modsbase.com", "uploadfiles.eu"]


def generate_download_url(mod: ModBase):
    """
    Generate the download url of a given mod.

    Mods are hosted on file hosting services (i.e. modsbase.com or uploadfiles.eu), this method generate the download
    url from the service that hosts the mod.

    :param mod: Mod to download
    :return: The download url
    """
    mod_url = mod.latest_revision.download_url
    hostname = urlparse(mod_url).hostname

    if hostname not in SUPPORTED_HOSTS:
        raise UnsupportedHostError(f"{hostname} in not a supported hosting services")

    if hostname == "uploadfiles.eu":
        # if hosting service is uploadfiles.eu we have to follow two redirects
        with requests.get(mod_url, allow_redirects=False) as r:
            r.raise_for_status()
            mod_url = r.headers['Location']

    url_parts = mod_url.split('/')
    download_id = url_parts[-2]

    data = {
        "op": "download2",
        "id": download_id,
        "rand": "",
        "referer": "https://smods.ru/",
        "method_free": "Free Download",
        "method_premium": ""
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    with requests.post(mod_url, headers=headers, data=data, allow_redirects=False) as r:
        r.raise_for_status()
        download_url = r.headers['Location']

    return download_url
