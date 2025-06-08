🌧️ Gaborone Flood Alert System

This project is a small-scale, end-to-end data engineering pipeline designed to monitor real-time weather conditions in Gaborone, Botswana, provide flood alerts, and visualize key meteorological data through an interactive dashboard.

💡 Problem Statement

Gaborone, like many urban areas, is susceptible to localized flooding during heavy rainfall, especially in specific low-lying or poorly drained regions. Timely information on rainfall intensity and potential flood risk is crucial for public safety and preparedness. This system aims to address this by providing automated alerts and an easily accessible overview of the current flood status.

✨ Features

* **Automated Data Collection:** Regularly fetches real-time weather data for Gaborone from the OpenWeatherMap API.
* **Data Storage:** Persists collected and processed weather data in a local SQLite database (`alertGabs_rain_db`).
* **Intelligent Flood Alert Logic:**
    * Calculates hourly rainfall, 24-hour accumulated rainfall, and a "rainy streak" (consecutive days of significant rain).
    * Determines a multi-level flood alert (Level 0 - No risk to Level 3 - Severe Warning) based on defined Gaborone-specific thresholds for rainfall intensity and accumulation.
* **Email Notifications:** Sends automated email alerts for critical flood levels (Level 2 and 3) to a designated recipient.
* **Interactive Dashboard:** A Streamlit-based web application providing:
    * A table of recent weather records.
    * A clear display of the latest flood alert status.
    * A **dynamic line chart** visualizing rainfall trends over the last 7 recorded entries, with properly formatted date/time axes.
    * A Folium map highlighting key flood-prone areas in Gaborone, with marker colors indicating the latest alert level.
* **Robust Error Handling & Logging:** Implements specific error handling for API calls, database operations, and email sending, along with structured logging for better observability and debugging.
* **Configuration Management:** Utilizes `.env` files for secure handling of API keys and sensitive credentials.

## 🚀 Technologies Used

* **Python 3.x**
* **`requests`**: For making HTTP requests to external APIs.
* **`pandas`**: For data manipulation and analysis.
* **`sqlite3`**: For local relational database storage.
* **`streamlit`**: For building the interactive web dashboard.
* **`folium`**: For creating interactive maps.
* **`matplotlib`**: For generating data visualizations (rainfall trends).
* **`dotenv`**: For loading environment variables.
* **`smtplib`, `email.mime`**: For sending email alerts.
* **`schedule`**: For basic job scheduling (current implementation).

## 🛠️ How to Run the Project Locally

Follow these steps to set up and run the Gaborone Flood Alert System on your machine:

### 1. **Clone the Repository:**

```bash
git clone [https://github.com/](https://github.com/)[JorgeMatapuri]/[AlertGaborone].git
cd [AlertGaborone]