import streamlit as st
import pandas as pd
import holidays
import requests
import calendar
from datetime import date
import os

# --- KONFIGURACJA ---
LAT, LON = 53.47, 14.50
PL_HOLIDAYS = holidays.Poland()
DB_FILE = "dane_napiwkow.csv"

st.set_page_config(page_title="Kalkulator Napiwków", layout="wide")

# --- DOPRACOWANA STYLIZACJA CSS ---
st.markdown("""
    <style>
    /* Ukrycie standardowych elementów */
    header {visibility: hidden;}
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    
    /* Tło całej strony - ciemniejszy szary dla kontrastu */
    .main { background-color: #f0f2f5; }
    
    /* Górny pasek */
    .top-bar { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 15px 25px; 
        border-bottom: 2px solid #e0e0e0; 
        background: white;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .logo-text { color: #dc3545; font-weight: bold; font-size: 24px; }
    
    /* Nagłówki dni tygodnia */
    .weekday-header { 
        background-color: #dc3545; 
        color: white; 
        padding: 12px 5px; 
        text-align: center; 
        font-weight: bold; 
        border: 1px solid #b21f2d;
        font-size: 0.9rem;
        text-transform: uppercase;
    }

    /* KAFELKI KALENDARZA - WYMUSZENIE ROZMIARU */
    div.stButton > button {
        width: 100% !important;
        height: 120px !important; /* Stała wysokość kafelka */
        border-radius: 0px !important;
        border: 1px solid #d1d1d1 !important;
        background-color: white !important;
        color: #333 !important;
        font-weight: bold !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        padding: 10px !important;
        transition: all 0.2s ease;
        box-shadow: inset 0 0 0 1px transparent;
    }
    
    div.stButton > button:hover {
        border-color: #dc3545 !important;
        background-color: #fff5f5 !important;
        z-index: 10;
        box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2) !important;
    }

    /* Wygląd tekstu wewnątrz kafelka */
    div.stButton p {
        margin: 0 !important;
        font-size: 1.1rem !important;
        text-align: left !important;
    }

    /* Dolne karty statystyk */
    .footer-card { 
        background: #dc3545; 
        color: white; 
        border-radius: 12px; 
        padding: 25px; 
        text-align: center; 
        margin-top: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .footer-label { font-size: 0.9rem; opacity: 0.9; margin-bottom: 5px; display: block; }
    .footer-val { font-size: 1.8rem; font-weight: bold; display: block; }

    /* Metryki u góry */
    [data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    return pd.DataFrame(columns=['data', 'napiwki', 'dostawy', 'temp', 'deszcz'])

def save_entry(d, t_val, d_val):
    # Pobieranie pogody
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&timezone=Europe/Warsaw"
        r = requests.get(url).json()
        temp = r['daily']['temperature_2m_max'][0]
        rain = r['daily']['precipitation_sum'][0]
    except:
        temp, rain = 0, 0
    
    df = load_data()
    new_data = pd.DataFrame([{'data': d, 'napiwki': t_val, 'dostawy': d_val, 'temp': temp, 'deszcz': rain}])
    df = pd.concat([df, new_data]).drop_duplicates(subset=['data'], keep='last')
    df.to_csv(DB_FILE, index=False)

@st.dialog("Dodaj/Edytuj napiwek")
def show_popup(target_date):
    st.write(f"📅 Edytujesz dzień: **{target_date}**")
    t_input = st.number_input("Suma napiwków (zł)", min_value=0.0, step=5.0)
    d_input = st.number_input("Liczba dostaw", min_value=1, step=1)
    if st.button("Zapisz zmiany", use_container_width=True):
        save_entry(target_date, t_input, d_input)
        st.rerun()

# --- START APLIKACJI ---
df = load_data()
dzis = date.today()

# Custom Header
st.markdown(f"""
    <div class='top-bar'>
        <div class='logo-text'>dpd <span style='color:#333; font-weight:normal; font-size:18px;'>| Kalkulator napiwków</span></div>
        <div style='color:#666; font-size:14px;'>Witaj, <b>Paweł</b> &nbsp; <span style='color:#dc3545; cursor:pointer;'>[Wyloguj]</span></div>
    </div>
""", unsafe_allow_html=True)

# Główne metryki
mies_df = df[pd.to_datetime(df['data']).dt.month == dzis.month]
total_m = mies_df['napiwki'].sum()
avg_m = mies_df['napiwki'].mean() if not mies_df.empty else 0

m_col1, m_col2, m_col3, m_col4 = st.columns([2, 1, 1, 1])
with m_col1: st.subheader(f"{calendar.month_name[dzis.month].capitalize()} {dzis.year}")
with m_col2: st.metric("Razem", f"{total_m:.2f} zł")
with m_col3: st.metric("Średnia", f"{avg_m:.2f} zł")
with m_col4: st.metric("Dni pracy", f"{len(mies_df)}/22")

st.write("")

# Kalendarz - Nagłówki
h_cols = st.columns(7)
week_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
for i, name in enumerate(week_names):
    h_cols[i].markdown(f"<div class='weekday-header'>{name}</div>", unsafe_allow_html=True)

# Kalendarz - Kratki
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(dzis.year, dzis.month)

for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        with cols[i]:
            if d.month == dzis.month:
                day_data = df[df['data'] == d]
                tip_label = ""
