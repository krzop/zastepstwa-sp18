import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor SP18 v5.1", page_icon="🏫", layout="centered")

st.title("🏫 Monitor Zastępstw SP18 v5.1")
st.markdown("Wersja mobilna z **funkcją lektora**")

# --- INTERFEJS UŻYTKOWNIKA ---
target_name = st.text_input("Wpisz nazwisko nauczyciela:", "Pielok-Opara")
check_now = st.button("🔍 SPRAWDŹ ZASTĘPSTWA")

def get_substitutions(name):
    url = "https://sp18.chorzow.pl/substitution/"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
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
        except:
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
            # Sortowanie v5: (3) przed 3
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

# --- LOGIKA WYŚWIETLANIA I LEKTORA ---
if check_now:
    with st.spinner('Pobieram dane...'):
        results = get_substitutions(target_name)
        
        if isinstance(results, str):
            st.error(results)
        elif results:
            st.warning(f"🔔 Znaleziono zmiany dla: **{target_name}**")
            
            full_speech_text = ""
            
            for p, i in results:
                # Wyświetlanie na ekranie
                with st.expander(f"Lekcja {p}", expanded=True):
                    display_text = i.replace("➔", " ➡️ ")
                    st.write(f"**Opis:** {display_text}")
                
                # Przygotowanie tekstu dla lektora (Twoja logika z "klasa")
                # Zamieniamy pierwszy dwukropek na słowo klasa w każdym wierszu
                line_for_speech = f"Lekcja {p} " + i.replace(":", " klasa ", 1).replace("➔", " zamiana na ")
                full_speech_text += line_for_speech + ". "

            # Przycisk głosowy (JavaScript)
            if full_speech_text:
                # Czyszczenie tekstu pod JavaScript
                js_text = full_speech_text.replace('"', '').replace("'", "").replace("\n", " ")
                
                tts_html = f"""
                <script>
                function speakPlan() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel(); // Zatrzymaj jeśli już coś mówi
                        var msg = new SpeechSynthesisUtterance();
                        msg.text = "{js_text}";
                        msg.lang = 'pl-PL';
                        msg.rate = 0.9;
                        window.speechSynthesis.speak(msg);
                    }} else {{
                        alert("Twoja przeglądarka nie obsługuje syntezatora mowy.");
                    }}
                }}
                </script>
                <div style="text-align: center;">
                    <button onclick="speakPlan()" style="
                        width: 100%;
                        background-color: #27AE60;
                        color: white;
                        padding: 20px;
                        border: none;
                        border-radius: 12px;
                        font-size: 20px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-top: 15px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                    ">🔊 PRZECZYTAJ PLAN NA GŁOS</button>
                </div>
                """
                st.components.v1.html(tts_html, height=120)
        else:
            st.success(f"✅ Brak zastępstw dla: **{target_name}**")

st.divider()
st.caption(f"Aktualizacja: v5.1 Mobile | {time.strftime('%H:%M:%S')}")
