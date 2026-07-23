import sqlite3
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

wiki_url = "https://www.wikipedia.org/"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WIKI_TEST_DB = PROJECT_ROOT / "job_data.db"


def log_wiki_test_run(page_title,db_path: Path = WIKI_TEST_DB,) -> None:
	now = datetime.now()
	run_date = now.strftime("%Y-%m-%d")
	run_time = now.strftime("%H:%M:%S")
	print('we stored the following information into the database:')
	print(f'Date of Execution: {run_date}')
	print(f'Time of Execution: {run_time}')
	print(f'Wiki Title Page: {page_title}')
	with sqlite3.connect(db_path) as conn:
		conn.execute(
			"INSERT OR IGNORE INTO \"wiki data\" (\"Date\", \"Time\", \"Page_Titles\") VALUES (?, ?, ?)",
			(run_date, run_time, page_title),
		)
		conn.commit()


def run_wiki_test(
	driver,
	query: str = "Selenium (software)",
	typing_func: Optional[Callable[[str, object], None]] = None,
	random_wait_func: Optional[Callable[[], None]] = None,
	scroll_func: Optional[Callable[[object], None]] = None,
) -> bool:
	print("Running Wikipedia site as an initial test...")

	try:
		wait = WebDriverWait(driver, 20)

		if random_wait_func:
			random_wait_func()
		else:
			delay = random.uniform(3, 5)
			time.sleep(delay)
			print(f"Waiting {delay:.1f} seconds to mimic human pacing.")

		print("Searching for the Wikipedia search bar...")
		search_input = wait.until(EC.element_to_be_clickable((By.ID, "searchInput")))
		search_input.clear()

		if typing_func:
			typing_func(query, search_input)
		else:
			search_input.send_keys(query)

		search_input.submit()

		wait.until(EC.url_contains("/wiki/"))
		if random_wait_func:
			random_wait_func()

		if scroll_func:
			scroll_func(driver)

		title_element = wait.until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "#firstHeading .mw-page-title-main"))
		)
		page_title = title_element.text.strip() or driver.title
		log_wiki_test_run(page_title)
		print("Wikipedia test passed: search opened an article page.")
		return True
	except Exception as exc:
		print(f"Wikipedia test failed: {exc}")
		return False