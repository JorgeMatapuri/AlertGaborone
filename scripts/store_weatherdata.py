import requests
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone # Import timezone for the new utcfromtimestamp method
import logging
import time

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- END NEW ---

# Load environment variables
load_dotenv(dotenv_path='config/.env')

API_KEY = os.getenv('OPENWEATHER_API_KEY')
CITY = 'Gaborone'
# --- Configuration Validation: Check API Key immediately ---
if not API_KEY:
    logging.critical("❌ OPENWEATHER_API_KEY environment variable is not set. Exiting.")
    exit(1) # Exit the script if critical configuration is missing

URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# --- Gaborone-specific rainfall constants (in mm) ---
GABS_FLASH_FLOOD_HOURLY_ADVISORY = 3
GABS_FLASH_FLOOD_HOURLY_WATCH = 8
GABS_FLASH_FLOOD_HOURLY_WARNING = 15

GABS_DAILY_RAINFALL_ADVISORY = 15
GABS_DAILY_RAINFALL_WATCH = 20
GABS_DAILY_RAINFALL_WARNING = 40

MIN_SIGNIFICANT_DAILY_RAINFALL_MM = 10
# --- END NEW ---

# --- NEW: Retry Constants ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
# --- END NEW ---


def get_flood_alert_level(current_hourly_rain_mm, daily_total_rain_mm, streak=0):
    """
    Determines the flood alert level for Gaborone based on hourly rainfall intensity,
    24-hour accumulated rainfall, and consecutive days of significant rain.
    """
    if current_hourly_rain_mm >= GABS_FLASH_FLOOD_HOURLY_WARNING or \
       daily_total_rain_mm >= GABS_DAILY_RAINFALL_WARNING or \
       streak >= 4:
        return "Level 3 - WARNING: Severe risk of flooding - Immediate action required."
    elif current_hourly_rain_mm >= GABS_FLASH_FLOOD_HOURLY_WATCH or \
         daily_total_rain_mm >= GABS_DAILY_RAINFALL_WATCH or \
         streak >= 2:
        return "Level 2 - WATCH: Moderate to high flood risk - Prepare for action."
    elif current_hourly_rain_mm >= GABS_FLASH_FLOOD_HOURLY_ADVISORY or \
         daily_total_rain_mm >= GABS_DAILY_RAINFALL_ADVISORY or \
         streak >= 1:
        return "Level 1 - ADVISORY: Possible localized flooding - Stay vigilant."
    else:
        return "Level 0 - No flood risk"


def send_email_alert(alert_msg):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = "projectjorgem@gmail.com" # <-- Replace with your real email for testing

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = "🚨 Flood Alert Notification"

    body = f"Attention:\n\n{alert_msg}\n\nPlease take necessary precautions."
    msg.attach(MIMEText(body, 'plain'))

    try:
        # --- Configuration Validation for Email ---
        email_host = os.getenv("EMAIL_HOST")
        email_port_str = os.getenv("EMAIL_PORT")

        if not all([sender, password, email_host, email_port_str]):
            logging.error("❌ Email configuration (EMAIL_USER, EMAIL_PASSWORD, EMAIL_HOST, EMAIL_PORT) is incomplete. Skipping email alert.")
            return

        try:
            email_port = int(email_port_str)
        except ValueError:
            logging.error(f"❌ Invalid SMTP port number configured: '{email_port_str}'. Must be an integer. Skipping email alert.")
            return

        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        logging.info("✅ Email alert sent.")
    except smtplib.SMTPException as e:
        logging.error(f"❌ Failed to send email (SMTP error): {e}", exc_info=True)
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred while sending email: {e}", exc_info=True)


def get_daily_total_rainfall(current_timestamp_dt):
    """
    Calculates the total rainfall (in mm) in the last 24 hours from the database.
    Assumes 'timestamp' in DB is in 'YYYY/MM/DD,HH:MM:SS' format and 'rainfall' is 'rain.1h'.
    """
    conn = None
    try:
        conn = sqlite3.connect("alertGabs_rain_db")
        cursor = conn.cursor()

        twenty_four_hours_ago = current_timestamp_dt - timedelta(hours=24)
        twenty_four_hours_ago_str = twenty_four_hours_ago.strftime('%Y/%m/%d,%H:%M:%S')

        cursor.execute("""
            SELECT SUM(rainfall)
            FROM weather
            WHERE timestamp > ?
        """, (twenty_four_hours_ago_str,))
        
        total_rain_24h = cursor.fetchone()[0]
        return total_rain_24h if total_rain_24h is not None else 0
    except sqlite3.Error as e:
        logging.error(f"❌ Database error calculating daily total rainfall: {e}", exc_info=True)
        return 0
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred in get_daily_total_rainfall: {e}", exc_info=True)
        return 0
    finally:
        if conn:
            conn.close()


