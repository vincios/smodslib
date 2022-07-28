import hashlib
from datetime import datetime
from typing import TypedDict, Union

from .utils import StrEnum


class ModRevision(object):
    @classmethod
    def hash(cls, string: str):
        return hashlib.md5(string.encode('utf-8'), usedforsecurity=False).hexdigest()[:10]

    @property
    def id(self) -> str:
        return ModRevision.hash(self.name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def download_url(self) -> str:
        return self._download_url

    @property
    def filename(self) -> str:
        return self.download_url.split("/")[-1].replace(".html", "").strip()

    def __init__(self, name: str, date: datetime, url: str) -> None:
        self._name = name
        self._date = date
        self._download_url = url

    def __repr__(self):
        return f"{self.id} | {self.name} | {self.filename} | {self.download_url}"


class ModBase(object):
    """
    Base version of a mod object, containing only the essentials mod information
    """

    @classmethod
    def from_mod(cls, mod):
        """
        Create a new ModBase instance starting from another Mod object. Only the ModBase properties will be copied

        :param mod:
        :return:
        """
        return cls(mod.name, mod.id, mod.steam_id, mod.authors, mod.size, mod.published_date,
                   mod.has_dependencies, mod.latest_revision, mod.category)

    @property
    def name(self) -> str:
        """ Mod name """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def id(self) -> str:
        """ Skymod id """
        return self._id

    @id.setter
    def id(self, value: Union[str, int]):
        self._id = str(value)

    @property
    def steam_id(self) -> str:
        """ Steam id"""
        return self._steam_id

    @steam_id.setter
    def steam_id(self, value: Union[str, int]):
        self._steam_id = str(value)

    @property
    def authors(self) -> Union[str, list[str]]:
        """ Mod authors list"""
        return self._authors

    @authors.setter
    def authors(self, value: Union[str, list[str]]):
        self._authors = value

    @property
    def published_date(self) -> datetime:
        """ Mod publishing date """
        return self._published_date

    @published_date.setter
    def published_date(self, value: datetime):
        """ Mod publishing date """
        self._published_date = value

    @property
    def size(self) -> str:
        """ Mod size"""
        return self._size

    @size.setter
    def size(self, value: str):
        self._size = value

    @property
    def has_dependencies(self) -> bool:
        """ Whether the mod has dependencies to download or not """
        return self._has_dependencies

    @has_dependencies.setter
    def has_dependencies(self, value: bool):
        self._has_dependencies = value

    @property
    def latest_revision(self) -> ModRevision:
        """ Mod latest revision download """
        return self._latest_revision

    @latest_revision.setter
    def latest_revision(self, value: ModRevision):
        self._latest_revision = value

    @property
    def category(self) -> str:
        """ Mod category """
        return self._category

    @category.setter
    def category(self, value: str):
        self._category = value

    @property
    def steam_url(self) -> str:
        return f"https://steamcommunity.com/workshop/filedetails/?id={self.steam_id}"

    @property
    def url(self) -> str:
        return f"https://smods.ru/archives/{self.id}"

    def __init__(self, name: str, sky_id: Union[str, int], steam_id: Union[str, int], authors: Union[str, list[str]],
                 size: str, published_date: datetime, has_dependencies: bool, latest_revision: ModRevision,
                 category: str) -> None:
        self.name = name
        self.id = sky_id
        self.steam_id = steam_id
        self.authors = authors
        self.has_dependencies = has_dependencies
        self.latest_revision = latest_revision
        self.published_date = published_date
        self.size = size
        self.category = category

    def __str__(self) -> str:
        return f"{self.id} | {self.name} [{self.category}]"

    def __repr__(self) -> str:
        return f"{self.id} | {self.name} [{self.category}]"


class ModDependency(ModBase):
    """
    Representation of a (base mod) with additional information about other Mods that requires it
    """

    @classmethod
    def from_mod(cls, mod):
        """
        Create a new ModDependency instance starting from another Mod object. Only the ModBase properties will be copied

        :param mod:
        :return:
        """
        return cls(mod.name, mod.id, mod.steam_id, mod.authors, mod.size, mod.published_date,
                   mod.has_dependencies, mod.latest_revision, mod.category)

    @property
    def required_by(self) -> list[ModBase]:
        return self._required_by

    @required_by.setter
    def required_by(self, value: list[ModBase]):
        self._required_by = value

    def __init__(self, name: str, sky_id: Union[str, int], steam_id: Union[str, int], authors: Union[str, list[str]],
                 size: str, published_date: datetime, has_dependencies: bool, latest_revision: ModRevision,
                 category: str) -> None:
        super().__init__(name, sky_id, steam_id, authors, size, published_date, has_dependencies,
                         latest_revision, category)
        self.required_by = []


class FullMod(ModBase):
    """
    Representation of a Mod with all the information there are into its html page
    """

    @classmethod
    def from_mod(cls, mod):
        """
        Create a new FullMod instance starting from another Mod object. Only the ModBase properties will be copied

        :param mod:
        :return:
        """
        return cls(mod.name, mod.id, mod.steam_id, mod.authors, mod.size, mod.published_date,
                   mod.has_dependencies, mod.latest_revision, mod.category)

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def plain_description(self) -> str:
        return self._plain_description

    @plain_description.setter
    def plain_description(self, value: str):
        self._plain_description = value

    @property
    def updated_date(self) -> datetime:
        return self._updated_date

    @updated_date.setter
    def updated_date(self, value: datetime):
        self._updated_date = value

    @property
    def dlc_requirements(self) -> list[str]:
        return self._dlc_requirements

    @dlc_requirements.setter
    def dlc_requirements(self, value: list[str]):
        self._dlc_requirements = value

    @property
    def mod_requirements(self) -> list[ModBase]:
        return self._mod_requirements

    @mod_requirements.setter
    def mod_requirements(self, value: list[ModBase]):
        self._mod_requirements = value

    @property
    def other_revisions(self) -> list[ModRevision]:
        return self._revisions

    @other_revisions.setter
    def other_revisions(self, value: list[ModRevision]):
        if value:
            sorted(value, key=lambda item: item.date)

        self._revisions = value

    @property
    def tags(self) -> list[str]:
        return self._tags

    @tags.setter
    def tags(self, value: list[str]):
        self._tags = value

    @property
    def image_url(self) -> str:
        """ Mod image url """
        return self._image_url

    @image_url.setter
    def image_url(self, value: str):
        self._image_url = value

    @property
    def rating(self) -> int:
        return self._rating

    @rating.setter
    def rating(self, value: bool):
        self._rating = value

    def __init__(self, name: str, sky_id: Union[str, int], steam_id: Union[str, int], authors: Union[str, list[str]],
                 size: str, published_date: datetime, has_dependencies: bool, latest_revision: ModRevision,
                 category: str, description: str = None, plain_description: str = None,
                 updated_date: datetime = None, dlc_requirements: list[str] = None,
                 mod_requirements: list[ModBase] = None, other_revisions: list[ModRevision] = None,
                 tags: list[str] = None, image_url: str = None, rating: int = None) -> None:
        super().__init__(name, sky_id, steam_id, authors, size, published_date, has_dependencies,
                         latest_revision, category)
        self.description = description
        self.plain_description = plain_description
        self.updated_date = updated_date
        self.dlc_requirements = dlc_requirements
        self.mod_requirements = mod_requirements
        self.other_revisions = other_revisions
        self.tags = tags
        self.image_url = image_url
        self.rating = rating


# CATALOGUE SECTION

class SortByFilter(StrEnum):
    """
    Methods to sort a catalogue.
        - Date uploaded (UPLOADED): Sort by date uploaded descending.
        - Date Updated (UPDATED): Sort by date updated descending. New items are excluded.
        - Highest Rated (HIGHEST_RATED): Sort by rating descending.
        - Unrated (UNRATED): Items that don't have enough votes.
        - Smallest File Size (SMALLEST_FILE_SIZE): Sort by original archive size ascending.
        - Largest File Size (LARGEST_FILE_SIZE): Sort by original archive size descending.

    """
    UPLOADED = ""
    UPDATED = "updated"
    HIGHEST_RATED = "highest-rated"
    UNRATED = "unrated"
    SMALLEST_FILE_SIZE = "smallest-file-size"
    LARGEST_FILE_SIZE = "largest-file-size"


class TimePeriodFilter(StrEnum):
    """
    Filters the catalogue items by time period.
        - All Time (ALL_TIME)
        - Last Day (ONE_DAY)
        - Last Three Days (THREE_DAYS)
        - Last Week (ONE_WEEK)
        - Last Two Weeks (TWO_WEEKS)
        - Last Month (ONE_MONTH)
        - Last Six Months (SIX_MONTHS)
        - Last Year (ONE_YEAR)
    """
    ALL_TIME = ""
    ONE_DAY = "one_day"
    THREE_DAYS = "three_days"
    ONE_WEEK = "one_week"
    TWO_WEEKS = "two_weeks"
    ONE_MONTH = "one_month"
    SIX_MONTHS = "six_months"
    ONE_YEAR = "one_year"


class CatalogueParameters(TypedDict, total=False):
    """
    Allowed filtering parameters
    """
    sort: SortByFilter
    period: TimePeriodFilter


class ModCatalogueItem(ModBase):
    """
    Representation of a mod in a catalogue page.

    A catalogue page is any Skymod page where multiple mods are listed (a search page, a category page, etc.)
    """

    @classmethod
    def from_mod(cls, mod):
        """
        Create a new FullMod instance starting from another Mod object. Only the ModBase properties will be copied

        :param mod:
        :return:
        """
        return cls(mod.name, mod.id, mod.steam_id, mod.authors, mod.size, mod.published_date,
                   mod.has_dependencies, mod.latest_revision, mod.category)

    @property
    def image_url(self) -> str:
        """ Mod image url """
        return self._image_url

    @image_url.setter
    def image_url(self, value: str):
        self._image_url = value

    @property
    def rating(self) -> int:
        return self._rating

    @rating.setter
    def rating(self, value: bool):
        self._rating = value

    def __init__(self, name: str, sky_id: Union[str, int], steam_id: Union[str, int], authors: Union[str, list[str]], size: str,
                 published_date: datetime, has_dependencies: bool, latest_revision: ModRevision,
                 category: str, image_url: str = None, rating: int = None) -> None:
        super().__init__(name, sky_id, steam_id, authors, size, published_date, has_dependencies,
                         latest_revision, category)
        self.image_url = image_url
        self.rating = rating
