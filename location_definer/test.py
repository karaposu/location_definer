from .location_definer import Region, City,Country, LocationDefiner

#python -m location_definer.test

# 1) Define regions with exceptions
# europe = Region("Europe")
# europe.add_exception(Country("Belarus")) 
turkey = Country("Turkey")
# tokyo =City("Tokyo")  
# ny = City("New York")


# 4) Build your filter
loc_definer = LocationDefiner(
    countries=[turkey],
)

# loc_definer = LocationDefiner(
#     regions=[europe],
#     countries=[turkey],
#     cities=[ny]
# )

# 5) Compile to a flat set of cities
cities = loc_definer.compile_cities()

print(cities)
