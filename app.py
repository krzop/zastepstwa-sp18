def get_substitutions(name):
    url = "https://sp18.chorzow.pl/substitution/"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # To ustawienie jest kluczowe dla Streamlit Cloud:
    options.binary_location = "/usr/bin/chromium"
    
    try:
        # Na serwerze podajemy ścieżkę do systemowego drivera
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Informacje dla nauczycieli')]")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        sections = soup.find_all("div", class_="section print-nobreak")
        
        raw_entries = []
        for sec in sections:
            header = sec.find("div", class_="header")
            if header and name.lower() in header.get_text().lower():
                rows = sec.find_all("div", class_="row")
                for r in rows:
                    p = r.find("div", class_="period")
                    i = r.find("div", class_="info")
                    if p and i:
                        raw_entries.append((p.get_text(strip=True), i.get_text(strip=True)))
        
        driver.quit()
        raw_entries.sort(key=lambda x: (int(''.join(filter(str.isdigit, x[0]))), 0 if "(" in x[0] else 1))
        return raw_entries
    except Exception as e:
        return f"Błąd techniczny: {str(e)}"
