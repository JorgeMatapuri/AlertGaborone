import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

st.set_page_config(page_title="Flood Alert Dashboard", layout="wide")


st.title("🌧️ Gaborone Flood Alert Dashboard")

# Connect to SQLite and load data
# Ordering by timestamp ASC ensures that `tail()` correctly picks the most recent entries.
conn = sqlite3.connect("alertGabs_rain_db")
df = pd.read_sql_query("SELECT * FROM weather ORDER BY timestamp ASC", conn)
conn.close()

# Convert timestamp to datetime objects for plotting and easier manipulation.
df['timestamp_dt'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d,%H:%M:%S')

# --- Visualization for the last seven entries ---
chart_df = df.tail(7)

# --- Display Recent Weather Records in a Table ---
st.subheader("Recent Weather Records")
# Display the most recent 7 entries in a DataFrame table.
st.dataframe(df.tail(7).drop(columns=['timestamp_dt'])) # Drop the datetime column for cleaner table display

# --- Display Latest Flood Alert ---
st.subheader("🚨 Latest Alert")
if not df.empty:
    latest = df.iloc[-1] # Get the very last entry in the DataFrame
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
st.subheader("📊 Rainfall Trends (Last 7 Entries)") # Updated subheader to reflect the 7 entries
if not chart_df.empty:
    fig, ax = plt.subplots(figsize=(10, 5)) # Create a matplotlib figure and axes
    
    # Convert datetime objects to Matplotlib's internal numeric format for plotting
    x_values_numeric = mdates.date2num(chart_df['timestamp_dt'])
    
    ax.plot(x_values_numeric, chart_df['rainfall'], marker='o', linestyle='-', color='skyblue')

    ax.set_xlabel("Time")
    ax.set_ylabel("Rainfall (mm)")
    ax.set_title("Hourly Rainfall Over Time")
    ax.grid(True) # Add a grid for better readability
    
    # Dynamic Y-axis Control
    max_rainfall = chart_df['rainfall'].max()
    ax.set_ylim(bottom=0, top=max_rainfall * 1.1 if max_rainfall > 0 else 1) # Ensure top is at least 1 if max_rainfall is 0
    
    # Set major ticks to be exactly at each data point's timestamp
    if len(chart_df) <= 7:
        ax.xaxis.set_major_locator(mticker.FixedLocator(mdates.date2num(chart_df['timestamp_dt'])))
    else:
        ax.xaxis.set_major_locator(mticker.AutoLocator())

    ax.xaxis.set_tick_params(rotation=45) 
    
    # Use a formatter that includes both date and time
    # '%Y-%m-%d %H:%M' shows year-month-day hour:minute for clarity.
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    fig.autofmt_xdate() # Automatically rotates and aligns the date labels to prevent overlap
    
    st.pyplot(fig) # Display the matplotlib figure in Streamlit
else:
    st.info("Not enough data to display rainfall trends yet. Collect more data to see trends.")
# --- END Rainfall Trends Chart Section ---


# --- Map section ---
st.subheader("🗺️ Key Flood-Prone Areas")

if not df.empty: # This block ensures map is only displayed if data exists
    alert = latest['flood_alert']
    if "Level 3" in alert:
        marker_color = 'darkred'
    elif "Level 2" in alert:
        marker_color = 'orange'
    elif "Level 1" in alert: # Level 1 is usually advisory, so yellow can be a good intermediate warning
        marker_color = 'yellow' # Changed from blue to yellow for Level 1
    else:
        marker_color = 'green'

    # Updated list of locations for Gaborone, including new bridges and low roads
    locations = [
        {"name": "Gaborone Dam", "lat": -24.700, "lon": 25.950},
        {"name": "Notwane River Area", "lat": -24.710, "lon": 25.930},
        {"name": "Old Naledi", "lat": -24.670, "lon": 25.910},
        {"name": "Bridge 1 (Gaborone West)", "lat": -24.654, "lon": 25.864},
        {"name": "Bridge 2 (Phase 4)", "lat": -24.651, "lon": 25.870},
        {"name": "Bridge 3 (Partial)", "lat": -24.644, "lon": 25.883},
        {"name": "Bridge 4 (Gaborone North)", "lat": -24.640, "lon": 25.888},
        {"name": "Bridge 5 (Mogoditshane Rd)", "lat": -24.638, "lon": 25.902},
        {"name": "Bridge 6 (Broadhurst)", "lat": -24.637, "lon": 25.915},
        {"name": "Bridge 7 (Phakalane Bypass)", "lat": -24.637, "lon": 25.928},
        {"name": "Bridge 8 (Airport Rd)", "lat": -24.637, "lon": 25.939},
        {"name": "Low Road (Near Notwane)", "lat": -24.598, "lon": 25.941},
        {"name": "Low Road (Central)", "lat": -24.635, "lon": 25.893},

    ]

    # Create map centered on Gaborone
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

    # Center the map using st.columns with increased width and height
    col1, col2, col3 = st.columns([1, 4, 1]) # Create 3 columns: 1 (empty), 4 (for map), 1 (empty)
    with col2: # Place the map in the middle column
        st_folium(m, width=1200, height=650) # Updated width and height
else:
    st.info("Map not available as no data is loaded.")
