import random
import time
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

PROJECT_ROOT = Path(__file__).resolve().parent
SERVICE_PATH_FILE = PROJECT_ROOT / "service_path.txt"
HEADERS_FILE = PROJECT_ROOT / "request_headers.txt"
DEFAULT_CHROME_BINARY = "/usr/bin/chromium-browser"
DEFAULT_WINDOW_SIZE: Tuple[int, int] = (1920, 1080)
DEFAULT_PROFILE_DIR = PROJECT_ROOT / "chrome_profile"

# These are commonly managed by the browser/network stack and should not be forced.
BLOCKED_HEADER_NAMES = {
	"host",
	"content-length",
	"connection",
	"proxy-connection",
	"transfer-encoding",
	"te",
	"upgrade-insecure-requests",
	"accept-encoding",
	"via",
	"x-forwarded-for",
}


#--------------------- Connecting with the local database! ---------------------------------------
# we go ahead and build the file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'job_data.db')

# establish a connection with the database with query abilities
connection = sqlite3.connect(db_path)
cursor = connection.cursor()
#-----------------------------------------------------------------------------------------


def _seed_randomness() -> None:
	# Use the current timestamp so each run gets a slightly different pattern.
	seed_value = int(datetime.now().timestamp() * 1000)
	random.seed(seed_value)


_seed_randomness()


def get_service_config() -> tuple[str, Dict[str, str]]:
	if not SERVICE_PATH_FILE.exists():
		raise FileNotFoundError(
			f"Missing {SERVICE_PATH_FILE}. Add your chromedriver executable path to this file."
		)

	lines = SERVICE_PATH_FILE.read_text(encoding="utf-8").splitlines()
	chromedriver_path = ""
	headers: Dict[str, str] = {}

	for raw_line in lines:
		line = raw_line.strip()
		if not line or line.startswith("#"):
			continue

		if "=" not in line:
			if not chromedriver_path:
				chromedriver_path = line
			continue

		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip()

		if not value:
			continue

		if key == "CHROMEDRIVER_PATH":
			chromedriver_path = value
		else:
			headers[key] = value

	if not chromedriver_path:
		raise ValueError(
			f"{SERVICE_PATH_FILE} is missing CHROMEDRIVER_PATH. Add your chromedriver path."
		)

	return chromedriver_path, headers


def get_headers_from_file() -> Dict[str, str]:
	if not HEADERS_FILE.exists():
		return {}

	headers: Dict[str, str] = {}
	for raw_line in HEADERS_FILE.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#"):
			continue

		if ":" in line:
			key, value = line.split(":", 1)
		elif "=" in line:
			key, value = line.split("=", 1)
		else:
			continue

		key = key.strip()
		value = value.strip()
		if key and value:
			headers[key] = value

	return headers


def get_chromedriver_path() -> str:
	chromedriver_path, _ = get_service_config()
	return chromedriver_path


def get_default_headers() -> Dict[str, str]:
	headers = get_headers_from_file()
	if headers:
		return headers

	# Backward compatibility for older mixed service_path.txt format.
	_, fallback_headers = get_service_config()
	return fallback_headers


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
	cleaned: Dict[str, str] = {}
	for key, value in headers.items():
		lower_key = key.lower()

		# Avoid forcing browser-managed or fingerprint-critical fetch headers.
		if lower_key in BLOCKED_HEADER_NAMES or lower_key.startswith("sec-"):
			continue
		cleaned[key] = value
	return cleaned

def typing(input_text, section) -> None:
	print("Executing typing")
	for char in input_text:
		section.send_keys(char)
		time.sleep(round(random.uniform(0.080, 0.320), 3))


def random_wait(min_seconds: float = 0.5, max_seconds: float = 3.0) -> None:
	wait_time = round(random.uniform(min_seconds, max_seconds), 3)
	print(f"Waiting {wait_time:.3f} seconds...")
	time.sleep(wait_time)


