import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor SP18 v5.4", page_icon="🏫", layout="centered")

st.title("🏫 Monitor Zastępstw SP18 v5.4")
st.markdown("Wersja mobilna dla **Android / iPhone / Chromebook**")

# --- INTERFEJS UŻYTKOWNIKA ---
target_name = st.text_input("Wpisz nazwisko nauczyciela:", "Pielok-Opara")
check_now = st.button("🔍 SPRAWDŹ I CZYTAJ")

def get_substitutions(name):
    url = "https://sp18.chorzow.pl/substitution/"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--blink-settings=imagesEnabled=false")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        
        wait = WebDriverWait(driver, 20)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Informacje dla nauczycieli')]")))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(4)
        except Exception:
            pass

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
        
        if raw_entries:
            raw_entries.sort(key=lambda x: (int(''.join(filter(str.isdigit, x[0]))), 0 if "(" in x[0] else 1))
        
        return raw_entries
    except Exception as e:
        return f"Błąd połączenia: {str(e)}"
    finally:
        if driver:
            driver.quit()

# --- LOGIKA WYŚWIETLANIA I AUDIO ---
if check_now:
    with st.spinner('Łączę się z serwerem SP18... Proszę czekać.'):
        results = get_substitutions(target_name)
        
        # Zmienna na tekst dla lektora
        full_speech_text = ""
        
        if isinstance(results, str):
            st.error(results)
            full_speech_text = "Wystąpił błąd połączenia ze stroną szkoły."
        elif results:
            st.balloons()
            st.warning(f"🔔 Znaleziono zmiany dla: **{target_name}**")
            
            for p, i in results:
                # Twoje ulubione formatowanie wizualne
                with st.expander(f"Lekcja {p}", expanded=True):
                    display_text = i.replace("➔", " ➡️ ")
                    st.write(f"**Opis:** {display_text}")
                
                # Budowanie tekstu do czytania
                speech_line = f"Lekcja {p} " + i.replace(":", " klasa ", 1).replace("➔", " zamiana na ")
                full_speech_text += speech_line + ". "
        else:
            # Komunikat o braku zmian
            st.success(f"✅ Brak zastępstw dla: **{target_name}**")
            full_speech_text = f"Dla nazwiska {target_name} brak nowych zastępstw. Masz czyste niebo."

        # --- SEKCJA AUDIO (UKRYTY SKRYPT) ---
        if full_speech_text:
            js_text = full_speech_text.replace('"', '').replace("'", "").replace("\n", " ")
            tts_html = f"""
            <script>
            function speakNow() {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance();
                    msg.text = "{js_text}";
                    msg.lang = 'pl-PL';
                    msg.rate = 0.9;
                    window.speechSynthesis.speak(msg);
                }}
            }}
            setTimeout(speakNow, 500);
            </script>
            <div style="text-align: center; color: #555; font-size: 0.8em; margin-top: 10px;">
                📢 Lektor odczytuje plan...
            </div>
            """
            st.components.v1.html(tts_html, height=50)

# --- STOPKA ---
st.divider()
st.caption(f"v5.4 Stable Audio | Czas serwera: {time.strftime('%H:%M:%S')}")
