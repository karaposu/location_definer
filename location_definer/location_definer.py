from abc import ABC, abstractmethod
from typing import List, Set, Optional

# stub mappings — replace with your real lookups
REGION_TO_COUNTRIES = {
    "Europe": ["Turkey", "Belarus", "France", "Germany"],
    "Asia":   ["Japan", "China", "India"],
}
COUNTRY_TO_CITIES = {
    "Turkey":  ["Istanbul", "Ankara", "Izmir"],
    "Belarus": ["Minsk", "Brest", "Grodno"],
    "France":  ["Paris", "Lyon", "Marseille"],
    "Germany": ["Berlin", "Munich", "Frankfurt"],
    "Japan":   ["Tokyo", "Osaka"],
    # …
}


class Location(ABC):
    def __init__(self, name: str):
        self.name = name
        self.exceptions: List["Location"] = []

    def add_exception(self, loc: "Location"):
        """Exclude this subordinate location."""
        self.exceptions.append(loc)

    @abstractmethod
    def compile_into_cities(self) -> Set[str]:
        """Return the flat set of city names this Location represents."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name!r}>"


class City(Location):
    def compile_into_cities(self) -> Set[str]:
        # If this city is explicitly excepted, return empty set
        if any(isinstance(exc, City) and exc.name == self.name for exc in self.exceptions):
            return set()
        return {self.name}


class Country(Location):
    def compile_into_cities(self) -> Set[str]:
        cities = set(COUNTRY_TO_CITIES.get(self.name, []))
        # remove any city-level exceptions
        excluded = {exc.name for exc in self.exceptions if isinstance(exc, City)}
        return cities - excluded


class Region(Location):
    def compile_into_cities(self) -> Set[str]:
        # 1) Expand region → countries → cities
        cities: Set[str] = set()
        for country in REGION_TO_COUNTRIES.get(self.name, []):
            # skip a whole-country exception
            if any(isinstance(exc, Country) and exc.name == country for exc in self.exceptions):
                continue
            # otherwise add that country’s cities
            cities.update(COUNTRY_TO_CITIES.get(country, []))

        # 2) remove city-level exceptions
        city_excs = {exc.name for exc in self.exceptions if isinstance(exc, City)}
        cities -= city_excs

        # 3) remove any region‐level exceptions
        for exc in self.exceptions:
            if isinstance(exc, Region):
                cities -= exc.compile_into_cities()

        return cities


class LocationFilter:
    """
    Holds your top-level geography spec:
      - regions
      - countries
      - cities
    Each entry can have its own exceptions.
    """
    def __init__(self,
                 regions: Optional[List[Region]]  = None,
                 countries: Optional[List[Country]] = None,
                 cities: Optional[List[City]]     = None):
        self.regions  = regions  or []
        self.countries = countries or []
        self.cities    = cities    or []

    def compile_cities(self) -> Set[str]:
        result: Set[str] = set()
        # gather from regions
        for r in self.regions:
            result |= r.compile_into_cities()
        # gather from countries
        for c in self.countries:
            result |= c.compile_into_cities()
        # gather from individual cities
        for c in self.cities:
            result |= c.compile_into_cities()
        return result

    def __repr__(self):
        parts = []
        if self.regions:  parts.append(f"Regions={self.regions}")
        if self.countries: parts.append(f"Countries={self.countries}")
        if self.cities:    parts.append(f"Cities={self.cities}")
        return "<LocationFilter " + "; ".join(parts) + ">"
