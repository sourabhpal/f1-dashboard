import fastf1

fastf1.Cache.enable_cache('/Users/sourabhpal/Downloads/F1 Dashboard/cache')  # Set full path

race = fastf1.get_event(2025, 3)
print(f"Race Name: {race['EventName']}")
print(f"Location: {race['Location']} on {race['Session1Date']}")