from datetime import datetime
import re
import requests
import pandas as pd
import sqlite3
from .Dictionaries import team_index_current
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import MaxRetryError

games_header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.133 Safari/537.36',
    'Dnt': '1',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en',
    'origin': 'http://stats.nba.com',
    'Referer': 'https://github.com'
}

data_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive'
}



def get_json_data(url):
    raw_data = requests.get(url, headers=data_headers)
    try:
        json = raw_data.json()
    except Exception as e:
        print(e)
        return {}
    return json.get('resultSets')


def get_todays_games_json(url):
    raw_data = requests.get(url, headers=games_header)
    json = raw_data.json()
    return json.get('gs').get('g')


def to_data_frame(data):
    try:
        data_list = data[0]
    except Exception as e:
        print(e)
        return pd.DataFrame(data={})
    return pd.DataFrame(data=data_list.get('rowSet'), columns=data_list.get('headers'))


def create_todays_games(input_list):
    games = []
    for game in input_list:
        home = game.get('h')
        away = game.get('v')
        home_team = home.get('tc') + ' ' + home.get('tn')
        away_team = away.get('tc') + ' ' + away.get('tn')
        games.append([home_team, away_team])
    return games


def create_todays_games_from_odds(input_dict):
    games = []
    for game in input_dict.keys():
        home_team, away_team = game.split(":")
        if home_team not in team_index_current or away_team not in team_index_current:
            continue
        games.append([home_team, away_team])
    return games

def get_date(date_string):
    year1,month,day = re.search(r'(\d+)-\d+-(\d\d)(\d\d)', date_string).groups()
    year = year1 if int(month) > 8 else int(year1) + 1
    return datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')

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
    "doubtful",
    "ruled out",
    "unavailable"
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
    "[Doubtful]",
    "[Ruled out]",
    "[Unavailable]"
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
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Card')))
    except TimeoutException:
        try:
            driver.refresh()
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Card')))
        except TimeoutException:
            print('Get Injuries Error')
            driver.quit()
            return []
        except WebDriverException:
            print('Get Injuries Error')
            driver.quit()
            return []
        except MaxRetryError:
            print('Get Injuries Error')
            driver.quit()
            return []
    except WebDriverException:
        print('Get Injuries Error')
        driver.quit()
        return []

    teams = driver.find_elements(By.CLASS_NAME, 'Table__league-injuries')

    injury_list = []

    for team in teams:
        body = team.find_element(By.CLASS_NAME, 'Table__TBODY')
        players = body.find_elements(By.TAG_NAME, 'tr')

        for player in players:
            p = Player()
            p.name = player.find_element(By.TAG_NAME, 'a').text
            p.status = player.find_element(By.CLASS_NAME, 'TextStatus').text
            desc = player.find_element(By.CLASS_NAME, 'col-desc').text.lower()
            for x in desc_list:
                if x in desc:
                    p.desc = "[" + x.capitalize() + "]"
                    break
            injury_list.append(p)

    driver.quit()
    
    return injury_list

def is_playing(name, injuries):
    for obj in injuries:
        if name == obj.name:
            if obj.status == 'Out' and obj.desc not in likely_list:
                return False
            elif obj.status != 'Out' and obj.desc in unlikely_list:
                return False
    return True

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

team_dict_cbs = {
    "Boston Celtics" : "BOS",
    "Brooklyn Nets" : "BRK",
    "New York Knicks" : "NYK",
    "Philadelphia 76ers" : "PHI",
    "Toronto Raptors" : "TOR",
    "Chicago Bulls" : "CHI",
    "Cleveland Cavaliers" : "CLE",
    "Detroit Pistons" : "DET",
    "Indiana Pacers" : "IND",
    "Milwaukee Bucks" : "MIL",
    "Atlanta Hawks" : "ATL",
    "Charlotte Hornets" : "CHA",
    "Miami Heat" : "MIA",
    "Orlando Magic" : "ORL",
    "Washington Wizards" : "WAS",
    "Denver Nuggets" : "DEN",
    "Minnesota Timberwolves" : "MIN",
    "Oklahoma City Thunder" : "OKC",
    "Portland Trail Blazers" : "POR",
    "Utah Jazz" : "UTA",
    "Golden State Warriors" : "GSW",
    "LA Clippers" : "LAC",
    "Los Angeles Lakers" : "LAL",
    "Phoenix Suns" : "PHO",
    "Sacramento Kings" : "SAC",
    "Dallas Mavericks" : "DAL",
    "Houston Rockets" : "HOU",
    "Memphis Grizzlies" : "MEM",
    "New Orleans Pelicans" : "NOP",
    "San Antonio Spurs" : "SAS"
}

