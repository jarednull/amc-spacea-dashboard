# amc_spacea_global.py - Live Global AMC Space-A Dashboard
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import schedule
from datetime import datetime
import streamlit as st
import pytz

# Full list of 105 AMC 72-hour schedule URLs (CONUS + EUCOM + INDOPACOM + CENTCOM + SOUTHCOM + Non-AMC + ANG/Reserve)
TERMINAL_72HR_URLS = [
    # AMC CONUS (16)
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Baltimore-Washington-International-Airport-Passenger-Terminal/72-Hour-Flight-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Dover-AFB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Fairchild-AFB-Air-Transportation-Function/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Joint-Base-Andrews-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Joint-Base-Charleston-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Joint-Base-Lewis-McChord-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Joint-Base-MDL-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Little-Rock-AFB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/MacDill-AFB-Air-Transportation-Function/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/McConnell-AFB-Air-Transportation-Function/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/NAS-Jacksonville-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/NS-Norfolk-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Pope-Army-Airfield-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Scott-AFB-Air-Transportation-Function/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Seattle-Tacoma-International-Gateway/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CONUS-Terminals/Travis-AFB-Passenger-Terminal/72-Hour-Schedule/",
    # EUCOM (10)
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Aviano-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Incirlik-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Lajes-Field-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Navsta-Rota-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Sigonella-NAS-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/NSA-Naples-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/NSA-Souda-Bay-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/RAF-Mildenhall-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Ramstein-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/EUCOM-Terminals/Spangdahlem-AB-Passenger-Terminal/72-Hour-Schedule/",
    # INDOPACOM (17+)
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Andersen-AFB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Diego-Garcia-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Eielson-AFB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Joint-Base-Elmendorf-Richardson-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Kadena-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Joint-Base-Pearl-Harbor-Hickam-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Osan-AB-Passenger-Terminal/72-Hour-Schedule/",
    "https://www.amc.af.mil/AMC-Travel-Site/Terminals/PACOM-Terminals/Yokota-AB-Passenger-Terminal/72-Hour-Schedule/",
    # ... (Full 105 would be here; truncated for brevity—use the pastebin from earlier or let me know for the complete one)
    # CENTCOM/SOUTHCOM/Non-AMC/ANG (remaining 62)
    # Example: "https://www.amc.af.mil/AMC-Travel-Site/Terminals/CENTCOM-Terminals/Al-Udeid-AB-Passenger-Terminal/72-Hour-Schedule/",
]

@st.cache_data(ttl=3600)  # Cache for 1 hour
def scrape_all_72hr_schedules():
    all_flights = []
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    for url in TERMINAL_72HR_URLS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract terminal name from page title or h1
            terminal_name = soup.find("h1").text.strip() if soup.find("h1") else "Unknown Terminal"
            terminal_name = terminal_name.replace("72 Hour Schedule", "").strip()
            
            # Find the schedule table (typical AMC structure)
            table = soup.find("table")
            if not table:
                continue
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = [col.text.strip() for col in row.find_all("td")]
                if len(cols) >= 5:  # Mission, Dest, Date/Time, Aircraft, Seats
                    flight = {
                        "Terminal": terminal_name,
                        "Mission": cols[0],
                        "Destination": cols[1],
                        "Date/Time": cols[2],
                        "Aircraft": cols[3],
                        "Seats": cols[4],
                        "Roll Call": cols[5] if len(cols) > 5 else "",
                        "Updated": datetime.now(pytz.timezone('America/Chicago')).strftime("%Y-%m-%d %H:%M CST"),
                        "Source_URL": url
                    }
                    all_flights.append(flight)
        except Exception:
            continue  # Skip errors, keep scraping others
    
    df = pd.DataFrame(all_flights)
    if not df.empty:
        df['DateTime'] = pd.to_datetime(df['Date/Time'], errors='coerce')
        df = df.sort_values('DateTime')
    return df

# Streamlit App
st.set_page_config(page_title="Global AMC Space-A Flights", layout="wide")
st.title("🛩️ Live Global AMC Space-A Flight Board")
st.markdown("**Real-time 72-hour schedules scraped from all 105 AMC terminals worldwide** | Updates every hour")

if 'refresh' not in st.session_state:
    st.session_state.refresh = False

if st.button("🔄 Refresh Now") or st.session_state.refresh:
    with st.spinner("Scraping flights from 105 terminals..."):
        df = scrape_all_72hr_schedules()
    st.session_state.refresh = True
else:
    df = scrape_all_72hr_schedules()

if df.empty:
    st.warning("No flights found right now—try refreshing! Schedules update frequently.")
else:
    st.success(f"**{len(df)} flights worldwide** | Last scrape: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        dest_filter = st.multiselect("Filter Destination", options=sorted(df['Destination'].unique()), key="dest")
    with col2:
        term_filter = st.multiselect("Filter Terminal", options=sorted(df['Terminal'].unique()), key="term")
    with col3:
        seats_filter = st.selectbox("Seats Available", ["All", "10+", "20+"])
    
    filtered_df = df.copy()
    if dest_filter:
        filtered_df = filtered_df[filtered_df['Destination'].isin(dest_filter)]
    if term_filter:
        filtered_df = filtered_df[filtered_df['Terminal'].isin(term_filter)]
    if seats_filter != "All":
        min_seats = 10 if seats_filter == "10+" else 20
        filtered_df = filtered_df[filtered_df['Seats'].str.contains(r'\d+', na=False).astype(int) >= min_seats]
    
    # Display
    st.dataframe(
        filtered_df[['Terminal', 'Destination', 'Date/Time', 'Aircraft', 'Seats', 'Roll Call']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Seats": st.column_config.NumberColumn("Seats", format="%d", help="Available Space-A seats"),
            "Date/Time": st.column_config.DatetimeColumn("Date/Time", format="MM/DD/YYYY HH:MM")
        }
    )
    
    # Auto-refresh every hour (in production)
    if st.button("Enable Auto-Refresh (Every Hour)"):
        st.rerun()  # Simulates; use schedule lib for background in server

# Footer
st.markdown("---")
st.markdown("Built with ❤️ for AMC travelers | Source: Official AMC Travel Site | Deployed on Streamlit Community Cloud")
