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

# --- STYLIZACJA CSS (KLON DPD) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main { background-color: #fcfcfc; }
    
    /* Górny pasek */
    .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-bottom: 1px solid #eee; background: white; }
    .logo-text { color: #dc3545; font-weight: bold; font-size: 22px; }
    
    /* Nagłówki dni tygodnia */
    .weekday-header { background-color: #dc3545; color: white; padding: 10px; text-align: center; font-weight: bold; border: 0.5px solid #b21f2d; margin-bottom: 0px; }

    /* Stylizacja PRZYCISKÓW jako KAFELKÓW */
    div.stButton > button {
        width: 100%;
        min-height: 100px;
        border-radius: 0px;
        border: 0.5px solid #eee !important;
        background-color: white;
        color: #666;
        font-weight: bold;
        display: block;
        text-align: left;
        vertical-align: top;
        padding: 5px;
        transition: all 0.2s;
        margin: 0px;
    }
    div.stButton > button:hover {
        border-color: #dc3545 !important;
        background-color: #fffafa;
        color: #dc3545;
    }
    div.stButton > button:active {
        background-color: #dc3545 !important;
        color: white !important;
    }

    /* Wyświetlanie napiwku wewnątrz przycisku (trick z pseudo-elementem) */
    .tip-inside {
        display: block;
        background-color: #dc3545;
        color: white;
        border-radius: 15px;
        padding: 2px 8px;
        font-size: 0.85em;
        margin-top: 10px;
        text-align: center;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }

    /* Dolne karty */
    .footer-card { background: #dc3545; color: white; border-radius: 15px; padding: 20px; text-align: center; margin-top: 20px; }
    .footer-val { font-size: 1.5rem; font-weight: bold; display: block; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    return pd.DataFrame(columns=['data', 'napiwki', 'dostawy', 'temp', 'deszcz'])

def save_entry(d, t_val, d_val):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={d}&end_date={d}&daily=temperature_2m_max,precipitation_sum&timezone=Europe/Warsaw"
    try:
        r = requests.get(url).json()
        temp = r['daily']['temperature_2m_max'][0]
        rain = r['daily']['precipitation_sum'][0]
    except:
        temp, rain = 20, 0
    df = load_data()
    new_data = pd.DataFrame([{'data': d, 'napiwki': t_val, 'dostawy': d_val, 'temp': temp, 'deszcz': rain}])
    df = pd.concat([df, new_data]).drop_duplicates(subset=['data'], keep='last')
    df.to_csv(DB_FILE, index=False)

# --- OKNO POPUP ---
@st.dialog("Edytuj dane dnia")
def show_popup(target_date):
    st.write(f"📅 Wybrałeś: **{target_date}**")
    t_input = st.number_input("Suma napiwków (zł)", min_value=0.0, step=5.0)
    d_input = st.number_input("Liczba dostaw", min_value=1, step=1)
    if st.button("Zatwierdź i zapisz"):
        save_entry(target_date, t_input, d_input)
        st.rerun()

# --- APLIKACJA ---
df = load_data()
dzis = date.today()

# Header
st.markdown("""<div class='top-bar'><div class='logo-text'>dpd <span style='color:#333; font-weight:normal; font-size:16px;'>Kalkulator napiwków</span></div><div>Paweł &nbsp; <span style='color:#dc3545; font-weight:bold;'>Wyloguj</span></div></div>""", unsafe_allow_html=True)

# Metryki
mies_df = df[pd.to_datetime(df['data']).dt.month == dzis.month]
total_m = mies_df['napiwki'].sum()
avg_m = mies_df['napiwki'].mean() if not mies_df.empty else 0

c1, c2, c3, c4, c5 = st.columns([2, 0.5, 1, 1, 1])
with c1: st.subheader(f"{calendar.month_name[dzis.month]} {dzis.year}")
with c3: st.metric("Razem", f"{total_m:.2f} zł")
with c4: st.metric("Średnia", f"{avg_m:.2f} zł")
with c5: st.metric("Dni pracy", f"{len(mies_df)}/22")

# Kalendarz
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(dzis.year, dzis.month)

# Nagłówki dni
h_cols = st.columns(7)
for i, name in enumerate(["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]):
    h_cols[i].markdown(f"<div class='weekday-header'>{name}</div>", unsafe_allow_html=True)

# Siatka przycisków
for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        with cols[i]:
            if d.month == dzis.month:
                day_data = df[df['data'] == d]
                label = f"{d.day}"
                
                # Jeśli są dane, dodajemy informację o napiwku do etykiety przycisku (uproszczone dla stabilności)
                if not day_data.empty:
                    val = day_data.iloc[0]['napiwki']
                    label = f"{d.day}\n\n{val} zł"
                
                # Renderowanie przycisku-kafelka
                if st.button(label, key=f"btn_{d}"):
                    show_popup(d)
            else:
                st.write("")

# Dolne karty
st.write("")
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(f"<div class='footer-card'>Najlepszy dzień<span class='footer-val'>22 Grudnia</span></div>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<div class='footer-card'>Średnia tygodniowa<span class='footer-val'>{avg_m*5:.2f} zł</span></div>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<div class='footer-card'>Trend<span class='footer-val'>Świetny 🔥</span></div>", unsafe_allow_html=True)

st.sidebar.download_button("Eksportuj", df.to_csv(index=False), "dane.csv")
