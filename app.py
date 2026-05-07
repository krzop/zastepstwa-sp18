import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor SP18 v5", page_icon="🏫", layout="centered")

st.title("🏫 Monitor Zastępstw SP18 v5")
st.markdown("Wersja mobilna dla **Android / iPhone / Chromebook**")

# --- INTERFEJS UŻYTKOWNIKA ---
target_name = st.text_input("Wpisz nazwisko nauczyciela:", "Pielok-Opara")
check_now = st.button("🔍 SPRAWDŹ ZASTĘPSTWA")

def get_substitutions(name):
    url = "https://sp18.chorzow.pl/substitution/"
    
    # Konfiguracja opcji Chrome pod serwer Linux (Streamlit Cloud)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    # Wyłączenie ładowania obrazków dla przyspieszenia działania
    options.add_argument("--blink-settings=imagesEnabled=false")
    
    driver = None
    try:
        # Inicjalizacja Drivera (Streamlit sam dopasuje wersję z packages.txt)
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # Wejście na stronę
        driver.get(url)
        
        # Oczekiwanie na przycisk "Informacje dla nauczycieli"
        wait = WebDriverWait(driver, 20)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Informacje dla nauczycieli')]")))
            driver.execute_script("arguments[0].click();", btn)
            # Czekamy chwilę na załadowanie dynamicznej tabeli
            time.sleep(4)
        except Exception as btn_err:
            st.warning("Nie udało się kliknąć przycisku (może tabela już jest widoczna?). Kontynuuję...")

        # Pobranie kodu strony i analiza BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        sections = soup.find_all("div", class_="section print-nobreak")
        
        raw_entries = []
        target_lower = name.lower()
        
        for sec in sections:
            header = sec.find("div", class_="header")
            if header and target_lower in header.get_text().lower():
                rows = sec.find_all("div", class_="row")
                for r in rows:
                    p = r.find("div", class_="period")
                    i = r.find("div", class_="info")
                    if p and i:
                        raw_entries.append((p.get_text(strip=True), i.get_text(strip=True)))
        
        # Sortowanie według logiki v5: (3) przed 3
        if raw_entries:
            raw_entries.sort(key=lambda x: (
                int(''.join(filter(str.isdigit, x[0]))), 
                0 if "(" in x[0] else 1
            ))
        
        return raw_entries

    except Exception as e:
        return f"Błąd połączenia: {str(e)}"
    finally:
        if driver:
            driver.quit()

# --- LOGIKA WYŚWIETLANIA ---
if check_now:
    with st.spinner('Łączę się z serwerem SP18... Proszę czekać.'):
        results = get_substitutions(target_name)
        
        if isinstance(results, str):
            st.error(results)
            st.info("💡 Porada: Jeśli błąd się powtarza, spróbuj 'Reboot App' w menu Streamlit.")
        elif results:
            st.balloons() # Mały efekt sukcesu
            st.warning(f"🔔 Znaleziono zmiany dla: **{target_name}**")
            
            for p, i in results:
                # Formatowanie dla wersji mobilnej
                with st.expander(f"Lekcja {p}", expanded=True):
                    # Zamiana strzałki na czytelniejszą ikonę
                    display_text = i.replace("➔", " ➡️ ")
                    st.write(f"**Opis:** {display_text}")
        else:
            st.success(f"✅ Brak zastępstw dla: **{target_name}**")

# --- STOPKA ---
st.divider()
st.caption(f"Aktualny czas serwera: {time.strftime('%H:%M:%S')}")
st.caption("Silnik: Monitor v5 (Stable) | SP18 Chorzów")
