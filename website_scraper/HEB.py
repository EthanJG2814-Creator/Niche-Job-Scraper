import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_Path = PROJECT_ROOT / "job_data.db"
HEB_BASE_URL = "https://careers.heb.com"

#------ Basic Set up above --------


def _safe_find_text(parent, by, selector):
    try:
        value = parent.find_element(by, selector).text
        return value.strip() if value is not None else None
    except Exception:
        return None


def _safe_find_href(parent, by, selector):
    try:
        value = parent.find_element(by, selector).get_attribute("href")
        return value.strip() if value else None
    except Exception:
        return None


def _normalize_posting_end_date(raw_date):
    if not raw_date:
        return None
    try:
        return datetime.strptime(raw_date.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _dismiss_cookie_consent(driver) -> None:
    try:
        consent = driver.find_element(By.ID, "pixel-consent-container")
    except Exception:
        return

    try:
        if not consent.is_displayed():
            return
    except Exception:
        return

    # Try common consent actions first.
    selectors = [
        "#pixel-consent-container button[aria-label*='accept' i]",
        "#pixel-consent-container .cc-allow",
        "#pixel-consent-container .cc-btn",
        "#pixel-consent-container button",
    ]
    for selector in selectors:
        try:
            button = driver.find_element(By.CSS_SELECTOR, selector)
            if button.is_displayed() and button.is_enabled():
                driver.execute_script("arguments[0].click();", button)
                return
        except Exception:
            continue

    # Last resort if no known button is found.
    driver.execute_script("arguments[0].style.display='none';", consent)


def navigating_pages(driver,random_wait_func,scroll_func,set_of_links,network_performance_func):
    last_page = False
    db_connection = sqlite3.connect(DB_Path)
    cursor = db_connection.cursor()

    while last_page == False:
        if scroll_func:
            scroll_func(driver)
        # Extracting job titles and links
        print('Extracting Table Elements')
        table = driver.find_element(By.TAG_NAME,'search-job-cards')
        rows = table.find_elements(By.TAG_NAME, 'mat-expansion-panel')

        # Capture scalar values first so navigation does not invalidate row elements.
        page_jobs = []
        for row in rows:
            href_value = _safe_find_href(row, By.CLASS_NAME, 'job-title-link')
            if not href_value:
                continue

            page_jobs.append({
                "full_link": urljoin(HEB_BASE_URL, href_value),
                "job_cd": _safe_find_text(row, By.CSS_SELECTOR, '.req-id.ng-star-inserted'),
                "job_title": _safe_find_text(row, By.CLASS_NAME, 'job-title'),
                "location": _safe_find_text(row, By.CSS_SELECTOR, '.label-value.location'),
                "position_type": _safe_find_text(row, By.CSS_SELECTOR, '.label-value.tags1'),
            })

        for job in page_jobs:
            full_link = job["full_link"]

            if full_link in set_of_links:
                print('repeated job posting found, skipping...')
            else:
                print('new job posting found, extracting...')
                if random_wait_func:
                    random_wait_func()
                date_of_retrival = datetime.now().strftime("%Y-%m-%d")

                # Open the detail page for this posting now, extract, then return.
                driver.get(full_link)
                if random_wait_func:
                    random_wait_func()
                if scroll_func:
                    scroll_func(driver)
                raw_posting_end_date = _safe_find_text(driver, By.ID, "header-posting_expiry_date")
                posting_end_date = _normalize_posting_end_date(raw_posting_end_date)
                job_description = _safe_find_text(driver, By.CLASS_NAME, "main-description-section")
                bandwidth_kb = network_performance_func(driver) if network_performance_func else None

                sql = '''
                INSERT INTO "HEB DATA" (
                    "Job Title",
                    "Job Code",
                    "Location",
                    "Position Type",
                    "DATE OF RETRIVAL",
                    "Posting End Date",
                    "Job Description",
                    "URL",
                    "BANDWIDTH"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(
                    sql,
                    (
                        job["job_title"],
                        job["job_cd"],
                        job["location"],
                        job["position_type"],
                        date_of_retrival,
                        posting_end_date,
                        job_description,
                        full_link,
                        bandwidth_kb,
                    ),
                )
                db_connection.commit()
                set_of_links.add(full_link)

                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'search-job-cards'))
                )
               

        # this find the button
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Next Page of Job Search Results']"))
        )

        # this checks if the last button is disabled preventing us from moving foward.
        if random_wait_func:
            random_wait_func()
        disabled_attr = button.get_attribute("disabled")
        button_class = (button.get_attribute("class") or "")
        if disabled_attr is not None or "mat-button-disabled" in button_class:
            print("Reached last HEB results page (Next button is disabled).")
            last_page = True
            break

        # this navigates to the next page
        if random_wait_func:
            random_wait_func()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Next Page of Job Search Results']"))
        )
        print("Navigating to the next page")
        try:
            button.click()
        except ElementClickInterceptedException:
            # if a cookie pop up happens we accept it. 
            _dismiss_cookie_consent(driver)
            driver.execute_script("arguments[0].click();", button)

    db_connection.close()

def links_previously_seen(DB_Path):
    print("Checking database for past job postings")
    seen_links = set()
    db_connection = None

    try:
        # connecting to database
        db_connection = sqlite3.connect(DB_Path)
        cursor = db_connection.cursor()

        #extracting values from database
        cursor.execute('''SELECT "URL" FROM "HEB DATA"''')
        URLS = cursor.fetchall()

        # appending urls to set variable
        for url in URLS:
            link = url[0]
            if link:
                seen_links.add(link)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if db_connection is not None:
            db_connection.close()
        
    return seen_links


#----- main execution -----

def HEB_MAIN(driver,
    typing_func: Optional[Callable[[str, object], None]] = None,
    random_wait_func: Optional[Callable[[], None]] = None,
    scroll_func: Optional[Callable[[object], None]] = None,
    network_performance_func: Optional[Callable[[object], int]] = None,
    min_repeats: int = 3,
    max_repeats: int = 7,
) -> bool:
    print("Running HEB site...")

    try:
        # Extracting page values
        set_of_links = links_previously_seen(DB_Path=DB_Path)
        navigating_pages(driver,random_wait_func=random_wait_func,scroll_func=scroll_func, set_of_links = set_of_links,network_performance_func= network_performance_func)
        return True
                
    except Exception as exc:
        print(f"HEB Program Failed failed: {exc}")
        return False