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


def get_visible_wiki_links(driver) -> list:
	visible_links = []
	for anchor in driver.find_elements(By.CSS_SELECTOR, "a[rel='mw:WikiLink'][href]"):
		try:
			if not anchor.is_displayed():
				continue
			rel_value = (anchor.get_attribute("rel") or "").strip()
			if rel_value != "mw:WikiLink":
				continue
			href = (anchor.get_attribute("href") or "").strip()
			if not href or href.startswith("javascript:"):
				continue
			visible_links.append(anchor)
		except Exception:
			continue
	return visible_links


def get_current_wiki_article_title(driver) -> str:
	try:
		title_element = WebDriverWait(driver, 8).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, "#firstHeading .mw-page-title-main"))
		)
		return title_element.text.strip() or driver.title or driver.current_url
	except Exception:
		fallback_title = (driver.title or "").strip()
		return fallback_title or driver.current_url


def click_random_visible_wiki_link(
	driver,
	wait: WebDriverWait,
	random_wait_func: Optional[Callable[[], None]] = None,
	max_attempts: int = 6,
) -> bool:
	for _ in range(max_attempts):
		visible_links = get_visible_wiki_links(driver)
		if not visible_links:
			return False

		candidate = random.choice(visible_links)
		before_url = driver.current_url
		try:
			driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", candidate)
			driver.execute_script("arguments[0].click();", candidate)
		except Exception:
			continue

		try:
			wait.until(lambda d: d.current_url != before_url)
		except Exception:
			continue

		page_title = get_current_wiki_article_title(driver)
		log_wiki_test_run(page_title)

		if random_wait_func:
			random_wait_func()
		return True

	return False


def run_wiki_test(
	driver,
	query: str = "Selenium (software)",
	typing_func: Optional[Callable[[str, object], None]] = None,
	random_wait_func: Optional[Callable[[], None]] = None,
	scroll_func: Optional[Callable[[object], None]] = None,
	min_repeats: int = 3,
	max_repeats: int = 7,
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

		# Log the initial article opened from the search.
		initial_title = get_current_wiki_article_title(driver)
		log_wiki_test_run(initial_title)

		repeat_count = random.randint(min_repeats, max_repeats)
		print(f"This session will repeat the scroll and click flow {repeat_count} time(s).")

		for step in range(repeat_count):
			if scroll_func:
				scroll_func(driver)

			clicked = click_random_visible_wiki_link(
				driver,
				wait,
				random_wait_func=random_wait_func,
			)
			if not clicked:
				print(f"Step {step + 1}: no clickable visible wiki links found, stopping early.")
				break

		print("Wikipedia test passed: search opened an article page.")
		return True
	except Exception as exc:
		print(f"Wikipedia test failed: {exc}")
		return False