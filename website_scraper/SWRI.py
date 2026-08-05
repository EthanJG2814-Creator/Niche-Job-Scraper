import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from selenium.webdriver.common.by import By


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SWRI_Path = PROJECT_ROOT / "job_data.db"

#------ Basic Set up above --------


def extracting_info(driver,random_wait_func,network_performance_func,scroll_func):
    # finds the specific table
    table = driver.find_element(By.ID, "tblHistory")
    rows = table.find_elements(By.TAG_NAME, 'a')
    cached_rows = []

    for row in rows:
        cached_rows.append(
            {
                "job_cd": row.get_attribute('job_cd'),
                "job_title": row.get_attribute('job_title'),
                "link": row.get_attribute('href'),
                "location": row.get_attribute('work_location'),
            }
        )

    for row_data in cached_rows:
        # Extracting Job information
        job_cd = row_data["job_cd"]
        job_title = row_data["job_title"]
        link = row_data["link"]
        location = row_data["location"]
        date = datetime.now().strftime("%Y-%m-%d")
        bandwidth = network_performance_func(driver)

        # waiting before clicking next link
        random_wait_func()
        driver.get(link)

        # extracting specific job posting data
        random_wait_func()
        scroll_func(driver)
        description = driver.find_element(By.ID, "divJobDescription2")
        who_we_are = description.find_element(By.ID, "divWhoWeAre").text        
        objectives = description.find_element(By.ID, "divObjectivesOfThisRole").text.replace("\n", " ")
        daily_responsibilities = description.find_element(By.ID, "divDailyAndMonthlyResponsibilities").text.replace("\n", " ")
        requirements = description.find_element(By.ID, "divSkillsAndQualifications").text.replace("\n", " ")

        # connecting to the database
        connection = sqlite3.connect(SWRI_Path)
        cursor = connection.cursor()

        # storing values to the database
        sql = '''
        INSERT INTO "SWRI DATA" (
        "JOB TITLE",
        "JOB CODE",
        "DATE OF RETRIVAL",
        "NETWORK_PERFORMANCE",
        "WHO WE ARE",
        "OBJECTIVES OF THIS ROLE",
        "DAILY RESPONSIBILITIES",
        "REQUIREMENTS",
        "LOCATION",
        "URL") VALUES (?,?,?,?,?,?,?,?,?,?)
        '''
        try:
            cursor.execute(sql,(
                job_title,
                job_cd,
                date,
                bandwidth,
                who_we_are,
                objectives,
                daily_responsibilities,
                requirements,
                location,
                link
            ))
            connection.commit()
        except sqlite3.Error as e:
            print(f"DB error: {e}")
            print(f'we will continue to move on and log this error.')

        connection.close()
        # we will return to the previous page
        driver.back()




#---- Main Execution -----
def SWRI_MAIN(driver,
    typing_func: Optional[Callable[[str, object], None]] = None,
    random_wait_func: Optional[Callable[[], None]] = None,
    scroll_func: Optional[Callable[[object], None]] = None,
    network_performance_func: Optional[Callable[[object], int]] = None,
    min_repeats: int = 3,
    max_repeats: int = 7,
) -> bool:
    print("Running SWRI site...")

    try:
        # Extracting page values
        scroll_func(driver)
        extracting_info(driver,random_wait_func=random_wait_func,network_performance_func=network_performance_func,scroll_func=scroll_func)
            
    except Exception as exc:
        print(f"SWRI PRogram Failed failed: {exc}")
        return False