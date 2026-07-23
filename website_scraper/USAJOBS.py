TARGET_URL = "https://www.usajobs.gov/"


if __name__ == "__main__":
    try:
        from main import run_scraper
    except ModuleNotFoundError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from main import run_scraper

    run_scraper(TARGET_URL)
