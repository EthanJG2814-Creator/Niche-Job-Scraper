import random
import time
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


def human_pause(min_s: float = 0.8, max_s: float = 2.4) -> None:
	time.sleep(random.uniform(min_s, max_s))


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
	human_pause(0.5, 1.6)
	driver.get(url)
	human_pause(1.0, 2.2)


def scroll_page(driver: webdriver.Chrome, min_scrolls: int = 2, max_scrolls: int = 5) -> None:
	scrolls = random.randint(min_scrolls, max_scrolls)
	for _ in range(scrolls):
		step = random.randint(300, 900)
		try:
			driver.execute_script("window.scrollBy(0, arguments[0]);", step)
		except (InvalidSessionIdException, WebDriverException):
			# If the browser process drops, skip warm behavior instead of crashing the run.
			break
		human_pause(0.4, 1.3)


def warm_page(driver: webdriver.Chrome) -> None:
	human_pause(0.8, 1.8)
	scroll_page(driver)
	human_pause(1.0, 2.0)


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


def run_scraper(target_url: str,extra_headers: Optional[Dict[str, str]] = None,) -> webdriver.Chrome:
	print("About to create driver...")
	driver = create_driver(extra_headers=extra_headers)
	print("Driver created, about to open URL...")
	safe_get(driver, target_url)
	warm_page(driver)
	return driver


if __name__ == "__main__":
	from website_scraper.USAJOBS import TARGET_URL
	from website_scraper.wiki_test import wiki_url

	run_scraper(wiki_url)
