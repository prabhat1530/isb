import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants
BASE_URL = "https://indiankanoon.org/search/"
COURTS = {
    "Allahabad High Court": "allahabad",
    # "Bombay High Court": "bombay"
}

# Updated Date Filters (DD-MM-YYYY format)
DATE_FILTERS = [
    ("1-1-2024", "31-1-2024")
    # ("1-2-2024", "29-2-2024"),
    # ("1-3-2024", "31-3-2024")
]

# Number of pages to scrape
MAX_PAGES = 10  # From pagenum=0 to pagenum=10

def scrape_data():
    options = uc.ChromeOptions()
    options.headless = False  # Set to True for headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)

    data = []

    for court_name, court_param in COURTS.items():
        for start_date, end_date in DATE_FILTERS:
            for page_num in range(MAX_PAGES + 1):  # Iterate through pages (0 to 10)
                print(f"🔍 Scraping {court_name} from {start_date} to {end_date} | Page {page_num}...")
               
                # Construct URL with pagination
                url = f"{BASE_URL}?formInput=doctypes%3A{court_param}+fromdate%3A{start_date}+todate%3A{end_date}&pagenum={page_num}"
                if page_num==0:
                  url=f"{BASE_URL}?formInput=doctypes%3A{court_param}+fromdate%3A{start_date}+todate%3A{end_date}"
                print(f"➡ Navigating to: {url}")
                

                driver.get(url)
                time.sleep(10)  # Wait for Cloudflare

                # Debug: Check if page loaded
                page_source = driver.page_source
               
                if "No results found" in page_source or "did not match any documents" in page_source:
                    print(f"⚠ No cases found for {court_name} from {start_date} to {end_date} (Page {page_num})")
                    continue

                # Extract case links
                case_links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, ".result .result_title a")]

                if not case_links:
                    print(f"⚠ No cases found for {court_name} from {start_date} to {end_date} (Page {page_num})")
                    continue

                for case_url in case_links:
                    print(f"📄 Fetching Case: {case_url}")
                    driver.get(case_url)
                    time.sleep(3)  # Allow page to load

                    try:
                        case_details = {
                            "High Court": court_name,
                            "Case Title": get_text(driver, ".doc_title"),
                            "Bench": get_text(driver, ".doc_bench"),
                            "Case Details": get_text(driver, "#pre_1"),
                            "Judgement Text": get_judgement_text(driver),
                        }
                        data.append(case_details)
                    except Exception as e:
                        print(f"⚠ Error fetching case: {e}")

    driver.quit()
    save_to_excel(data)

def get_text(driver, selector):
    """Utility function to extract text from an element."""
    try:
        return WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).text.strip()
    except:
        return "N/A"

def get_judgement_text(driver):
    """Extracts judgment text starting from the 7th child element."""
    try:
        parent_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".judgments"))
        )
        children = parent_element.find_elements(By.XPATH, "./*")  # Get all child elements

        # Extract text from the 7th child onwards
        judgement_text = "\n".join(child.text for child in children[6:] if child.text)

        return judgement_text if judgement_text else "N/A"
    except:
        return "N/A"

def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("court_cases.xlsx", index=False)
    print("✅ Data saved to court_cases.xlsx")

if __name__ == "__main__":
    scrape_data()