def build_chrome_options(
	chrome_binary_location: str = DEFAULT_CHROME_BINARY,
	window_size: Optional[Tuple[int, int]] = DEFAULT_WINDOW_SIZE,
	user_data_dir: Optional[str] = None,
) -> Options:
	chrome_options = Options()
	chrome_options.binary_location = chrome_binary_location

	if window_size:
		chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")

	if user_data_dir:
		profile_path = Path(user_data_dir).expanduser().resolve()
		profile_path.mkdir(parents=True, exist_ok=True)
		chrome_options.add_argument(f"--user-data-dir={profile_path}")

	chrome_options.add_argument("--no-sandbox")
	chrome_options.add_argument("--disable-dev-shm-usage")
	chrome_options.add_argument("--disable-gpu")
	# Let Chrome choose an available debugging port to avoid stale port conflicts.
	chrome_options.add_argument("--remote-debugging-port=0")
	chrome_options.add_argument("--disable-blink-features=AutomationControlled")
	chrome_options.add_argument("--disable-images")
	chrome_options.add_argument("--disable-plugins")
	chrome_options.add_argument("--disable-extensions")
	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
	chrome_options.add_experimental_option("useAutomationExtension", False)
	return chrome_options


def apply_stealth_patches(driver: webdriver.Chrome) -> None:
	# Injects a preload script before page scripts run to mask obvious WebDriver signals.
	stealth_script = """
		Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

		Object.defineProperty(navigator, 'languages', {
			get: () => ['en-US', 'en']
		});

		Object.defineProperty(navigator, 'platform', {
			get: () => 'Linux x86_64'
		});

		const fakePlugins = [
			{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
			{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
			{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
		];

		Object.defineProperty(navigator, 'plugins', {
			get: () => fakePlugins
		});

		window.chrome = window.chrome || { runtime: {} };
	"""

	driver.execute_cdp_cmd(
		"Page.addScriptToEvaluateOnNewDocument",
		{"source": stealth_script},
	)


def apply_default_headers(driver: webdriver.Chrome, headers: Dict[str, str]) -> None:
	# Uses CDP-level default headers for future requests while skipping browser-managed fields.
	safe_headers = sanitize_headers(headers)
	if not safe_headers:
		return

	driver.execute_cdp_cmd("Network.enable", {})
	driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": safe_headers})


def safe_get(driver: webdriver.Chrome, url: str) -> None:
	random_wait()
	driver.get(url)
	random_wait()


def _is_bottom_of_page(driver: webdriver.Chrome, threshold: float = 0.98) -> bool:
	try:
		scroll_height = driver.execute_script(
			"return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight);"
		)
		viewport_height = driver.execute_script(
			"return window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;"
		)
		scroll_top = driver.execute_script(
			"return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;"
		)
		return (scroll_top + viewport_height) >= (scroll_height * threshold)
	except (InvalidSessionIdException, WebDriverException):
		return True


def _smooth_scroll(
	driver: webdriver.Chrome,
	direction: int,
	target_distance: int,
	pixels_per_second: int,
	step_delay_ms: int,
	max_steps: int,
) -> None:
	script = """
		const direction = arguments[0];
		const targetDistance = arguments[1];
		const pixelsPerSecond = arguments[2];
		const stepDelayMs = arguments[3];
		const maxSteps = arguments[4];
		const callback = arguments[arguments.length - 1];

		const startY = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
		const maxScrollY = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
		const targetY = direction > 0
			? Math.min(startY + targetDistance, maxScrollY)
			: Math.max(startY - targetDistance, 0);

		const distance = Math.max(0, Math.abs(targetY - startY));
		if (distance <= 1) {
			window.scrollTo(0, targetY);
			callback();
			return;
		}

		const duration = Math.max(300, Math.min(2500, (distance / pixelsPerSecond) * 1000));
		const startTime = performance.now();

		function tick(now) {
			const elapsed = now - startTime;
			const travelDistance = Math.min(distance, (elapsed / 1000) * pixelsPerSecond);
			const currentY = Math.round(startY + (direction > 0 ? travelDistance : -travelDistance));

			window.scrollTo(0, currentY);

			if (travelDistance < distance) {
				requestAnimationFrame(tick);
			} else {
				window.scrollTo(0, targetY);
				callback();
			}
		}

		requestAnimationFrame(tick);
	"""
	try:
		driver.execute_async_script(script, direction, target_distance, pixels_per_second, step_delay_ms, max_steps)
	except (InvalidSessionIdException, WebDriverException):
		pass


