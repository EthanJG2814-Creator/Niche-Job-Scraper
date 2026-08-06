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
BASE_URL = 'https://careers.universityhealth.com'

#------ Main Execution ---------
def Univeristy_Health_MAIN(driver,
    typing_func: Optional[Callable[[str, object], None]] = None,
    random_wait_func: Optional[Callable[[], None]] = None,
    scroll_func: Optional[Callable[[object], None]] = None,
    network_performance_func: Optional[Callable[[object], int]] = None,
    min_repeats: int = 3,
    max_repeats: int = 7,
) -> bool:
    print("Running University Health site...")

    try:
        # Finding hyper links on Pages
        set_of_links = links_previously_seen(DB_Path=DB_Path)
        browsing(driver,random_wait_func=random_wait_func,scroll_func=scroll_func, set_of_links = set_of_links,network_performance_func= network_performance_func)
        return True


    except Exception as exc:
        print(f"HEB Program Failed failed: {exc}")
        return False


#------- Functions to call --------

def links_previously_seen(DB_Path):
    print("checking database for past job posting")
    seen_links = set()
    db_connection = None

    try:
        # connecting to database
        db_connection = sqlite3.connect(DB_Path)
        cursor = db_connection.cursor()

        # extracting values form database
        cursor.execute('''SELECT "URL" FROM "UHEALTH DATA"''')
        URLS = cursor.fetchall()

        # apprending urls to set variable
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

