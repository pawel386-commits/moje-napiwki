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

# --- STYLIZACJA CSS (KLONOWANIE WYGLĄDU ZE SCREENA) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #fcfcfc; }
    header {visibility: hidden;}
    
    /* Górne menu */
    .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 20px; }
    .logo-text { color: #dc3545; font-weight: bold; font-size: 20px; display: flex; align-items: center; }
    
    /* Metryki u góry */
    .metric-container { background: #dc3545; color: white; border-radius: 10px; padding: 15px; text-align: center; }
    .metric-label { font-size: 0.8rem; opacity: 0.9; }
    .metric-value { font-size: 1.4rem; font-weight: bold; }

    /* Kalendarz */
    .weekday-header { background-color: #dc3545; color: white; padding: 10px; text-align: center; font-weight: bold; border: 0.5px solid #c82333; }
    .cal-cell { border: 0.5px solid #eee; min-height: 100px; padding: 5px; background: white; position: relative; }
    .day-num { font-size: 1rem; color: #666; font-weight: bold; margin-bottom: 10px; }
    .tip-pill { background-color: #dc3545; color: white; border-radius: 20px; padding: 4px 12px; font-weight: bold; font-size: 0.9rem; text-align: center; margin: 5px auto; width: 80%; }
    .holiday-cell { background-color: #fff5f5; }

    /* Dolne panele */
    .footer-card { background: #dc3545; color: white; border-radius: 15px; padding: 25px; text-align: center; min-height: 150px; }
    .footer-label { font-size: 1rem; margin-bottom: 10px; }
    .footer-value { font-size: 1.8rem; font-weight: bold; }
    
    /* Ukrywanie standardowych przycisków streamlit by wyglądały jak kafelki */
    .stButton button { width: 100%; background: transparent; border: none; height: 100px; position: absolute; top: 0; left: 0; z-index: 10; color: transparent; }
    .stButton button:hover { background: rgba(220, 53, 69, 0.05); color: transparent; }
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

# --- OKNO DIALOGOWE (POPUP) ---
@st.dialog("Dodaj napiwek")
def edit_day(target_date):
    st.write(f"📅 Dzień: **{target_date}**")
    t_input = st.number_input("Suma napiwków (zł)", min_value=0.0, step=5.0)
    d_input = st.number_input("Liczba dostaw", min_value=1, step=1)
    if st.button("Zapisz"):
        save_entry(target_date, t_input, d_input)
        st.rerun()

# --- INTERFEJS ---
df = load_data()
dzis = date.today()

# Top Bar
st.markdown("""<div class='top-bar'><div class='logo-text'>dpd &nbsp; <span style='color:#333; font-weight:normal; font-size:16px;'>Kalkulator napiwków</span></div><div>Paweł &nbsp; <span style='color:#dc3545; font-weight:bold;'>Wyloguj</span></div></div>""", unsafe_allow_html=True)

# Statystyki Miesięczne
mies_df = df[pd.to_datetime(df['data']).dt.month == dzis.month]
total_m = mies_df['napiwki'].sum()
avg_m = mies_df['napiwki'].mean() if not mies_df.empty else 0

c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 1, 1, 1, 1])
with c_h1: st.markdown(f"### < {calendar.month_name[dzis.month]} {dzis.year} >", unsafe_allow_html=True)
with c_h3: st.markdown(f"<div class='metric-container'><div class='metric-label'>Razem w miesiącu</div><div class='metric-value'>{total_m:.2f} zł</div></div>", unsafe_allow_html=True)
with c_h4: st.markdown(f"<div class='metric-container'><div class='metric-label'>Średnia dzienna</div><div class='metric-value'>{avg_m:.2f} zł</div></div>", unsafe_allow_html=True)
with c_h5: st.markdown(f"<div class='metric-container'><div class='metric-label'>Dni pracy</div><div class='metric-value'>{len(mies_df)}/22</div></div>", unsafe_allow_html=True)

st.write("")

# Kalendarz
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(dzis.year, dzis.month)

# Nagłówki dni
h_cols = st.columns(7)
weekdays = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
for i, name in enumerate(weekdays):
    h_cols[i].markdown(f"<div class='weekday-header'>{name}</div>", unsafe_allow_html=True)

# Siatka dni
for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        with cols[i]:
            if d.month == dzis.month:
                day_data = df[df['data'] == d]
                tip_val = day_data.iloc[0]['napiwki'] if not day_data.empty else None
                
                is_hol = d in PL_HOLIDAYS or d.weekday() == 6
                bg_style = "holiday-cell" if is_hol else ""
                
                # Renderowanie kafelka
                st.markdown(f"""<div class="cal-cell {bg_style}"><div class="day-num">{d.day}</div></div>""", unsafe_allow_html=True)
                if tip_val is not None:
                    st.markdown(f"""<div style="position:absolute; top:40px; width:90%; left:5%;"><div class="tip-pill">{tip_val} zł</div></div>""", unsafe_allow_html=True)
                
                # Przycisk "Klikalny Kafelek"
                if st.button(f"btn_{d}", key=f"d_{d}"):
                    edit_day(d)
            else:
                st.markdown("<div class='cal-cell' style='background:#f9f9f9;'></div>", unsafe_allow_html=True)

st.write("")

# Panele dolne
f1, f2, f3 = st.columns(3)
with f1:
    best_day = df.loc[df['napiwki'].idxmax()] if not df.empty else None
    val = f"{best_day['data'].day} {calendar.month_name[best_day['data'].month]}" if best_day is not None else "---"
    st.markdown(f"<div class='footer-card'><div class='footer-label'>Najlepszy dzień</div><div class='footer-value'>{val}</div></div>", unsafe_allow_html=True)
with f2:
    st.markdown(f"<div class='footer-card'><div class='footer-label'>Średnia tygodniowa</div><div class='footer-value'>{avg_m*5:.2f} zł</div></div>", unsafe_allow_html=True)
with f3:
    st.markdown(f"<div class='footer-card'><div class='footer-label'>Trend</div><div class='footer-value'>Świetny 🔥</div></div>", unsafe_allow_html=True)

# Przycisk eksportu (mały, biały u góry jak na screenie)
st.sidebar.download_button("📤 Eksportuj dane", df.to_csv(index=False), "dane.csv")
