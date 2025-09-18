import requests
import pycountry
import random
from django.shortcuts import render
from datetime import datetime

API_KEY = 'YOUR_API_KEY'
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Background images
day_backgrounds = {
    "Clear": "https://i.pinimg.com/1200x/2f/79/cd/2f79cd910b9a80a07f0e94cbb38a7440.jpg",  # use your image URLs
    "Clouds": "https://i.pinimg.com/736x/c5/f3/31/c5f331770f86cd888bd2277d78fc0d90.jpg",
    "Rain": "https://i.pinimg.com/736x/fe/c6/86/fec686553096d7262db90c25975d4965.jpg",
    "Drizzle": "https://i.pinimg.com/736x/54/ed/ac/54edac0188ed8a0e30f36d0e25ab4f04.jpg",
    "Thunderstorm": "https://i.pinimg.com/1200x/3b/85/d4/3b85d473fe137bdad1b28a9be3a91817.jpg",
    "Snow": "https://i.pinimg.com/1200x/67/c0/01/67c0016d8932ebde504343cc16444ef6.jpg",
    "Mist": "https://i.pinimg.com/1200x/fa/82/e5/fa82e5a8b9e70f6666d8662f9b096882.jpg",
    "Fog": "https://i.pinimg.com/1200x/54/83/c2/5483c2d56be01718639bd149bb4b62dd.jpg",
    "Haze": "https://i.pinimg.com/1200x/a9/56/68/a95668ab0c081745218e4cf10e70399e.jpg"
}

night_backgrounds = {
    "Clear": "https://i.pinimg.com/1200x/50/26/95/5026955249d1990dc42e012bab8535b9.jpg",  # use your night image URLs
    "Clouds": "https://i.pinimg.com/1200x/0f/79/db/0f79db315c0f9f2a54f7c4f3e869896d.jpg",
    "Rain": "https://i.pinimg.com/1200x/0d/b5/a8/0db5a8a64197aa3f8051e978c345be62.jpg",
    "Drizzle": "https://i.pinimg.com/736x/c5/2d/b5/c52db536696d6170c02118473e601131.jpg",
    "Thunderstorm": "https://i.pinimg.com/1200x/25/f8/95/25f895e691235db6c67a0b0ffb7dce5e.jpg",
    "Snow": "https://i.pinimg.com/736x/bf/5c/53/bf5c533a058bbe1c69f5c2829fc886c0.jpg",
    "Mist": "https://i.pinimg.com/1200x/5b/33/31/5b33316f4834b0aa6f567380c61bcd90.jpg",
    "Fog": "https://i.pinimg.com/736x/a4/4b/e5/a44be5449d39378206abe9d81bd51933.jpg",
    "Haze": "https://i.pinimg.com/736x/35/a9/e2/35a9e20cde9f8ef297804cc68c5cb7e9.jpg"
}

def get_weather_quote(description):
    quotes = {
        "clear": ["Sun’s out, fun’s out!"],
        "clouds": ["A cloudy day is no match for a sunny attitude!"],
        "rain": ["Don’t forget your umbrella!"],
        "thunderstorm": ["Thunder only happens when it’s raining!"],
        "snow": ["Let it snow, let it snow!"],
        "mist": ["A little fog to keep things mysterious!"],
    }
    key = description.lower()
    for condition, messages in quotes.items():
        if condition in key:
            return random.choice(messages)
    return "Weather is unpredictable—just like life!"

def get_country_name(code):
    country = pycountry.countries.get(alpha_2=code)
    return country.name if country else code

def format_unix_time(timestamp, offset):
    local_time = datetime.utcfromtimestamp(timestamp + offset)
    return local_time.strftime('%I:%M %p')

def index(request):
    weather_data = {}
    city = request.POST.get('city')

    if city:
        try:
            geo_res = requests.get(GEO_URL, params={'q': city, 'limit': 1, 'appid': API_KEY})
            geo_data = geo_res.json()

            if not geo_data:
                return render(request, 'index.html', {'weather_data': {'error': 'City not found'}})

            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
            city_name = geo_data[0]['name']

            weather_res = requests.get(WEATHER_URL, params={'lat': lat, 'lon': lon, 'units': 'metric', 'appid': API_KEY})
            weather_json = weather_res.json()

            if weather_json.get('cod') != 200:
                return render(request, 'index.html', {'weather_data': {'error': weather_json.get('message')}})

            forecast_res = requests.get(FORECAST_URL, params={'lat': lat, 'lon': lon, 'units': 'metric', 'appid': API_KEY})
            forecast_json = forecast_res.json()

            timezone_offset = weather_json['timezone']
            current_time = datetime.utcfromtimestamp(weather_json['dt'] + timezone_offset)
            sunrise_time = datetime.utcfromtimestamp(weather_json['sys']['sunrise'] + timezone_offset)
            sunset_time = datetime.utcfromtimestamp(weather_json['sys']['sunset'] + timezone_offset)
            is_day = sunrise_time <= current_time <= sunset_time

            condition_main = weather_json['weather'][0]['main']
            description = weather_json['weather'][0]['description']
            background_url = (
                day_backgrounds.get(condition_main, day_backgrounds["Clear"]) if is_day
                else night_backgrounds.get(condition_main, night_backgrounds["Clear"])
            )

            hourly_forecast = [
                {
                    'dt_txt': item['dt_txt'],
                    'temp': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                }
                for item in forecast_json.get('list', [])[:8]
            ]

            daily_forecast = [
                {
                    'date': item['dt_txt'].split()[0],
                    'temp': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                }
                for item in forecast_json.get('list', [])
                if item['dt_txt'].split()[1] == "12:00:00"
            ]

            weather_data = {
                'city': city_name,
                'country': get_country_name(weather_json['sys']['country']),
                'temperature': weather_json['main']['temp'],
                'pressure': weather_json['main']['pressure'],
                'humidity': weather_json['main']['humidity'],
                'description': description,
                'icon': weather_json['weather'][0]['icon'],
                'coord': {'lat': lat, 'lon': lon},
                'hourly_forecast': hourly_forecast,
                'daily_forecast': daily_forecast,
                'background_url': background_url,
                'quote': get_weather_quote(description),
                'sunrise': format_unix_time(weather_json['sys']['sunrise'], timezone_offset),
                'sunset': format_unix_time(weather_json['sys']['sunset'], timezone_offset),
                'local_time': current_time.strftime('%I:%M %p'),
                'is_day': is_day
            }

        except Exception as e:
            weather_data = {'error': f"Something went wrong: {str(e)}"}

    return render(request, 'index.html', {'weather_data': weather_data})

