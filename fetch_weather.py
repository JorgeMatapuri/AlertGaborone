import requests  # Makes the web request
import os        # Access environment variables
from dotenv import load_dotenv  # Load the .env file

load_dotenv(dotenv_path='config/.env')  # Read the .env file into Python

API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Get API key from .env
CITY = "Sassandra"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

response = requests.get(URL)  # Send GET request
data = response.json()        # Convert to Python dictionary

print("✅ Weather data:")
print(data)                   # Show the result
