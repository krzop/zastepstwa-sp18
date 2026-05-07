import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# Ustawienia strony
st.set_page_config(page_title="Monitor SP18 v5", page_icon="🏫")

st.title("🏫 Monitor Zastępstw SP18 v5")
st.write("Wersja mobilna (Android / iPhone / Chromebook)")

# Interfejs
target_name = st.text_input("Wpisz nazwisko:", "Pielok-Opara")
check_now = st.button("SPRAWDŹ ZASTĘPSTWA")

def get_substitutions(name):
    url = "https://sp18.chorzow.pl/substitution/"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Na Streamlit Cloud nie podajemy ścieżek na sztywno, 
    # system sam dobierze odpowiedni binarek z packages.txt
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Oczekiwanie na przycisk "Informacje dla nauczycieli"
        wait = WebDriverWait(driver, 15)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Informacje dla nauczycieli')]")))
        driver.execute_script("arguments[0].click();", btn)
        
        # Krótka pauza na przeładowanie tabeli
        time.sleep(3)
        
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
        
        driver.quit()
        
        # Logika sortowania v5 (Anulowane w nawiasach przed zwykłymi)
        raw_entries.sort(key=lambda x: (
            int(''.join(filter(str.isdigit, x[0]))), 
            0 if "(" in x[0] else 1
        ))
        
        return raw_entries

    except Exception as e:
        return f"Błąd techniczny: {str(e)}"

if check_now:
    with st.spinner('Pobieram dane ze strony szkoły...'):
        results = get_substitutions(target_name)
        
        if isinstance(results, str):
            st.error(results)
            st.info("💡 Jeśli widzisz błąd 'SessionNotCreated', upewnij się, że masz plik packages.txt na GitHubie.")
        elif results:
            st.warning(f"🔔 Znaleziono zmiany dla: {target_name}")
            for p, i in results:
                # Formatowanie wizualne dla telefonu
                st.markdown(f"### Lekcja {p}")
                display_text = i.replace("➔", " ➡️ ")
                st.info(display_text)
        else:
            st.success(f"✅ Brak zastępstw dla nazwiska {target_name} na liście.")

st.divider()
st.caption("Silnik: Monitor v5 | Status: Gotowy do pracy")
