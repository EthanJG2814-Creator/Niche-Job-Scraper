import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "job_data.db"
USAJOBS_BASE_URL = "https://www.usajobs.gov"


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


def _wait(random_wait_func, min_seconds: float = 0.5, max_seconds: float = 3.0):
	if random_wait_func:
		try:
			random_wait_func(min_seconds, max_seconds)
			return
		except TypeError:
			pass
	time.sleep((min_seconds + max_seconds) / 2.0)


def _normalize_date(raw_date: Optional[str]) -> Optional[str]:
	if not raw_date:
		return None
	try:
		return datetime.strptime(raw_date.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
	except ValueError:
		return None


def _extract_job_code_from_url(url: str) -> Optional[str]:
	match = re.search(r"/job/(\d+)", url or "")
	return match.group(1) if match else None


def _extract_posting_end_date(card) -> Optional[str]:
	date_line = _safe_find_text(card, By.CSS_SELECTOR, "div.mt-2.italic span")
	match = re.search(r"to\s+(\d{2}/\d{2}/\d{4})", date_line or "")
	return _normalize_date(match.group(1) if match else None)


def _extract_location(card) -> Optional[str]:
	for block in card.find_elements(By.CSS_SELECTOR, "div.flex.items-center"):
		text = (block.text or "").strip()
		if text and not ("open" in text.lower() and " to " in text.lower()):
			return text
	return None


def _extract_position_type(card, location_text: Optional[str]) -> Optional[str]:
	labels = []
	if location_text and "remote" in location_text.lower():
		labels.append("Remote")
	for badge in card.find_elements(By.CSS_SELECTOR, "span.badge.badge-secondary"):
		value = (badge.text or "").strip().lower()
		if "full-time" in value and "Full-time" not in labels:
			labels.append("Full-time")
		if "part-time" in value and "Part-time" not in labels:
			labels.append("Part-time")
	return ", ".join(labels) if labels else None


def _first_job_link(driver) -> Optional[str]:
	return _safe_find_href(driver, By.CSS_SELECTOR, "#search-results h2 a[href]")


def _extract_section_text(driver, section_id: str) -> Optional[str]:
	try:
		section = driver.find_element(By.ID, section_id)
		text = (driver.execute_script("return arguments[0].innerText;", section) or "").strip()
		return text if text else None
	except Exception:
		return None


def _extract_control_number(driver) -> Optional[str]:
	try:
		value = driver.find_element(
			By.XPATH,
			"//dt[normalize-space()='Control number']/following-sibling::dd[1]"
		).text
		return value.strip() if value else None
	except Exception:
		return None


def _extract_job_description(driver) -> Optional[str]:
	parts = []
	for section_id, label in (
		("joa-summary", "Summary"),
		("joa-duties", "Duties"),
		("joa-requirements", "Requirements"),
	):
		text = _extract_section_text(driver, section_id)
		if text:
			parts.append(f"{label}\n{text}")
	return "\n\n".join(parts) if parts else None


def _extract_cards(driver):
	sections = driver.find_elements(By.CSS_SELECTOR, "#search-results div.page-section")
	return [s for s in sections if _safe_find_href(s, By.CSS_SELECTOR, "h2 a[href]")]


def _next_button(driver):
	try:
		return driver.find_element(By.CSS_SELECTOR, "#search-results-pagination button#page-n-next")
	except Exception:
		return None


def _is_disabled(button) -> bool:
	if button is None:
		return True
	classes = (button.get_attribute("class") or "").lower()
	return (
		button.get_attribute("disabled") is not None
		or (button.get_attribute("aria-disabled") or "").lower() == "true"
		or "disabled" in classes
	)


def _ensure_table(cursor, db_connection):
	cursor.execute(
		'''
		CREATE TABLE IF NOT EXISTS "USAJOBS DATA" (
			"ID" INTEGER PRIMARY KEY AUTOINCREMENT,
			"JOB TITLE" TEXT,
			"JOB CODE" TEXT,
			"LOCATION" TEXT,
			"POSITION TYPE" TEXT,
			"DATE OF RETRIVAL" DATE,
			"POSTING END DATE" DATE,
			"JOB DESCRIPTION" TEXT,
			"URL" TEXT,
			"BANDWIDTH" INTEGER
		)
		'''
	)
	cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS uc_USAJOBS_URL ON "USAJOBS DATA" ("URL")''')
	cursor.execute(
		'''
		CREATE UNIQUE INDEX IF NOT EXISTS uc_USAJOBS_JOBCODE
		ON "USAJOBS DATA" ("JOB CODE")
		WHERE "JOB CODE" IS NOT NULL AND TRIM("JOB CODE") <> ''
		'''
	)
	db_connection.commit()


def _seen_sets(cursor):
	cursor.execute('''SELECT "URL" FROM "USAJOBS DATA"''')
	seen_links = {row[0] for row in cursor.fetchall() if row and row[0]}
	cursor.execute('''SELECT "JOB CODE" FROM "USAJOBS DATA"''')
	seen_codes = {row[0] for row in cursor.fetchall() if row and row[0]}
	return seen_links, seen_codes


def _insert_job(cursor, db_connection, row):
	sql = '''
	INSERT INTO "USAJOBS DATA" (
		"JOB TITLE", "JOB CODE", "LOCATION", "POSITION TYPE", "DATE OF RETRIVAL",
		"POSTING END DATE", "JOB DESCRIPTION", "URL", "BANDWIDTH"
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	'''
	try:
		cursor.execute(
			sql,
			(
				row["job_title"], row["job_code"], row["location"], row["position_type"],
				row["date_of_retrieval"], row["posting_end_date"], row["job_description"],
				row["url"], row["bandwidth_kb"],
			),
		)
		db_connection.commit()
		return True
	except sqlite3.IntegrityError as e:
		print(f"Database error (duplicate row): {e}")
		db_connection.rollback()
		return False
	except sqlite3.Error as e:
		print(f"Database error while inserting USAJOBS row: {e}")
		db_connection.rollback()
		return False


def _extract_listing_item(card):
	relative = _safe_find_href(card, By.CSS_SELECTOR, "h2 a[href]")
	if not relative:
		return None
	url = urljoin(USAJOBS_BASE_URL, relative)
	location = _extract_location(card)
	return {
		"job_title": _safe_find_text(card, By.CSS_SELECTOR, "h2 a[href]"),
		"job_code": _extract_job_code_from_url(url),
		"location": location,
		"position_type": _extract_position_type(card, location),
		"date_of_retrieval": datetime.now().strftime("%Y-%m-%d"),
		"posting_end_date": _extract_posting_end_date(card),
		"url": url,
	}


def _extract_detail_item(driver, base_item, random_wait_func, scroll_func, network_performance_func):
	driver.get(base_item["url"])
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main#main_content")))
	if scroll_func:
		scroll_func(driver)
	_wait(random_wait_func, 9.5, 10.5)

	resolved_code = _extract_control_number(driver) or base_item["job_code"]
	bandwidth_kb = None
	if network_performance_func:
		try:
			bandwidth_kb = network_performance_func(driver)
		except Exception as exc:
			print(f"Bandwidth collection error: {exc}")

	row = dict(base_item)
	row["job_code"] = resolved_code
	row["job_description"] = _extract_job_description(driver)
	row["bandwidth_kb"] = bandwidth_kb
	return row


def _back_to_results(driver, random_wait_func):
	driver.back()
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search-results")))
	_wait(random_wait_func, 4.5, 5.5)


def _go_next_page(driver, random_wait_func):
	current_marker = _first_job_link(driver)
	button = _next_button(driver)
	if _is_disabled(button):
		return False
	_wait(random_wait_func)
	try:
		button.click()
	except ElementClickInterceptedException:
		driver.execute_script("arguments[0].click();", button)
	try:
		WebDriverWait(driver, 10).until(lambda d: _first_job_link(d) not in (None, current_marker))
		return True
	except TimeoutException:
		print("Next page did not refresh in time; stopping pagination.")
		return False


def USAJOBS_MAIN(
	driver,
	typing_func: Optional[Callable[[str, object], None]] = None,
	random_wait_func: Optional[Callable[[], None]] = None,
	scroll_func: Optional[Callable[[object], None]] = None,
	network_performance_func: Optional[Callable[[object], int]] = None,
	min_repeats: int = 3,
	max_repeats: int = 7,
) -> bool:
	print("Running USAJOBS site...")

	db_connection = sqlite3.connect(DB_PATH)
	cursor = db_connection.cursor()
	_ensure_table(cursor, db_connection)
	seen_links, seen_job_codes = _seen_sets(cursor)

	page_num = 1
	try:
		while True:
			if scroll_func:
				scroll_func(driver)
			_wait(random_wait_func)

			cards = _extract_cards(driver)
			print(f"USAJOBS listing page {page_num}: found {len(cards)} cards")

			for card in cards:
				listing_item = _extract_listing_item(card)
				if not listing_item:
					continue

				if listing_item["url"] in seen_links:
					print(f"[DUPLICATE_IN_DB_URL] {listing_item['job_title']}")
					continue

				if listing_item["job_code"] and listing_item["job_code"] in seen_job_codes:
					print(f"[DUPLICATE_IN_DB_JOBCODE] {listing_item['job_title']} ({listing_item['job_code']})")
					continue

				print(f"Opening job card: {listing_item['job_title']}")
				detail_item = _extract_detail_item(
					driver,
					listing_item,
					random_wait_func=random_wait_func,
					scroll_func=scroll_func,
					network_performance_func=network_performance_func,
				)

				if detail_item["job_code"] and detail_item["job_code"] in seen_job_codes:
					print(f"[DUPLICATE_AFTER_DETAIL_JOBCODE] {detail_item['job_title']} ({detail_item['job_code']})")
					_back_to_results(driver, random_wait_func)
					continue

				inserted = _insert_job(cursor, db_connection, detail_item)
				if inserted:
					seen_links.add(detail_item["url"])
					if detail_item["job_code"]:
						seen_job_codes.add(detail_item["job_code"])
					print("[INSERTED]")
					print(f"  Title: {detail_item['job_title']}")
					print(f"  Job Code: {detail_item['job_code']}")
					print(f"  Location: {detail_item['location']}")
					print(f"  Position Type: {detail_item['position_type']}")
					print(f"  Date Retrieved: {detail_item['date_of_retrieval']}")
					print(f"  Posting End Date: {detail_item['posting_end_date']}")
					print(f"  Bandwidth (kB): {detail_item['bandwidth_kb']}")
					print(f"  URL: {detail_item['url']}")

				_back_to_results(driver, random_wait_func)

			if not _go_next_page(driver, random_wait_func):
				print("Reached last USAJOBS results page.")
				break
			page_num += 1
		return True
	except Exception as exc:
		print(f"USAJOBS Program failed: {exc}")
		return False
	finally:
		db_connection.close()