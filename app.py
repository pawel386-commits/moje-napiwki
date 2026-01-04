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

# --- CSS: MAKSYMALNA STABILNOŚĆ I KONTRAST ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main { background-color: #f0f2f5 !important; }
    
    /* Górny pasek */
    .top-bar { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 25px; background: white; border-bottom: 2px solid #dc3545;
        margin-bottom: 20px;
    }
    .logo-text { color: #dc3545; font-weight: bold; font-size: 24px; }

    /* Nagłówki dni */
    .weekday-header { 
        background-color: #dc3545; color: white; padding: 10px 0; 
        text-align: center; font-weight: bold; border: 1px solid #b21f2d;
        font-size: 0.8rem; margin-bottom: 5px;
    }

    /* KAFELKI - PRZYCISKI */
    div.stButton > button {
        width: 100% !important;
        height: 100px !important;
        background-color: white !important;
        color: #333 !important;
        border: 1px solid #d1d1d1 !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        padding: 8px !important;
        margin-bottom: 10px !important;
    }
    
    div.stButton > button:hover {
        border-color: #dc3545 !important;
        background-color: #fff5f5 !important;
    }

    /* Dolne karty */
    .footer-card { 
        background: #dc3545; color: white; border-radius: 10px; 
        padding: 20px; text-align: center; min-height: 120px;
    }
    .footer-val { font-size: 1.6rem; font-weight: bold; display: block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    return pd.DataFrame(columns=['data', 'napiwki', 'dostawy', 'temp', 'deszcz'])

def save_entry(d, t_val, d_val):
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&timezone=Europe/Warsaw"
        r = requests.get(url, timeout=5).json()
        temp = r['daily']['temperature_2m_max'][0]
        rain = r['daily']['precipitation_sum'][0]
    except:
        temp, rain = 0, 0
    df = load_data()
    new_data = pd.DataFrame([{'data': d, 'napiwki': t_val, 'dostawy': d_val, 'temp': temp, 'deszcz': rain}])
    df = pd.concat([df, new_data]).drop_duplicates(subset=['data'], keep='last')
    df.to_csv(DB_FILE, index=False)

@st.dialog("Edytuj dzień")
def show_popup(target_date):
    st.write(f"📅 Data: **{target_date}**")
    t_input = st.number_input("Suma napiwków (zł)", min_value=0.0, step=5.0)
    d_input = st.number_input("Liczba dostaw", min_value=1, step=1)
    if st.button("Zapisz", use_container_width=True):
        save_entry(target_date, t_input, d_input)
        st.rerun()

# --- RENDEROWANIE ---
df = load_data()
dzis = date.today()

# Header
st.markdown("""<div class='top-bar'><div class='logo-text'>dpd | <span style='color:#333; font-weight:normal;'>Napiwki</span></div><div>Paweł [Wyloguj]</div></div>""", unsafe_allow_html=True)

# Statystyki
mies_df = df[pd.to_datetime(df['data']).dt.month == dzis.month]
m1, m2, m3 = st.columns(3)
m1.metric("W tym miesiącu", f"{mies_df['napiwki'].sum():.2f} zł")
m2.metric("Średnia", f"{mies_df['napiwki'].mean() if not mies_df.empty else 0:.2f} zł")
m3.metric("Dni pracy", f"{len(mies_df)}/22")

st.write("---")

# Kalendarz
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(dzis.year, dzis.month)

# Nagłówki dni
h_cols = st.columns(7)
for i, name in enumerate(["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]):
    h_cols[i].markdown(f"<div class='weekday-header'>{name}</div>", unsafe_allow_html=True)

# Generowanie kafelków
for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        with cols[i]:
            if d.month == dzis.month:
                day_data = df[df['data'] == d]
                tip_text = ""
                if not day_data.empty:
                    tip_text = f"\n💰 {day_data.iloc[0]['napiwki']} zł"
                
                # KLUCZOWE: Dodanie unikalnego klucza (key) dla każdego przycisku
                if st.button(f"{d.day}{tip_text}", key=f"day_{d.day}_{d.month}"):
                    show_popup(d)
            else:
                st.write(" ")

# Panele dolne
st.write("---")
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(f"<div class='footer-card'>Najlepszy dzień<span class='footer-val'>{df['napiwki'].max() if not df.empty else 0:.2f} zł</span></div>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<div class='footer-card'>Średnia tydzień<span class='footer-val'>{(mies_df['napiwki'].sum()/4):.2f} zł</span></div>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<div class='footer-card'>Trend<span class='footer-val'>Świetny 🔥</span></div>", unsafe_allow_html=True)