def scroll_page(
	driver: webdriver.Chrome,
	min_pause: float = 0.2,
	max_pause: float = 2.0,
	scroll_up_min: int = 3,
	scroll_up_max: int = 5
) -> None:
	# Keep scrolling smoothly until the bottom of the page is reached.
	bottom_of_page = False
	while not bottom_of_page:
		if _is_bottom_of_page(driver):
			bottom_of_page = True
			break

		step_delay_ms = 0
		target_distance = random.randint(500, 800)
		pixels_per_second = random.randint(3000, 4000)
		print('Scrolling now...')
		_smooth_scroll(
			driver,
			direction=1,
			target_distance=target_distance,
			pixels_per_second=pixels_per_second,
			step_delay_ms=step_delay_ms,
			max_steps=15,
		)
		random_wait(min_seconds=0.2, max_seconds=2)

		if _is_bottom_of_page(driver):
			bottom_of_page = True

	if bottom_of_page:
		random_up_scrolls = random.randint(scroll_up_min,scroll_up_max)
		print('The program will begin to scroll up now')
		for _ in range(random_up_scrolls):
			current_top = driver.execute_script(
				"return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;"
			)
			if current_top <= 0:
				break

			step_delay_ms = 0
			target_distance = random.randint(250, 700)
			pixels_per_second = random.randint(3001, 3999)
			_smooth_scroll(
				driver,
				direction=-1,
				target_distance=target_distance,
				pixels_per_second=pixels_per_second,
				step_delay_ms=step_delay_ms,
				max_steps=12,
			)
			random_wait(min_seconds=0.2, max_seconds=2)


def create_driver(
	extra_headers: Optional[Dict[str, str]] = None,
	user_data_dir: Optional[str] = str(DEFAULT_PROFILE_DIR),
	window_size: Optional[Tuple[int, int]] = DEFAULT_WINDOW_SIZE,
) -> webdriver.Chrome:
	service = Service(executable_path=get_chromedriver_path())
	driver = webdriver.Chrome(
		service=service,
		options=build_chrome_options(
			user_data_dir=user_data_dir,
			window_size=window_size,
		),
	)

	apply_stealth_patches(driver)

	if extra_headers is None:
		extra_headers = get_default_headers()

	if extra_headers:
		apply_default_headers(driver, extra_headers)

	return driver


def run_scraper(
	target_url: str,
	extra_headers: Optional[Dict[str, str]] = None,
) -> webdriver.Chrome:
	print("About to create driver...")
	driver = create_driver(extra_headers=extra_headers)
	print("Driver created, about to open URL...")
	safe_get(driver, target_url)
	return driver


if __name__ == "__main__":
	from website_scraper.wiki_test import run_wiki_test, wiki_url

	user_choice = input("Would you like to run the Wikipedia test? (Y/N) ").strip().upper()

	if user_choice == "Y":
		user_query = input("What do you want to search on Wikipedia? ").strip()
		if not user_query:
			user_query = "Selenium (software)"

		driver = run_scraper(wiki_url)
		result = run_wiki_test(
			driver,
			query=user_query,
			typing_func=typing,
			random_wait_func=random_wait,
			scroll_func=scroll_page,
		)
		print(f"Main orchestrator wiki test result: {result}")
		random_wait()
		print('Thank you for using wiki test...')
		random_wait()
		#driver.quit()
	else:
		print("Skipping Wikipedia test.")
