from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import MaxRetryError

class Player:
    def __init__(self):
        self.name = ""
        self.status = ""
        self.desc = ""

desc_list = [
    "not probable",
    "probable to miss",
    "probable to play",
    "probable",
    "unlikely to miss",
    "unlikely to play",
    "unlikely",
    "not likely",
    "likely to miss",
    "likely to play",
    "likely",
    "not expected to play",
    "not expected to miss",
    "not expected",
    "expected to play",
    "expected to miss",
    "possible",
    "question mark",
    "questionable",
    "doubtful"
]

likely_list = [
    "[Probable]",
    "[Probable to play]",
    "[Unlikely to miss]",
    "[Likely]",
    "[Likely to play]",
    "[Not expected to miss]",
    "[Expected to play]",
    "[Possible]",
    "[Questionable]"
]

unlikely_list = [
    "[Not probable]",
    "[Probable to miss]",
    "[Unlikely to play]",
    "[Unlikely]",
    "[Not likely]",
    "[Likely to miss]",
    "[Expected to miss]",
    "[Not expected to play]",
    "[Not expected]",
    "[Doubtful]"
]

def get_injuries():
    URL = "https://www.espn.com/nba/injuries"
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--diable-dve-shm-uage")
    options.add_argument('--deny-permission-prompts')

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        wait = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Card')))
    except TimeoutException:
        try:
            driver.refresh()
            wait = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Card')))
        except TimeoutException:
            driver.quit()
        except WebDriverException:
            driver.quit()
        except MaxRetryError:
            driver.quit()
    except WebDriverException:
        driver.quit()

    driver.execute_script('window.stop();')
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    results = soup.find(class_="Card")
    teams = results.find_all(class_="Table__TR Table__TR--sm Table__even")

    injury_list = []

    for players in teams:
        p = Player()
        p.name = players.find("a", class_="AnchorLink").text
        p.status = players.find(class_="TextStatus").text
        desc = players.find(class_="col-desc").text.lower()
        for x in desc_list:
            if x in desc:
                p.desc = "[" + x.capitalize() + "]"
                break
        injury_list.append(p)
    
    return injury_list

def is_playing(name, injuries):
    for obj in injuries:
        if name == obj.name:
            if obj.status == 'Out' and obj.desc not in likely_list:
                return False
            elif obj.status != 'Out' and obj.desc in unlikely_list:
                return False
    return True

injuries = get_injuries()
print(is_playing('Lebron James', injuries))