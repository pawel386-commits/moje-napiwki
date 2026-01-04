import streamlit as st
import pandas as pd
import holidays
import requests
import calendar
from datetime import date, datetime
import os

# --- KONFIGURACJA ---
LAT, LON = 53.47, 14.50
PL_HOLIDAYS = holidays.Poland()
DB_FILE = "dane_napiwkow.csv"

st.set_page_config(page_title="Kalkulator Napiwków", layout="wide")

# Stylizacja CSS dla wyglądu "DPD"
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #dc3545; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .calendar-card { background-color: white; border-radius: 10px; padding: 10px; border: 1px solid #ddd; text-align: center; min-height: 80px; }
    .calendar-day-num { font-weight: bold; color: #555; text-align: left; }
    .tip-value { background-color: #dc3545; color: white; border-radius: 15px; padding: 2px 8px; font-size: 0.8em; margin-top: 5px; display: inline-block; }
    .header-box { background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    return pd.DataFrame(columns=['data', 'napiwki', 'dostawy', 'temp', 'deszcz'])

df = load_data()

# --- HEADER I STATYSTYKI ---
with st.container():
    col_logo, col_user = st.columns([5, 1])
    col_logo.subheader("🔴 Kalkulator napiwków")
    col_user.write("Użytkownik: **Kurier**")

    # Obliczenia do metryk
    dzis = date.today()
    miesiac_df = df[pd.to_datetime(df['data']).dt.month == dzis.month]
    total_tips = miesiac_df['napiwki'].sum()
    avg_tip = miesiac_df['napiwki'].mean() if not miesiac_df.empty else 0
    work_days = len(miesiac_df)

    m1, m2, m3 = st.columns(3)
    m1.metric("Razem w miesiącu", f"{total_tips:.2f} zł")
    m2.metric("Średnia dzienna", f"{avg_tip:.2f} zł")
    m3.metric("Dni pracy", f"{work_days}")

# --- INTERAKTYWNY KALENDARZ ---
st.markdown(f"### < {calendar.month_name[dzis.month]} {dzis.year} >", unsafe_allow_html=True)

# Generowanie siatki kalendarza
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(dzis.year, dzis.month)

# Nagłówki dni tygodnia
cols = st.columns(7)
weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
for i, day_name in enumerate(weekdays):
    cols[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#dc3545;'>{day_name}</p>", unsafe_allow_html=True)

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day.month == dzis.month:
            # Sprawdzanie czy są dane dla tego dnia
            day_data = df[df['data'] == day]
            tip_html = ""
            if not day_data.empty:
                tip_val = day_data.iloc[0]['napiwki']
                tip_html = f"<div class='tip-value'>{tip_val} zł</div>"
            
            # Kolorowanie tła dla świąt/niedziel
            bg_color = "#fff"
            if day in PL_HOLIDAYS or day.weekday() == 6: bg_color = "#f8d7da"
            
            cols[i].markdown(f"""
                <div class="calendar-card" style="background-color: {bg_color};">
                    <div class="calendar-day-num">{day.day}</div>
                    {tip_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            cols[i].write("")

# --- PANEL EDYCJI (POD KALENDARZEM) ---
st.divider()
with st.expander("➕ Dodaj / Edytuj napiwek", expanded=True):
    col_date, col_tips, col_del, col_btn = st.columns([2, 2, 2, 1])
    with col_date:
        edit_date = st.date_input("Wybierz dzień z kalendarza", dzis)
    with col_tips:
        new_tips = st.number_input("Suma napiwków (zł)", min_value=0.0)
    with col_del:
        new_del = st.number_input("Liczba dostaw", min_value=1)
    with col_btn:
        st.write(" ") # margines
        if st.button("Zapisz"):
            # Pobieranie pogody
            url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={edit_date}&end_date={edit_date}&daily=temperature_2m_max,precipitation_sum&timezone=Europe/Warsaw"
            r = requests.get(url).json()
            t = r['daily']['temperature_2m_max'][0]
            rain = r['daily']['precipitation_sum'][0]
            
            new_entry = pd.DataFrame([{'data': edit_date, 'napiwki': new_tips, 'dostawy': new_del, 'temp': t, 'deszcz': rain}])
            df = pd.concat([df, new_entry]).drop_duplicates(subset=['data'], keep='last')
            df.to_csv(DB_FILE, index=False)
            st.rerun()

# --- ANALIZA NA DOLE ---
if st.button("📊 Pokaż szczegółową analizę pogody"):
    if not df.empty:
        df['zl_na_dostawe'] = df['napiwki'] / df['dostawy']
        fig = fig = requests.get # Tutaj można dodać wykres plotly jak w poprzedniej wersji
        st.scatter_chart(df, x="deszcz", y="zl_na_dostawe")
