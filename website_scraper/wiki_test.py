import random
import time
from typing import Callable, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

wiki_url = "https://www.wikipedia.org/"


def run_wiki_test(
	driver,
	query: str = "Selenium (software)",
	typing_func: Optional[Callable[[str, object], None]] = None,
	random_wait_func: Optional[Callable[[], None]] = None,
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
		random_wait_func()
		print("Wikipedia test passed: search opened an article page.")
		return True
	except Exception as exc:
		print(f"Wikipedia test failed: {exc}")
		return False