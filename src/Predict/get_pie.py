import get_injuries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import MaxRetryError

team_dict = {
    "Boston Celtics" : "1610612738",
    "Brooklyn Nets" : "1610612751",
    "New York Knicks" : "1610612752",
    "Philadelphia 76ers" : "1610612755",
    "Toronto Raptors" : "1610612761",
    "Chicago Bulls" : "1610612741",
    "Cleveland Cavaliers" : "1610612739",
    "Detroit Pistons" : "1610612765",
    "Indiana Pacers" : "1610612754",
    "Milwaukee Bucks" : "1610612749",
    "Atlanta Hawks" : "1610612737",
    "Charlotte Hornets" : "1610612766",
    "Charlotte Bobcats" : "1610612766",
    "Miami Heat" : "1610612748",
    "Orlando Magic" : "1610612753",
    "Washington Wizards" : "1610612764",
    "Denver Nuggets" : "1610612743",
    "Minnesota Timberwolves" : "1610612750",
    "Oklahoma City Thunder" : "1610612760",
    "Portland Trail Blazers" : "1610612757",
    "Utah Jazz" : "1610612762",
    "Golden State Warriors" : "1610612744",
    "Los Angeles Clippers" : "1610612746",
    "LA Clippers" : "1610612746",
    "Los Angeles Lakers" : "1610612747",
    "Phoenix Suns" : "1610612756",
    "Sacramento Kings" : "1610612758",
    "Dallas Mavericks" : "1610612742",
    "Houston Rockets" : "1610612745",
    "Memphis Grizzlies" : "1610612763",
    "New Orleans Pelicans" : "1610612740",
    "New Orleans Hornets" : "1610612740",
    "San Antonio Spurs" : "1610612759"
}

def get_pie(team, injury_list=None):
    # Get current injury status of all players if not provided
    if injury_list == None:
        injury_list = get_injuries.get_injuries()

    URL = 'https://www.nba.com/stats/team/' + team_dict[team] + '/players-advanced?dir=D&sort=MIN'
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--diable-dve-shm-uage")
    options.add_argument('--deny-permission-prompts')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
    except TimeoutException:
        try:
            driver.refresh()
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
        except TimeoutException:
            driver.quit()
            return
        except WebDriverException:
            driver.quit()
            return
        except MaxRetryError:
            driver.quit()
            return
    except WebDriverException:
        driver.quit()
        return

    results = driver.find_elements(By.CLASS_NAME, 'Crom_body__UYOcU')
    players = results[1].find_elements(By.TAG_NAME, 'tr')

    pie = 0
    pie_w = 0
    total_minutes = 0
    player_count = 8
    player_list = []
    roster = get_roster(team)

    for p in players:
        if player_count == 0: break

        stats = p.find_elements(By.TAG_NAME, 'td')
        name = stats[0].text

        if get_injuries.is_playing(name, injury_list) and name in roster:
            player_list.append(name)
            pie += float(stats[-1].text)
            pie_w += float(stats[-1].text) * float(stats[2].text)
            total_minutes += float(stats[2].text)
            player_count -= 1

    pie_w /= total_minutes

    driver.quit()

    return pie, pie_w

def get_roster(team):
    URL = 'https://www.nba.com/stats/team/' + team_dict[team]

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--diable-dve-shm-uage")
    options.add_argument('--deny-permission-prompts')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
    except TimeoutException:
        try:
            driver.refresh()
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
        except TimeoutException:
            driver.quit()
            return
        except WebDriverException:
            driver.quit()
            return
        except MaxRetryError:
            driver.quit()
            return
    except WebDriverException:
        driver.quit()
        return

    results = driver.find_element(By.CLASS_NAME, 'Crom_body__UYOcU')
    players = results.find_elements(By.TAG_NAME, 'tr')

    roster = []

    for p in players:
        roster.append(p.find_element(By.TAG_NAME, 'td').text)

    return roster

# pie, pie_w = get_pie('Boston Celtics', get_injuries.get_injuries())
# print(f"""{format(pie, '.1f')}, {format(pie_w, '.1f')}""")
