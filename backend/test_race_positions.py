import requests
import json

def test_race_positions():
    # Test the race positions endpoint for the first race of 2025
    response = requests.get('http://localhost:8000/race/2025/1/positions')
    
    if response.status_code == 200:
        data = response.json()
        print("Success! Retrieved position data for the following drivers:")
        for driver, info in data.items():
            print(f"\nDriver: {info['driver_name']}")
            print(f"Team: {info['team']}")
            print(f"Number of laps: {len(info['positions'])}")
            print(f"First position: {info['positions'][0]}")
            print(f"Last position: {info['positions'][-1]}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_race_positions() 