import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor SP18 v5.2", page_icon="🏫", layout="centered")

st.title("🏫 Monitor SP18 v5.2")
st.markdown("Automatyczne pobieranie i odczytywanie zmian")

# --- INTERFEJS ---
target_name = st.text_input("Wpisz nazwisko nauczyciela:", "Pielok-Opara")
# Zmieniona nazwa przycisku sugerująca podwójne działanie
check_now = st.button("🔍 POBIERZ DANE I CZYTAJ")

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
            raw_entries.sort(key=lambda x: (int(''.join(filter(str.isdigit, x[0]))), 0 if "(" in x[0] else 1))
        
        return raw_entries
    except Exception as e:
        return f"Błąd: {str(e)}"
    finally:
        if driver:
            driver.quit()

# --- LOGIKA WYŚWIETLANIA I AUTOMATYCZNEGO CZYTANIA ---
if check_now:
    with st.spinner('Pobieram dane i przygotowuję lektora...'):
        results = get_substitutions(target_name)
        
        if isinstance(results, str):
            st.error(results)
        elif results:
            st.warning(f"🔔 Znaleziono zmiany dla: **{target_name}**")
            
            full_speech_text = ""
            for p, i in results:
                with st.expander(f"Lekcja {p}", expanded=True):
                    st.write(f"**Opis:** {i.replace('➔', ' ➡️ ')}")
                
                # Budowanie tekstu do czytania
                line_for_speech = f"Lekcja {p} " + i.replace(":", " klasa ", 1).replace("➔", " zamiana na ")
                full_speech_text += line_for_speech + ". "

            if full_speech_text:
                js_text = full_speech_text.replace('"', '').replace("'", "").replace("\n", " ")
                
                # Skrypt JavaScript, który odpala się SAMODZIELNIE po załadowaniu
                tts_html = f"""
                <script>
                function startSpeaking() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel(); 
                        var msg = new SpeechSynthesisUtterance();
                        msg.text = "{js_text}";
                        msg.lang = 'pl-PL';
                        msg.rate = 0.9;
                        window.speechSynthesis.speak(msg);
                    }}
                }}
                // Uruchomienie mowy od razu po wstrzyknięciu kodu do strony
                setTimeout(startSpeaking, 500);
                </script>
                <div style="text-align: center; padding: 10px; background: #27AE60; color: white; border-radius: 10px;">
                    📢 Lektor powinien zacząć czytać automatycznie...
                </div>
                """
                st.components.v1.html(tts_html, height=100)
        else:
            st.success(f"✅ Brak zastępstw dla: **{target_name}**")
            
            # Opcjonalnie: niech powie, że brak zmian
            no_changes_js = """
            <script>
            var msg = new SpeechSynthesisUtterance("Brak nowych zastępstw. Czyste niebo.");
            msg.lang = 'pl-PL';
            window.speechSynthesis.speak(msg);
            </script>
            """
            st.components.v1.html(no_changes_js, height=0)

st.divider()
st.caption("v5.2 Auto-Talk | Kliknij przycisk i poczekaj na głos.")
