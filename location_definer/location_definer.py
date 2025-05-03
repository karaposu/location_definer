from abc import ABC, abstractmethod
from typing import List, Set, Optional

# stub mappings — replace with your real lookups
REGION_TO_COUNTRIES = {
    "Africa": [
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
        "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros",
        "Congo", "Côte d'Ivoire", "Democratic Republic of the Congo", "Djibouti",
        "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
        "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho", "Liberia",
        "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
        "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
        "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia",
        "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia",
        "Uganda", "Zambia", "Zimbabwe"
    ],
    "MiddleEast": [
        "Bahrain", "Cyprus", "Egypt", "Iran", "Iraq", "Israel", "Jordan",
        "Kuwait", "Lebanon", "Oman", "Palestine", "Qatar", "Saudi Arabia",
        "Syria", "Turkey", "United Arab Emirates", "Yemen"
    ],
    "Asia": [
        "Afghanistan", "Armenia", "Azerbaijan", "Bangladesh", "Bhutan", "Brunei",
        "Cambodia", "China", "Georgia", "India", "Indonesia", "Japan", "Kazakhstan",
        "Kyrgyzstan", "Laos", "Malaysia", "Maldives", "Mongolia", "Myanmar",
        "Nepal", "North Korea", "Pakistan", "Philippines", "Singapore",
        "South Korea", "Sri Lanka", "Taiwan", "Tajikistan", "Thailand",
        "Timor-Leste", "Turkmenistan", "Uzbekistan", "Vietnam"
    ],
    "Europe": [
        "Albania", "Andorra", "Austria", "Belarus", "Belgium",
        "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czech Republic", "Denmark",
        "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland",
        "Ireland", "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania",
        "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russia",
        "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden",
        "Switzerland", "Ukraine", "United Kingdom", "Vatican City"
    ],
    "NorthAmerica": [
        "Antigua and Barbuda", "Bahamas", "Barbados", "Belize", "Canada",
        "Costa Rica", "Cuba", "Dominica", "Dominican Republic", "El Salvador",
        "Grenada", "Guatemala", "Haiti", "Honduras", "Jamaica", "Mexico",
        "Nicaragua", "Panama", "Saint Kitts and Nevis", "Saint Lucia",
        "Saint Vincent and the Grenadines", "Trinidad and Tobago", "United States"
    ],
    "SouthAmerica": [
        "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador",
        "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela"
    ],
    "Oceania": [
        "Australia", "Fiji", "Kiribati", "Marshall Islands", "Micronesia",
        "Nauru", "New Zealand", "Palau", "Papua New Guinea", "Samoa",
        "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu"
    ]
}


# pip install geonamescache

import geonamescache

gc = geonamescache.GeonamesCache()

# Get a dict of all countries by ISO2 code
countries = gc.get_countries()  # e.g. {'TR': {'name': 'Turkey', ...}, ...}

# Get a dict of all cities keyed by city ID, including their country codes
cities = gc.get_cities()  # e.g. {'379252': {'name': 'Istanbul', 'countrycode': 'TR', ...}, ...}

# Build COUNTRY_TO_CITIES mapping
COUNTRY_TO_CITIES = {}
for country_iso, cinfo in countries.items():
    country_name = cinfo['name']
    # Collect all cities whose countrycode matches this ISO
    city_list = [
        city['name'] for city in cities.values()
        if city['countrycode'] == country_iso
    ]
    # Optionally: sort, dedupe, and take only the top N largest cities, etc.
    COUNTRY_TO_CITIES[country_name] = sorted(set(city_list))

# Example output snippet
# print({k: COUNTRY_TO_CITIES[k][:5] for k in ['Turkey', 'Belarus', 'France', 'Germany', 'Japan']})
# {
#   'Turkey': ['Adana', 'Afyonkarahisar', 'Ağrı', 'Amasya', 'Ankara'],
#   'Belarus': ['Barysaw', 'Brest', 'Gomel', 'Grodno', 'Minsk'],
#   ...
# }





# COUNTRY_TO_CITIES = {
#     "Turkey":  ["Istanbul", "Ankara", "Izmir"],
#     "Belarus": ["Minsk", "Brest", "Grodno"],
#     "France":  ["Paris", "Lyon", "Marseille"],
#     "Germany": ["Berlin", "Munich", "Frankfurt"],
#     "Japan":   ["Tokyo", "Osaka"],
#     # …
# }


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


class LocationDefiner:
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
