import streamlit as st
import pandas as pd
import holidays
import requests
import plotly.express as px
from datetime import date
import os

# --- KONFIGURACJA LOKALIZACJI (SZCZECIN OSÓW) ---
LAT, LON = 53.47, 14.50 
PL_HOLIDAYS = holidays.Poland()
DB_FILE = "dane_napiwkow.csv"

st.set_page_config(page_title="Kurier TipStats Szczecin", layout="wide", page_icon="🚴")

# --- LOGIKA POBIERANIA DANYCH ---
def get_weather(target_date):
    """Pobiera dane pogodowe z darmowego API Open-Meteo"""
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={target_date}&end_date={target_date}&daily=temperature_2m_max,precipitation_sum&timezone=Europe%2FWarsaw"
    try:
        response = requests.get(url, timeout=5).json()
        temp = response['daily']['temperature_2m_max'][0]
        rain = response['daily']['precipitation_sum'][0]
        return temp, rain
    except Exception:
        return None, None

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    return pd.DataFrame(columns=['data', 'napiwki', 'dostawy', 'temp', 'deszcz', 'typ_dnia'])

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🚚 Kurier TipStats - Szczecin")

tab_add, tab_stats = st.tabs(["📝 Dodaj Raport", "📈 Analiza i Wykresy"])

# TAB 1: DODAWANIE DANYCH
with tab_add:
    col_input, col_info = st.columns([1, 1])
    
    with col_input:
        selected_date = st.date_input("Wybierz datę", date.today())
        
        # Sprawdzanie rodzaju dnia
        is_holiday = selected_date in PL_HOLIDAYS or selected_date.weekday() == 6
        is_saturday = selected_date.weekday() == 5
        
        day_type = "Roboczy"
        if is_holiday: day_type = "Wolne (Niedziela/Święto)"
        elif is_saturday: day_type = "Sobota"
        
        st.write(f"Wybrany dzień to: **{day_type}**")
        
        # Logika dostępności pól
        working = st.checkbox("Pracowałem w ten dzień", value=(not is_holiday and not is_saturday))
        
        if working:
            tips = st.number_input("Suma napiwków (zł)", min_value=0.0, step=5.0)
            count = st.number_input("Liczba dostaw", min_value=1, step=1)
            
            if st.button("Zapisz w bazie", use_container_width=True):
                with st.spinner("Pobieranie danych pogodowych..."):
                    t, r = get_weather(selected_date)
                    new_entry = pd.DataFrame([{
                        'data': selected_date,
                        'napiwki': tips,
                        'dostawy': count,
                        'temp': t,
                        'deszcz': r,
                        'typ_dnia': day_type
                    }])
                    
                    df = load_data()
                    # Usuwamy stary wpis z tego samego dnia, jeśli istnieje (nadpisywanie)
                    df = pd.concat([df, new_entry]).drop_duplicates(subset=['data'], keep='last')
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"Zapisano! Pogoda w Szczecinie: {t}°C, Opady: {r}mm")

    with col_info:
        st.info("""
        **Zasady kalendarza:**
        * Niedziele i święta są automatycznie blokowane.
        * Soboty są domyślnie wolne (zaznacz checkbox, by dodać dyżur).
        * Dane pogodowe pobierane są automatycznie dla osiedla Osów.
        """)

# TAB 2: ANALIZA
with tab_stats:
    df_main = load_data()
    
    if not df_main.empty:
        # Obliczenia
        df_main['zl_na_dostawe'] = (df_main['napiwki'] / df_main['dostawy']).round(2)
        
        # Podsumowanie liczbowe
        m1, m2, m3 = st.columns(3)
        m1.metric("Średni napiwek", f"{df_main['napiwki'].mean():.2f} zł")
        m2.metric("Napiwek / Dostawa", f"{df_main['zl_na_dostawe'].mean():.2f} zł")
        m3.metric("Najlepszy dzień", f"{df_main['napiwki'].max():.2f} zł")
        
        st.divider()
        
        # Wykres korelacji z deszczem
        st.subheader("☔ Wpływ opadów na hojność klientów")
        fig_rain = px.scatter(df_main, x="deszcz", y="zl_na_dostawe", 
                             size="napiwki", color="temp",
                             labels={"deszcz": "Opady (mm)", "zl_na_dostawe": "PLN na jedną dostawę"},
                             trendline="ols", hover_name="data")
        st.plotly_chart(fig_rain, use_container_width=True)
        
        # Wykres temperatury
        st.subheader("🌡️ Temperatura a wysokość napiwków")
        fig_temp = px.bar(df_main.sort_values("data"), x="data", y="napiwki", color="temp",
                         title="Zarobki na osi czasu z uwzględnieniem temperatury")
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Eksport
        st.divider()
        st.download_button(
            label="📥 Pobierz wszystkie dane (Excel/CSV)",
            data=df_main.to_csv(index=False).encode('utf-8'),
            file_name=f"napiwki_kurier_{date.today()}.csv",
            mime='text/csv'
        )
    else:
        st.warning("Baza danych jest pusta. Dodaj pierwszy raport!")