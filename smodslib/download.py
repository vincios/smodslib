import os.path
from typing import Callable, Union
from urllib.parse import urlparse

import cloudscraper
from requests import HTTPError

from .exceptions import UnsupportedHostError
from .model import ModBase, ModRevision
from .smods import create_mod_base_from_id

SUPPORTED_HOSTS = ["modsbase.com", "uploadfiles.eu"]


def generate_download_url_from_id(sky_id: str) -> str:
    mod = create_mod_base_from_id(sky_id)
    return generate_download_url(mod.latest_revision)


def generate_download_url(revision: ModRevision):
    """
    Generate the download url of a given mod revision.

    Mods are hosted on file hosting services (i.e. modsbase.com or uploadfiles.eu), this method generate the download
    url from the service that hosts the mod.

    :param mod: Mod to download
    :return: The download url
    """
    mod_url = revision.download_url
    hostname = urlparse(mod_url).hostname

    if hostname not in SUPPORTED_HOSTS:
        raise UnsupportedHostError(f"{hostname} in not a supported hosting services")

    if hostname == "uploadfiles.eu":
        # if hosting service is uploadfiles.eu we have to follow two redirects
        scraper = cloudscraper.create_scraper()
        with scraper.get(mod_url, allow_redirects=False) as r:
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

    scraper = cloudscraper.create_scraper()
    with scraper.post(mod_url, data=data, allow_redirects=False) as r:
        r.raise_for_status()
        download_url = r.headers['Location']

    return download_url


def download_revision(download_url: str, download_path: str, progress_callback: Callable[[int, int], None] = None,
                      error_callback: Callable[[int, str], None] = None) -> Union[str, None]:
    """
    Tries to download a mod revision to a given download path. It tries to bypass cloudflare protection, but in case of
    failure, an error 403 will be raised from the error_callback. The progress_callback instead will be called when a
    new chunk of bytes has been downloaded successfully.
    download bytes.

    If file already exists the function will return immediately.

    :param download_url: ModRevision download url generated with generate_download_url function
    :param download_path: path where the zipped file will be downloaded
    :param progress_callback: callback of type (downloaded_bytes: int, total_bytes: int) -> None
    :param error_callback: callback of type (http_error_code, error_content)
    :return: The downloaded file path
    """
    url_parts = download_url.split('/')
    local_filename = url_parts[-1]

    download_target = os.path.join(os.path.abspath(download_path), local_filename)
    if os.path.exists(download_target):
        if progress_callback:
            size = os.path.getsize(download_target)
            progress_callback(size, size)

        return os.path.abspath(download_target)

    scraper = cloudscraper.create_scraper()

    # NOTE the stream=True parameter below
    with scraper.get(download_url, stream=True) as r:
        try:
            r.raise_for_status()
        except HTTPError as e:
            if error_callback:
                error_callback(r.status_code, str(e))

            return None

        total_length = r.headers.get('content-length')

        with open(download_target, 'wb') as f:
            dl = 0
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                dl += len(chunk)
                f.write(chunk)

                if total_length and progress_callback:
                    progress_callback(dl, int(total_length))

    return os.path.abspath(download_target)
