from .location_definer import Region, City,Country, LocationFilter

# 1) Define regions with exceptions
europe = Region("Europe")
europe.add_exception(Country("Belarus"))  # drop entire country
europe.add_exception(City("Minsk"))       # drop one city

asia = Region("Asia")
asia.add_exception(City("Tokyo"))

# 2) Define a standalone country-level inclusion
turkey = Country("Turkey")
turkey.add_exception(City("Izmir"))  # e.g. exclude one city if needed

# 3) Maybe an explicit city inclusion
ny = City("New York")

# 4) Build your filter
loc_filter = LocationFilter(
    regions=[europe, asia],
    countries=[turkey],
    cities=[ny]
)

# 5) Compile to a flat set of cities
cities = loc_filter.compile_cities()
# cities now contains:
#   all European & Asian cities (minus Belarus/Minsk/Tokyo),
#   plus Turkish cities (minus Izmir), plus New York.
