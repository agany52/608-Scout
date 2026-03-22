import streamlit as st
import requests
import json
import datetime
import google.generativeai as genai

# Configure the page
st.set_page_config(
    page_title="608 Scout | Dynamic Madison Events",
    page_icon="⛺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Gradient Background for the App */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #a18cd1, #fbc2eb) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    h1, h2, h3, p, div, span, strong, label {
        color: #1e293b !important;
    }
    h1 {
        font-family: 'Inter', sans-serif;
        color: #0f172a !important;
        text-shadow: 0 2px 4px rgba(255, 255, 255, 0.5);
    }
    
    [data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.45) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(8px) !important;
    }
    [data-baseweb="input"] input {
        color: #1e293b !important;
    }
    /* Ensure the eye icon background is transparent */
    [data-baseweb="input"] > div {
        background-color: transparent !important;
    }
    .stButton > button {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        color: #1e293b !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
    }

    /* Glassmorphism Classes */
    .event-card {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-top: 1px solid rgba(255, 255, 255, 0.8);
        border-left: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .event-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.9);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.2);
    }
    .event-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0f172a !important;
        margin-bottom: 0.5rem;
    }
    .event-time {
        color: #334155 !important;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .event-venue {
        font-weight: 800;
        color: #4338ca !important;
    }
    .weather-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-top: 10px;
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        color: #1e3a8a !important;
        text-shadow: none !important;
    }
    .weather-forecast {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-top: 1px solid rgba(255, 255, 255, 0.8);
        border-left: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }
    .forecast-title {
        font-weight: 800;
        color: #0f172a !important;
        font-size: 1.2rem;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("⛺ 608 Scout (AI Powered)")
st.markdown("**Your dynamic guide to Madison, WI**")

# Inputs
selected_date = st.date_input("Select a day to scout:", datetime.date.today())
api_key = st.secrets.get("GEMINI_API_KEY", "")
st.markdown("<p style='color: #334155; font-weight: 600; margin-bottom: 24px;'>Powered by Google Gemini API ✨</p>", unsafe_allow_html=True)

# --- Agent Functions ---
def fetch_weather(date_obj):
    start_str = date_obj.strftime("%Y-%m-%d")
    url = f"https://api.open-meteo.com/v1/forecast?latitude=43.0731&longitude=-89.4012&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America%2FChicago&temperature_unit=fahrenheit&precipitation_unit=inch&start_date={start_str}&end_date={start_str}"
    try:
        r = requests.get(url)
        data = r.json()
        if 'daily' in data and data['daily']['time']:
            high = data['daily']['temperature_2m_max'][0]
            low = data['daily']['temperature_2m_min'][0]
            precip = data['daily']['precipitation_sum'][0]
            return f"High: {high}°F, Low: {low}°F, Precipitation: {precip}in"
        else:
            url_arch = f"https://archive-api.open-meteo.com/v1/archive?latitude=43.0731&longitude=-89.4012&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America%2FChicago&temperature_unit=fahrenheit&precipitation_unit=inch&start_date={start_str}&end_date={start_str}"
            r_arch = requests.get(url_arch)
            data_arch = r_arch.json()
            high = data_arch['daily']['temperature_2m_max'][0]
            low = data_arch['daily']['temperature_2m_min'][0]
            precip = data_arch['daily']['precipitation_sum'][0]
            return f"Historical High: {high}°F, Low: {low}°F, Precipitation: {precip}in"
    except Exception as e:
        return "Weather data unavailable for this date."

def generate_scout_data(api_key, date_str, weather_str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""You are the 608 Scout, an expert Madison, WI guide. 
The user is planning for {date_str}. The weather in Madison will be: {weather_str}.

You MUST output ONLY a raw JSON object with no markdown formatting around it.
The JSON object must have the following structure exactly:
{{
  "weather_summary": "Write a 2-sentence AI description of what the weather feels like and whether it's a good day to be indoors/outdoors.",
  "events": [
    {{
      "title": "A highly plausible and realistic event title in Madison",
      "time": "e.g., 7:00 PM",
      "venue": "A real Madison venue",
      "description": "1 short sentence about the event.",
      "weather_status": "e.g., Indoor Friendly 🏠 or Outdoor Event ❄️"
    }}
  ]
}}

Generate exactly 6 unique events for this specific date based on the weather.
"""
    response = model.generate_content(prompt)
    return response.text

if st.button("🚀 Scout Events!"):
    if not api_key:
        st.error("Please provide a Gemini API Key to generate the dynamic events!")
    else:
        with st.spinner("Agent 1: Fetching Weather Data..."):
            weather_data = fetch_weather(selected_date)
            
        with st.spinner("Agent 2 & 3: AI is writing descriptions and generating events..."):
            try:
                raw_json = generate_scout_data(api_key, selected_date.strftime("%A, %B %d, %Y"), weather_data)
                
                # Cleanup potential markdown ticks
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:-3]
                elif raw_json.startswith("```"):
                    raw_json = raw_json[3:-3]
                    
                data = json.loads(raw_json.strip())
                
                st.session_state.weather_summary = data.get("weather_summary", "No summary.")
                st.session_state.events = data.get("events", [])
            except Exception as e:
                st.error(f"Error communicating with AI: {e}")

# Display Results if they exist in session state
if 'weather_summary' in st.session_state and 'events' in st.session_state:
    st.markdown(f"""
    <div class="weather-forecast">
        <div class="forecast-title">🌤️ AI Weather Scout</div>
        <div style="color: #475569;">
            {st.session_state.weather_summary}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎟️ Your AI-Curated Events")
    for event in st.session_state.events:
        st.markdown(f"""
        <div class="event-card">
            <div class="event-title">{event['title']}</div>
            <div class="event-time">📍 <span class="event-venue">{event['venue']}</span> • 🕒 {event['time']}</div>
            <p style="color: #334155; margin-bottom: 12px;">{event['description']}</p>
            <div class="weather-badge weather-indoor">{event['weather_status']}</div>
        </div>
        """, unsafe_allow_html=True)
