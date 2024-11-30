from datetime import datetime
import requests


def is_valid_date(date_str, date_format='%d.%m.%Y'):
    try:
        # Try to parse the input string into a datetime object
        datetime.strptime(date_str, date_format)
        return True  # The date is valid
    except ValueError:
        return False  # The date is invalid


from geopy.geocoders import Nominatim


def get_location(latitude, longitude):
    geolocator = Nominatim(user_agent="coordinateconverter")
    address = f'{latitude}, {longitude}'
    location = geolocator.reverse(address)
    city = location.raw['address'].get('city', None)
    if not city:
        city = location.raw['address'].get('town', None) or location.raw['address'].get('village', None)
    return city


import json


class JsonController:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_from_json(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            print(f"Data read from {self.file_path}.")
            return data
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
            return None
        except json.JSONDecodeError:
            print(f"Failed to decode JSON in {self.file_path}.")
            return None


    def edit_json(self, key, value):
        data = self.read_from_json()
        for i in data:
            if i == str(key):
                print("Already exists")
                return "Already exists"
        try:
            data = self.read_from_json()

            if not isinstance(data, dict):
                print("JSON data is not a dictionary; cannot edit.")
                return

            # Ensure the key is a string (JSON keys must be strings)
            if isinstance(key, (str, int)):
                key = str(key)
            else:
                print(f"Key must be a string or integer, but got {type(key).__name__}.")
                return

            # Add or update the key-value pair
            data[key] = value

            # Write the updated data back to the JSON file
            with open(self.file_path, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"Successfully updated key '{key}' in {self.file_path}.")

        except IOError as e:
            print(f"Failed to edit JSON file {self.file_path}: {e}")


def get_prayer_times(latitude, longitude, method=2):
    """
    Fetch prayer times for a given location using Aladhan API.

    :param latitude: Latitude of the location (float).
    :param longitude: Longitude of the location (float).
    :param method: Calculation method (default=2 for Islamic Society of North America).
    :return: Dictionary containing prayer times or error message.
    """
    url = "https://api.aladhan.com/v1/timings"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "method": method  # Calculation method, default=2
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data["data"]["timings"]
        else:
            return {"error": f"Failed to fetch prayer times. Status code: {response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"An error occurred: {e}"}

def get_user_data():
    controller = JsonController('data.json')
    return controller.read_from_json()


import requests
from datetime import datetime, timedelta


def get_prayer_times_for_next_7_days(latitude, longitude, method=2):
    """
    Fetch prayer times for the next 7 days for a given location using Aladhan API.

    :param latitude: Latitude of the location (float).
    :param longitude: Longitude of the location (float).
    :param method: Calculation method (default=2 for Islamic Society of North America).
    :return: Dictionary containing prayer times for the next 7 days or an error message.
    """
    # Get current date
    today = datetime.now()
    month = today.month
    year = today.year

    # API endpoint for the calendar
    url = "https://api.aladhan.com/v1/calendar"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "method": method,
        "month": month,
        "year": year
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" not in data:
                return {"error": "Unexpected API response format"}

            # Extract prayer times for the next 7 days
            next_7_days = {}
            for i in range(7):
                target_date = today + timedelta(days=i)
                day_data = data["data"][target_date.day - 1]  # Subtract 1 because API uses 1-based index
                next_7_days[target_date.strftime("%Y-%m-%d")] = day_data["timings"]
            return next_7_days
        else:
            return {"error": f"Failed to fetch prayer times. Status code: {response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"An error occurred: {e}"}
