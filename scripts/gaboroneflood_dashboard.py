import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker # Crucial: Make sure this is imported

st.set_page_config(page_title="Flood Alert Dashboard", layout="wide")

# --- Custom CSS for background color (Light Blue: #ADD8E6) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #ADD8E6;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- END Custom CSS ---

st.title("🌧️ Gaborone Flood Alert Dashboard")

# Connect to SQLite and load data
conn = sqlite3.connect("alertGabs_rain_db")
df = pd.read_sql_query("SELECT * FROM weather ORDER BY timestamp ASC", conn)
conn.close()

# Convert timestamp to datetime objects for plotting and easier manipulation.
df['timestamp_dt'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d,%H:%M:%S')

# --- Visualization for the last seven entries ---
chart_df = df.tail(7)

# --- Display Recent Weather Records in a Table ---
st.subheader("Recent Weather Records")
st.dataframe(df.tail(7).drop(columns=['timestamp_dt']))

# --- Display Latest Flood Alert ---
st.subheader("🚨 Latest Alert")
if not df.empty:
    latest = df.iloc[-1]
    st.markdown(f"""
    **City**: {latest['city']}  
    **Time**: {latest['timestamp']}  
    **Rainfall (last 1h)**: {latest['rainfall']} mm  
    **Streak (significant rain)**: {latest['rain_streak']} days  
    **Flood Alert**: {latest['flood_alert']}  
    """)
else:
    st.info("No weather data available yet. Please run the data collection script to populate data.")

# --- Rainfall Trends Chart Section (Showing Last 7 Entries) ---
st.subheader("📊 Rainfall Trends (Last 7 Entries)")
if not chart_df.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Convert datetime objects to Matplotlib's internal numeric format for plotting
    x_values_numeric = mdates.date2num(chart_df['timestamp_dt'])
    
    ax.plot(x_values_numeric, chart_df['rainfall'], marker='o', linestyle='-', color='skyblue')

    ax.set_xlabel("Time")
    ax.set_ylabel("Rainfall (mm)")
    ax.set_title("Hourly Rainfall Over Time")
    ax.grid(True)
    
    # --- FIX START ---
    # Set major ticks to be exactly at each data point's timestamp
    # Now correctly using mticker.FixedLocator and mticker.AutoLocator
    if len(chart_df) <= 7:
        # FixedLocator expects numeric values for plotting if you're passing numeric to ax.plot
        # So convert chart_df['timestamp_dt'] to numeric dates for FixedLocator
        ax.xaxis.set_major_locator(mticker.FixedLocator(mdates.date2num(chart_df['timestamp_dt']))) # CORRECTED: Changed mdates.FixedLocator to mticker.FixedLocator
    else:
        ax.xaxis.set_major_locator(mticker.AutoLocator())

    ax.xaxis.set_tick_params(rotation=45) 
    
    # Use a formatter that includes both date and time
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    fig.autofmt_xdate() 
    # --- FIX END ---
    
    st.pyplot(fig)
else:
    st.info("Not enough data to display rainfall trends yet. Collect more data to see trends.")
# --- END Rainfall Trends Chart Section ---


# --- Map section (existing code) ---
st.subheader("🗺️ Key Flood-Prone Areas")

if not df.empty:
    alert = latest['flood_alert']
    if "Level 3" in alert:
        marker_color = 'darkred'
    elif "Level 2" in alert:
        marker_color = 'orange'
    elif "Level 1" in alert:
        marker_color = 'blue'
    else:
        marker_color = 'green'

    locations = [
        {"name": "Gaborone Dam", "lat": -24.700, "lon": 25.950},
        {"name": "Notwane River Area", "lat": -24.710, "lon": 25.930},
        {"name": "Old Naledi", "lat": -24.670, "lon": 25.910}
    ]

    m = folium.Map(location=[-24.69, 25.93], zoom_start=12)

    for loc in locations:
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=8,
            popup=loc["name"],
            color=marker_color,
            fill=True,
            fill_opacity=0.7
        ).add_to(m)

    st_folium(m, width=700, height=450)
else:
    st.info("Map not available as no data is loaded.")