def browsing(driver,random_wait_func,scroll_func,set_of_links,network_performance_func):
    last_page = False
    db_connection = sqlite3.connect(DB_Path)
    cursor = db_connection.cursor()
    _ensure_uhealth_bandwidth_column(cursor, db_connection)
    _ensure_uhealth_url_unique_index(cursor, db_connection)

    try:
        while last_page == False:
            if scroll_func:
                scroll_func(driver)
            if random_wait_func:
                random_wait_func()

            # searching for the rows of jobs
            print('Extracting Table Elements')
            table = driver.find_element(By.ID,"search-results-list")
            rows = table.find_elements(By.TAG_NAME, 'li')

            # keeps a memory of the job posting
            job_postings = []

            # itterates though the list of job postings
            for row in rows:
                link_part = _safe_find_href(row,By.CSS_SELECTOR,'a')
                if not link_part:
                    continue

                job_postings.append({
                    "full_link": urljoin(BASE_URL, link_part),
                    "job_title": _safe_find_text(row, By.TAG_NAME, 'h2'),
                })

            # navigate into the job posting if a new link is found.
            for job in job_postings:
                full_link = job['full_link']

                if full_link in set_of_links:
                    print(f"repeated job posting found: {job['job_title']}, skipping...")
                    continue

                print(f"new job posting found: {job['job_title']}")
                if random_wait_func:
                    random_wait_func()

                # grabbing the date we aquried the job posting
                date_of_retrival = datetime.now().strftime("%Y-%m-%d")

                # opening the job posting for details
                print('opening job posting and extracting...')
                driver.get(full_link)
                if random_wait_func:
                    random_wait_func()
                if scroll_func:
                    scroll_func(driver)

                # aquring job metadata
                job_code = _safe_find_text(driver, By.CSS_SELECTOR, ".job-id.job-info")
                location = "4502 Medical Drive\nSan Antonio, Texas 78229"
                postion_type = _safe_find_text(driver, By.CSS_SELECTOR, ".job-schedule.job-info")
                posting_date_raw = _safe_find_text(driver, By.CSS_SELECTOR, ".job-date.job-info")
                posting_date = _normalize_posting_date(posting_date_raw)
                job_description = _extract_ats_description(driver)
                bandwidth_kb = _safe_bandwidth_kb(driver, network_performance_func)

                sql = '''
                INSERT INTO "UHEALTH DATA" (
                    "JOB TITLE",
                    "JOB CODE",
                    "LOCATION",
                    "DATE OF RETRIVAL",
                    "POSTING DATE",
                    "POSITION TYPE",
                    "JOB DESCRIPTION",
                    "BANDWIDTH",
                    "URL"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''

                try:
                    cursor.execute(
                        sql,
                        (
                            job["job_title"],
                            job_code,
                            location,
                            date_of_retrival,
                            posting_date,
                            postion_type,
                            job_description,
                            bandwidth_kb,
                            full_link,
                        ),
                    )
                    db_connection.commit()
                    set_of_links.add(full_link)
                except sqlite3.IntegrityError as e:
                    print(f"Database error (duplicate row): {e}")
                    set_of_links.add(full_link)
                except sqlite3.Error as e:
                    print(f"Database error while inserting UHealth row: {e}")

                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search-results-list"))
                )

            #here this will allow us to navigate to the next page
            current_marker = job_postings[0]["full_link"] if job_postings else None
            next_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination-paging a.next"))
            )
            next_href = next_link.get_attribute("href")
            next_classes = (next_link.get_attribute("class") or "").lower()

            if "disabled" in next_classes or not next_href:
                print("Reached last University Health results page.")
                last_page = True
                break

            if random_wait_func:
                random_wait_func()

            print("navigating to the next page")
            try:
                next_link.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", next_link)

            # Some pages update results via JS and keep the same top-level URL.
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: _first_job_link(d) != current_marker
                )
            except Exception:
                # Fallback: navigate directly to the next href when click does not refresh the list.
                driver.get(urljoin(BASE_URL, next_href))
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search-results-list"))
                )
    finally:
        db_connection.close()


def _first_job_link(driver):
    try:
        table = driver.find_element(By.ID, "search-results-list")
        row = table.find_element(By.TAG_NAME, "li")
        return _safe_find_href(row, By.CSS_SELECTOR, "a")
    except Exception:
        return None


def _extract_ats_description(driver):
    try:
        paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.ats-description p")
        cleaned = []
        for paragraph in paragraphs:
            text = paragraph.text.strip()
            if text:
                cleaned.append(text)
        return "\n\n".join(cleaned) if cleaned else None
    except Exception:
        return None


def _safe_bandwidth_kb(driver, network_performance_func):
    if not network_performance_func:
        return None
    try:
        return network_performance_func(driver)
    except Exception as e:
        print(f"Database error: failed to gather bandwidth: {e}")
        return None


def _normalize_posting_date(raw_value):
    if not raw_value:
        return None

    cleaned = " ".join(raw_value.replace("|", " ").split())
    cleaned = cleaned.replace("Post Date", "").replace("Posted", "")
    cleaned = cleaned.strip(" :-")
    cleaned = cleaned.replace(".", "")

    for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _ensure_uhealth_bandwidth_column(cursor, db_connection):
    try:
        cursor.execute('''PRAGMA table_info("UHEALTH DATA")''')
        columns = {row[1] for row in cursor.fetchall()}
        if "BANDWIDTH" not in columns:
            cursor.execute('''ALTER TABLE "UHEALTH DATA" ADD COLUMN "BANDWIDTH" INTEGER''')
            db_connection.commit()
    except sqlite3.Error as e:
        print(f"Database error: could not ensure BANDWIDTH column exists: {e}")


def _ensure_uhealth_url_unique_index(cursor, db_connection):
    try:
        cursor.execute('''DROP INDEX IF EXISTS uc_UHealth''')
        cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS uc_UHealth ON "UHEALTH DATA" ("URL")''')
        db_connection.commit()
    except sqlite3.Error as e:
        print(f"Database error: could not ensure URL unique index: {e}")
        

def _safe_find_href(parent, by, selector):
    try:
        value = parent.find_element(by, selector).get_attribute("href")
        return value.strip() if value else None
    except Exception:
        return None

def _safe_find_text(parent, by, selector):
    try:
        value = parent.find_element(by, selector).text
        return value.strip() if value is not None else None
    except Exception:
        return None