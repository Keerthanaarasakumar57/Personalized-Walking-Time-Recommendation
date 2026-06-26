import requests

def get_weather(city):

    API_KEY = "0915a79bfc91679762000313910074e6"

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        return temp, humidity

    except Exception as e :
        print("Weather error:", e)
        return 30, 60   # Default fallback