def fetch_weather_data():
    for attempt in range(MAX_RETRIES):
        try:
            # --- FIX: DeprecationWarning here ---
            # Use datetime.fromtimestamp with timezone.utc
            response = requests.get(URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            rain_1h = data.get("rain", {}).get("1h", 0)
            if rain_1h < 0:
                logging.warning(f"Received negative rainfall value: {rain_1h} mm. Treating as 0.")
                rain_1h = 0
            
            # --- UPDATED LINE for DeprecationWarning ---
            current_timestamp_dt = datetime.fromtimestamp(data['dt'], timezone.utc) 
            # If you want it to be timezone-naive for comparison with SQLite, convert to naive:
            current_timestamp_dt_naive = current_timestamp_dt.replace(tzinfo=None)
            timestamp = current_timestamp_dt_naive.strftime('%Y/%m/%d,%H:%M:%S') # Use naive for strftime

            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]

            daily_total_rain_mm = get_daily_total_rainfall(current_timestamp_dt_naive) # Pass naive datetime
            streak = get_rainy_streak()
            
            flood_alert = get_flood_alert_level(rain_1h, daily_total_rain_mm, streak)

            logging.info(f"Extracted: Time: {timestamp}, Temp: {temp}, Humidity: {humidity}, Rain (1h): {rain_1h} mm")
            logging.info(f"Daily Total Rain (24h): {daily_total_rain_mm} mm")
            logging.info(f"Rainy Streak (significant days): {streak} consecutive day(s)")
            logging.info(f"Flood Alert: {flood_alert}")

            return {
                "city": CITY,
                "timestamp": timestamp,
                "temperature": temp,
                "humidity": humidity,
                "rainfall": rain_1h,
                "flood_alert": flood_alert,
                "rain_streak": streak
            }
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logging.warning(f"⚠️ API connection/timeout error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logging.error(f"❌ Failed to fetch weather data after {MAX_RETRIES} attempts due to connection/timeout errors. Last error: {e}", exc_info=True)
                return None
        except requests.exceptions.HTTPError as e:
            logging.error(f"❌ HTTP error fetching weather data: {e} - Status Code: {e.response.status_code}. Not retrying permanent error.", exc_info=True)
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ An unhandled requests error occurred: {e}", exc_info=True)
            return None
        except ValueError as e:
            logging.error(f"❌ Error decoding JSON response from API or invalid data: {e}. Raw response might be invalid.", exc_info=True)
            return None
        except KeyError as e:
            logging.error(f"❌ Missing expected key in API response: {e}. Data structure might have changed. Full data: {data}", exc_info=True)
            return None
        except Exception as e:
            logging.error(f"❌ An unexpected error occurred during data fetching: {e}", exc_info=True)
            return None
    return None


def save_to_db(weather):
    if weather is None:
        logging.warning("Skipping database save as no valid weather data was provided.")
        return

    conn = None
    try:
        conn = sqlite3.connect("alertGabs_rain_db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                timestamp TEXT,
                temperature REAL,
                humidity INTEGER,
                rainfall REAL,
                flood_alert TEXT,
                rain_streak INTEGER
            )
        """)

        cursor.execute("""
            INSERT INTO weather(city, timestamp, temperature, humidity, rainfall, flood_alert, rain_streak)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (weather["city"], weather["timestamp"], weather["temperature"],
              weather["humidity"], weather["rainfall"], weather["flood_alert"], weather["rain_streak"]))

        conn.commit()
        logging.info("✅ Data saved into DB.")
    except sqlite3.Error as e:
        logging.error(f"❌ Database error saving data: {e}", exc_info=True)
        if conn:
            conn.rollback()
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred during database save: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


def get_rainy_streak():
    """
    Calculates the number of consecutive days with 'significant' rainfall.
    A day is considered 'significant' if its total rainfall is >= MIN_SIGNIFICANT_DAILY_RAINFALL_MM.
    """
    conn = None
    try:
        conn = sqlite3.connect("alertGabs_rain_db")
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT DATE(REPLACE(REPLACE(timestamp, '/', '-'), ',', ' ')), SUM(rainfall)
            FROM weather
            GROUP BY DATE(REPLACE(REPLACE(timestamp, '/', '-'), ',', ' '))
            ORDER BY DATE(REPLACE(REPLACE(timestamp, '/', '-'), ',', ' ')) DESC
            LIMIT 7
        """)
        daily_rainfall_records = cursor.fetchall()
        
        streak = 0
        if not daily_rainfall_records:
            return 0

        # --- FIX: Removed .replace(tzinfo=None) from date objects ---
        # datetime.strptime(date_str, '%Y-%m-%d').date() already returns a timezone-naive date object
        current_date = datetime.strptime(daily_rainfall_records[0][0], '%Y-%m-%d').date()

        for i, (date_str, daily_total_rain) in enumerate(daily_rainfall_records):
            # --- FIX: Removed .replace(tzinfo=None) here as well ---
            record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            expected_date = (current_date - timedelta(days=i))

            if record_date == expected_date and daily_total_rain >= MIN_SIGNIFICANT_DAILY_RAINFALL_MM:
                streak += 1
                # The 'current_date' in this loop implicitly handles moving to the previous day
                # No longer decrementing current_date in the loop, as `expected_date` uses `i` for offset
                # This ensures comparison is always against the correct consecutive date based on initial `current_date`
            else:
                if record_date < expected_date:
                    # If we encounter a record date that is earlier than the expected date (meaning a gap), break the streak
                    break
                # If record_date > expected_date (meaning data out of order or duplicate date entries), continue to next record
        return streak
    except sqlite3.Error as e:
        logging.error(f"❌ Database error calculating rainy streak: {e}", exc_info=True)
        return 0
    except ValueError as e:
        logging.error(f"❌ Date parsing error in get_rainy_streak. Check DB timestamp format: {e}", exc_info=True)
        return 0
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred during rainy streak calculation: {e}", exc_info=True)
        return 0
    finally:
        if conn:
            conn.close()


def fetch_and_store_weather_data():
    logging.info("Starting weather data fetch and store process.")
    weather = fetch_weather_data()
    if weather:
        save_to_db(weather)

        if "Level 2" in weather["flood_alert"] or "Level 3" in weather["flood_alert"]:
            logging.info(f"Flood alert triggered: {weather['flood_alert']}")
            send_email_alert(weather["flood_alert"])
    else:
        logging.warning("Weather data fetch failed. Skipping save and alert check.")

# Run if script is executed directly
if __name__ == "__main__":
    fetch_and_store_weather_data()