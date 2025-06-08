import schedule
import time
from store_weatherdata import fetch_and_store_weather_data
import logging

logging.info("Data collection is in progress...")

# Run the function every hour
schedule.every().hour.do(fetch_and_store_weather_data)

while True:
    schedule.run_pending()
    time.sleep(1)
    logging.debug("Scheduler is running pending jobs")