def get_pie(team, injury_list=None):
    # Get current injury status of all players if not provided
    if injury_list == None:
        injury_list = get_injuries()

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
            print('Get PIE Error:', team)
            driver.quit()
            return
        except WebDriverException:
            print('Get PIE Error:', team)
            driver.quit()
            return
        except MaxRetryError:
            print('Get PIE Error:', team)
            driver.quit()
            return
    except WebDriverException:
        print('Get PIE Error:', team)
        driver.quit()
        return

    results = driver.find_elements(By.CLASS_NAME, 'Crom_body__UYOcU')
    players = results[1].find_elements(By.TAG_NAME, 'tr')

    pie = pie_w = min_p = net = pace = player_count = 0
    player_list = []
    roster = get_roster(team)

    for p in players:
        stats = p.find_elements(By.TAG_NAME, 'td')
        name = stats[0].text

        if is_playing(name, injury_list) and name in roster:
            player_list.append(name)
            pie += float(stats[-1].text)
            pie_w += float(stats[-1].text) * float(stats[2].text)
            min_p += float(stats[2].text)
            net += float(stats[5].text)
            pace += float(stats[-2].text)

            player_count += 1

        if player_count == 8: break

    pie /= player_count
    pie_w /= min_p
    min_p /= player_count
    net /= player_count
    pace /= player_count

    driver.quit()

    return pie, pie_w, min_p, net, pace

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
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
    except TimeoutException:
        try:
            driver.refresh()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
        except Exception as e:
            print('Get Roster Error:', team)
            # print(e)
            driver.quit()
            return get_roster2(team)
    except Exception as e:
        print('Get Roster Error:', team)
        # print(e)
        driver.quit()
        return get_roster2(team)

    results = driver.find_element(By.CLASS_NAME, 'Crom_body__UYOcU')
    players = results.find_elements(By.TAG_NAME, 'tr')

    roster = []

    for p in players:
        roster.append(p.find_element(By.TAG_NAME, 'td').text)
    
    driver.quit()

    return roster

def get_roster2(team):
    dashed_team = team.replace(' ', '-') if team != 'LA Clippers' else 'Los Angeles Clippers'
    URL = f'https://www.cbssports.com/nba/teams/{team_dict_cbs[team]}/{dashed_team.lower()}/roster/'

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
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'TableBase-table')))
    except TimeoutException:
        try:
            driver.refresh()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'TableBase-table')))
        except Exception as e:
            print('Get Roster Error:', team)
            # print(e)
            driver.quit()
            return
    except Exception as e:
        print('Get Roster Error:', team)
        # print(e)
        driver.quit()
        return

    players = driver.find_elements(By.CLASS_NAME, 'CellPlayerName--long')

    roster = []

    for p in players:
        roster.append(p.text)
    
    driver.quit()

    return roster

def add_to_results(date, home_team, away_team, home_odds, away_odds, home_percent, away_percent, home_ev, away_ev, bet_type, bet):
    con = sqlite3.connect('Data/results.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    found = False

    for row in dataset.execute("""SELECT `Date`, `Home_Team`, `Bet_Type`, `Bet` FROM `Picks`"""):
        if row[0] == date and row[1] == home_team and row[2] == bet_type:
            cur.execute(f"""UPDATE `Picks` SET `Home_Odds` = '{home_odds}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Away_Odds` = '{away_odds}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Home_Percent` = '{format(home_percent, '.3f')}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Away_Percent` = '{format(away_percent, '.3f')}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Home_EV` = '{format(home_ev, '.2f')}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Away_EV` = '{format(away_ev, '.2f')}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            cur.execute(f"""UPDATE `Picks` SET `Bet` = '{bet}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[2]}'""")
            con.commit()
            found = True
            break

    if not found:
        cur.execute(f"""INSERT INTO `Picks` (`Date`, `Home_Team`, `Away_Team`, `Home_Odds`, `Away_Odds`, `Home_Percent`, `Away_Percent`, `Home_EV`, `Away_EV`, `Bet_Type`, `Bet`) VALUES ('{date}', '{home_team}', '{away_team}', '{home_odds}', '{away_odds}', '{format(home_percent, '.3f')}', '{format(away_percent, '.3f')}', '{format(home_ev, '.2f')}', '{format(away_ev, '.2f')}', '{bet_type}', '{bet}')""")
        con.commit()

    dataset.close()
    cur.close()
    con.close()
