import sqlite3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from sbrscrape import Scoreboard
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

data_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive'
}

month_dict = {
    1 : 31,
    2 : 28,
    3 : 31,
    4 : 30,
    5 : 31,
    6 : 30,
    7 : 31,
    8 : 31,
    9 : 30,
    10 : 31,
    11 : 30,
    12 : 31
}

month_dict_leap = {
    1 : 31,
    2 : 29,
    3 : 31,
    4 : 30,
    5 : 31,
    6 : 30,
    7 : 31,
    8 : 31,
    9 : 30,
    10 : 31,
    11 : 30,
    12 : 31
}

def add_games(init=False):
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()

    if init:
        year = start_date[0]
        month = start_date[1]
        day = start_date[2]
        curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
        end_day = f'{end_date[0]}-{str(end_date[1]).zfill(2)}-{str(end_date[2]).zfill(2)}'
    else:
        for last_row in dataset.execute(f"""SELECT `Date` FROM `dataset_2023-24` ORDER BY `index` DESC LIMIT 1"""):
            curr_day = last_row[0]
            year = int(curr_day.split('-')[0])
            month = int(curr_day.split('-')[1])
            day = int(curr_day.split('-')[2]) + 1
            curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
            end_day = datetime.today().strftime('%Y-%m-%d')
            break

    while curr_day != end_day:
        try:
            games = Scoreboard(sport='NBA', date=(curr_day)).games

            for game in games:
                home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")
                away_team_name = game['away_team'].replace("Los Angeles Clippers", "LA Clippers")

                year = int(curr_day.split('-')[0])
                month = int(curr_day.split('-')[1])
                day = int(curr_day.split('-')[2])

                if year % 4 == 0:
                    if day <= month_dict_leap[month]:
                        cur.execute(f"""INSERT INTO `dataset_2023-24` (`TEAM_NAME`, `TEAM_NAME.1`, `Date`, `Date.1`) VALUES ('{home_team_name}', '{away_team_name}', '{curr_day}', '{curr_day}')""")
                        con.commit()
                else:
                    if day <= month_dict[month]:
                        cur.execute(f"""INSERT INTO `dataset_2023-24` (`TEAM_NAME`, `TEAM_NAME.1`, `Date`, `Date.1`) VALUES ('{home_team_name}', '{away_team_name}', '{curr_day}', '{curr_day}')""")
                        con.commit()
        except: None
        
        if day == 31:
            day = 1
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        else:
            day += 1
        curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'

    dataset.close()
    cur.close()
    con.close()

def add_covered(init=False):
    sportsbook = 'fanduel'
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()

    if init:
        year = start_date[0]
        month = start_date[1]
        day = start_date[2]
        curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
        end_day = f'{end_date[0]}-{str(end_date[1]).zfill(2)}-{str(end_date[2]).zfill(2)}'
    else:
        for last_row in dataset.execute(f"""SELECT `Date` FROM `dataset_2023-24` WHERE `Score` IS NULL ORDER BY `index` ASC LIMIT 1"""):
            curr_day = last_row[0]
            year = int(curr_day.split('-')[0])
            month = int(curr_day.split('-')[1])
            day = int(curr_day.split('-')[2])
            end_day = datetime.today().strftime('%Y-%m-%d')
            break

    while curr_day != end_day:
        try:
            games = Scoreboard(sport='NBA', date=(curr_day)).games

            for game in games:
                home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")

                home_score = away_score = totals_value = home_line = None

                # Get team scores
                home_score = game['home_score']
                away_score = game['away_score']

                # Get money line bet values
                if sportsbook in game['home_ml']:
                    money_line_home_value = game['home_ml'][sportsbook]
                if sportsbook in game['away_ml']:
                    money_line_away_value = game['away_ml'][sportsbook]

                # Get totals bet value
                if sportsbook in game['total']:
                    totals_value = game['total'][sportsbook]

                # Get spreads bet value
                if sportsbook in game['home_spread']:
                    home_line = game['home_spread'][sportsbook]

                home_win = 1 if home_score > away_score else 0
                ou_cover = 1 if (home_score + away_score) > totals_value else 0 if (home_score + away_score) < totals_value else 2
                spread_cover = 1 if (away_score - home_score) < home_line else 0 if (away_score - home_score) > home_line else 2

                cur.execute(f"""UPDATE `dataset_2023-24` SET `Score` = '{home_score + away_score}', `Home-Team-Win` = '{home_win}', `OU` = '{totals_value}', `OU-Cover` = '{ou_cover}', `Spread` = '{home_line}', `Spread-Cover` = '{spread_cover}', `ML_Home` = '{money_line_home_value}', `ML_Away` = '{money_line_away_value}' WHERE `Date` = '{curr_day}' AND `TEAM_NAME` = '{home_team_name}'""")
                con.commit()
        except: pass
        
        if day == 31:
            day = 1
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        else:
            day += 1
        curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'

    dataset.close()
    cur.close()
    con.close()

def add_stats():
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    count = index = 0


    for row in dataset.execute("""SELECT `Date`, `TEAM_NAME`, `TEAM_NAME.1`, `index` FROM `dataset_2023-24`"""):
        # if count == 20: break

        index += 1
        # if row[0] != '2024-04-06': continue

        if row[3] == None:
            segment = '?SeasonType=IST' if row[0] == '2023-12-09' else ''
            count += 1
            split = row[0].split('-')
            year = split[0]
            month = split[1]
            day = split[2]

            if int(year) == 2024 and int(month) >= 4 and int(month) <= 6 and int(day) >= 20:
                segment_roster = segment + '&SeasonType=Playoffs'
            elif int(year) == 2024 and int(month) == 4 and int(day) >= 16:
                segment_roster = segment + '&SeasonType=PlayIn'
            else:
                segment_roster = segment

            date = row[0]
            if int(day) != 1:
                date_before = date[:-2] + str(int(day)-1)
            else:
                if int(year[-2:]) % 4 == 0:
                    if int(month) == 1:
                        date_before = str(int(year)-1) + '-12-' + str(month_dict_leap[12])
                    else:
                        date_before = year + '-' + str(int(month)-1) + '-' + str(month_dict_leap[int(month)-1])
                else:
                    if int(month) == 1:
                        date_before = str(int(year)-1) + '-12-' + str(month_dict[12])
                    else:
                        date_before = year + '-' + str(int(month)-1) + '-' + str(month_dict[int(month)-1])

            data_url = 'https://stats.nba.com/stats/leaguedashteamstats?' \
            f'Conference=&DateFrom=&DateTo={date_before}&Division=&GameScope=&' \
            'GameSegment=&LastNGames=0&LeagueID=00&Location=&' \
            'MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&' \
            'PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&' \
            'PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&' \
            'Season=2023-24&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&' \
            'StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision='

            raw_data = requests.get(data_url, headers=data_headers)
            try:
                json = raw_data.json()
            except Exception as e:
                print('json' + e)
                continue
            try:
                data_list = json.get('resultSets')[0]
            except Exception as e:
                print('json_get' + e)
                continue
            df = pd.DataFrame(data=data_list.get('rowSet'), columns=data_list.get('headers'))

            found = 0
            for i in df.index:
                curr_team = df['TEAM_NAME'][i]

                if curr_team == row[1]:
                    gp = df['GP'][i]
                    w = df['W'][i]
                    l = df['L'][i]
                    w_pct = df['W_PCT'][i]
                    min = df['MIN'][i]
                    fgm = df['FGM'][i]
                    fga = df['FGA'][i]
                    fg_pct = df['FG_PCT'][i]
                    fg3m = df['FG3M'][i]
                    fg3a = df['FG3A'][i]
                    fg3_pct = df['FG3_PCT'][i]
                    ftm = df['FTM'][i]
                    fta = df['FTA'][i]
                    ft_pct = df['FT_PCT'][i]
                    oreb = df['OREB'][i]
                    dreb = df['DREB'][i]
                    reb = df['REB'][i]
                    ast = df['AST'][i]
                    tov = df['TOV'][i]
                    stl = df['STL'][i]
                    blk = df['BLK'][i]
                    blka = df['BLKA'][i]
                    pf = df['PF'][i]
                    pfd = df['PFD'][i]
                    pts = df['PTS'][i]
                    plus_minus = df['PLUS_MINUS'][i]
                    gp_rank = df['GP_RANK'][i]
                    w_rank = df['W_RANK'][i]
                    l_rank = df['L_RANK'][i]
                    w_pct_rank = df['W_PCT_RANK'][i]
                    min_rank = df['MIN_RANK'][i]
                    fgm_rank = df['FGM_RANK'][i]
                    fga_rank = df['FGA_RANK'][i]
                    fg_pct_rank = df['FG_PCT_RANK'][i]
                    fg3m_rank = df['FG3M_RANK'][i]
                    fg3a_rank = df['FG3A_RANK'][i]
                    fg3_pct_rank = df['FG3_PCT_RANK'][i]
                    ftm_rank = df['FTM_RANK'][i]
                    fta_rank = df['FTA_RANK'][i]
                    ft_pct_rank = df['FT_PCT_RANK'][i]
                    oreb_rank = df['OREB_RANK'][i]
                    dreb_rank = df['DREB_RANK'][i]
                    reb_rank = df['REB_RANK'][i]
                    ast_rank = df['AST_RANK'][i]
                    tov_rank = df['TOV_RANK'][i]
                    stl_rank = df['STL_RANK'][i]
                    blk_rank = df['BLK_RANK'][i]
                    blka_rank = df['BLKA_RANK'][i]
                    pf_rank = df['PF_RANK'][i]
                    pfd_rank = df['PFD_RANK'][i]
                    pts_rank = df['PTS_RANK'][i]
                    plus_minus_rank = df['PLUS_MINUS_RANK'][i]
                    found += 1
                elif curr_team == row[2]:
                    gp1 = df['GP'][i]
                    w1 = df['W'][i]
                    l1 = df['L'][i]
                    w_pct1 = df['W_PCT'][i]
                    min1 = df['MIN'][i]
                    fgm1 = df['FGM'][i]
                    fga1 = df['FGA'][i]
                    fg_pct1 = df['FG_PCT'][i]
                    fg3m1 = df['FG3M'][i]
                    fg3a1 = df['FG3A'][i]
                    fg3_pct1 = df['FG3_PCT'][i]
                    ftm1 = df['FTM'][i]
                    fta1 = df['FTA'][i]
                    ft_pct1 = df['FT_PCT'][i]
                    oreb1 = df['OREB'][i]
                    dreb1 = df['DREB'][i]
                    reb1 = df['REB'][i]
                    ast1 = df['AST'][i]
                    tov1 = df['TOV'][i]
                    stl1 = df['STL'][i]
                    blk1 = df['BLK'][i]
                    blka1 = df['BLKA'][i]
                    pf1 = df['PF'][i]
                    pfd1 = df['PFD'][i]
                    pts1 = df['PTS'][i]
                    plus_minus1 = df['PLUS_MINUS'][i]
                    gp_rank1 = df['GP_RANK'][i]
                    w_rank1 = df['W_RANK'][i]
                    l_rank1 = df['L_RANK'][i]
                    w_pct_rank1 = df['W_PCT_RANK'][i]
                    min_rank1 = df['MIN_RANK'][i]
                    fgm_rank1 = df['FGM_RANK'][i]
                    fga_rank1 = df['FGA_RANK'][i]
                    fg_pct_rank1 = df['FG_PCT_RANK'][i]
                    fg3m_rank1 = df['FG3M_RANK'][i]
                    fg3a_rank1 = df['FG3A_RANK'][i]
                    fg3_pct_rank1 = df['FG3_PCT_RANK'][i]
                    ftm_rank1 = df['FTM_RANK'][i]
                    fta_rank1 = df['FTA_RANK'][i]
                    ft_pct_rank1 = df['FT_PCT_RANK'][i]
                    oreb_rank1 = df['OREB_RANK'][i]
                    dreb_rank1 = df['DREB_RANK'][i]
                    reb_rank1 = df['REB_RANK'][i]
                    ast_rank1 = df['AST_RANK'][i]
                    tov_rank1 = df['TOV_RANK'][i]
                    stl_rank1 = df['STL_RANK'][i]
                    blk_rank1 = df['BLK_RANK'][i]
                    blka_rank1 = df['BLKA_RANK'][i]
                    pf_rank1 = df['PF_RANK'][i]
                    pfd_rank1 = df['PFD_RANK'][i]
                    pts_rank1 = df['PTS_RANK'][i]
                    plus_minus_rank1 = df['PLUS_MINUS_RANK'][i]
                    found += 1

                if found == 2: break

            URL = 'https://www.nba.com/stats/team/' + team_dict[row[1]] + '/players-advanced?&DateFrom=' + date + '&DateTo=' + date + '&Season=2023-24&dir=D&sort=MIN' + segment_roster
            
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
            except Exception:
                try:
                    driver.quit()
                    driver = webdriver.Chrome(options=options)
                    driver.get(URL)
                    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                except Exception:
                    print(row[1], date, 'get_players')
                    driver.quit()
                    continue

            driver.execute_script('window.stop();')
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = soup.find_all(class_='Crom_body__UYOcU')[1].find_all('tr')
            players = []

            for r in results:
                players.append(r.find('td').text)

            driver.quit()

            URL = 'https://www.nba.com/stats/team/' + team_dict[row[1]] + '/players-advanced?DateTo=' + date_before + '&Season=2023-24&dir=D&sort=MIN' + segment
            
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
            except Exception:
                try:
                    driver.quit()
                    driver = webdriver.Chrome(options=options)
                    driver.get(URL)
                    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                except Exception:
                    print(row[1], date, 'get_stats')
                    driver.quit()
                    continue

            driver.execute_script('window.stop();')
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = soup.find_all(class_='Crom_body__UYOcU')[1].find_all('tr')
            
            pie = pie_w = min_p = player_count = 0

            for r in results:
                stats = r.find_all('td')

                for i in range(len(players)):
                    if stats[0].text == players[i]:
                        pie += float(stats[-1].text)
                        pie_w += float(stats[-1].text) * float(stats[2].text)
                        min_p += float(stats[2].text)
                
                        player_count += 1
                        break

                if player_count == 8:
                    break

            pie_w /= min_p
            driver.quit()

            URL = 'https://www.nba.com/stats/team/' + team_dict[row[2]] + '/players-advanced?&DateFrom=' + date + '&DateTo=' + date + '&Season=2023-24&dir=D&sort=MIN' + segment_roster
            
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
            except Exception:
                try:
                    driver.quit()
                    driver = webdriver.Chrome(options=options)
                    driver.get(URL)
                    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                except Exception:
                    print(row[2], date, 'get_players')
                    driver.quit()
                    continue

            driver.execute_script('window.stop();')
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = soup.find_all(class_='Crom_body__UYOcU')[1].find_all('tr')
            players = []

            for r in results:
                players.append(r.find('td').text)

            driver.quit()

            URL = 'https://www.nba.com/stats/team/' + team_dict[row[2]] + '/players-advanced?DateTo=' + date_before + '&Season=2023-24&dir=D&sort=MIN' + segment
            
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
            except Exception:
                try:
                    driver.quit()
                    driver = webdriver.Chrome(options=options)
                    driver.get(URL)
                    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CLASS_NAME, 'Crom_body__UYOcU')))
                except Exception:
                    print(row[2], date, 'get_stats')
                    driver.quit()
                    continue

            driver.execute_script('window.stop();')
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = soup.find_all(class_='Crom_body__UYOcU')[1].find_all('tr')
            
            pie1 = pie_w1 = min_p1 = player_count = 0

            for r in results:
                stats = r.find_all('td')

                for i in range(len(players)):
                    if stats[0].text == players[i]:
                        pie1 += float(stats[-1].text)
                        pie_w1 += float(stats[-1].text) * float(stats[2].text)
                        min_p1 += float(stats[2].text)
                
                        player_count += 1
                        break

                if player_count == 8:
                            break

            pie_w1 /= min_p1
            driver.quit()

            curr_date = row[0].split('-')
            year = int(curr_date[0])
            month = int(curr_date[1])
            day = int(curr_date[2])
            if day != 1:
                day -= 1
            else:
                if year % 4 == 0:
                    if month == 1:
                        year -= 1
                        month = 12
                        day = month_dict_leap[month]
                    else:
                        month -= 1
                        day = month_dict_leap[month]
                else:
                    if month == 1:
                        year -= 1
                        month = 12
                        day = month_dict[month]
                    else:
                        month -= 1
                        day = month_dict[month]
            found_previous = count_days = 0
            home_off = away_off = None

            while found_previous < 2:
                if count_days == 14:
                    if home_off == None: home_off = count_days
                    if away_off == None: away_off = count_days
                    break

                count_days += 1
                curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
                try:
                    games = Scoreboard(sport='NBA', date=(curr_day)).games

                    for game in games:
                        home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")
                        away_team_name = game['away_team'].replace("Los Angeles Clippers", "LA Clippers")

                        if home_off == None and (home_team_name == row[1] or away_team_name == row[1]):
                            home_off = count_days
                            found_previous += 1
                        if away_off == None and (home_team_name == row[2] or away_team_name == row[2]):
                            away_off = count_days
                            found_previous += 1

                    if day != 1:
                        day -= 1
                    else:
                        if year % 4 == 0:
                            if month == 1:
                                year -= 1
                                month = 12
                                day = month_dict_leap[month]
                            else:
                                month -= 1
                                day = month_dict_leap[month]
                        else:
                            if month == 1:
                                year -= 1
                                month = 12
                                day = month_dict[month]
                            else:
                                month -= 1
                                day = month_dict[month]
                    curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
                except: 
                    if day != 1:
                        day -= 1
                    else:
                        if year % 4 == 0:
                            if month == 1:
                                year -= 1
                                month = 12
                                day = month_dict_leap[month]
                            else:
                                month -= 1
                                day = month_dict_leap[month]
                        else:
                            if month == 1:
                                year -= 1
                                month = 12
                                day = month_dict[month]
                            else:
                                month -= 1
                                day = month_dict[month]
                    curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'

            cur.execute(f"""UPDATE `dataset_2023-24` SET `index` = '{index - 1}', `GP` = '{gp}', `W` = '{w}', `L` = '{l}', `W_PCT` = '{w_pct}', `MIN` = '{min}', `FGM` = '{fgm}', `FGA` = '{fga}', `FG_PCT` = '{fg_pct}', `FG3M` = '{fg3m}', `FG3A` = '{fg3a}', `FG3_PCT` = '{fg3_pct}', `FTM` = '{ftm}', `FTA` = '{fta}', `FT_PCT` = '{ft_pct}', `OREB` = '{oreb}', `DREB` = '{dreb}', `REB` = '{reb}', `AST` = '{ast}', `TOV` = '{tov}', `STL` = '{stl}', `BLK` = '{blk}', `BLKA` = '{blka}', `PF` = '{pf}', `PFD` = '{pfd}', `PTS` = '{pts}', `PLUS_MINUS` = '{plus_minus}', `GP_RANK` = '{gp_rank}', `W_RANK` = '{w_rank}', `L_RANK` = '{l_rank}', `W_PCT_RANK` = '{w_pct_rank}', `MIN_RANK` = '{min_rank}', `FGM_RANK` = '{fgm_rank}', `FGA_RANK` = '{fga_rank}', `FG_PCT_RANK` = '{fg_pct_rank}', `FG3M_RANK` = '{fg3m_rank}', `FG3A_RANK` = '{fg3a_rank}', `FG3_PCT_RANK` = '{fg3_pct_rank}', `FTM_RANK` = '{ftm_rank}', `FTA_RANK` = '{fta_rank}', `FT_PCT_RANK` = '{ft_pct_rank}', `OREB_RANK` = '{oreb_rank}', `DREB_RANK` = '{dreb_rank}', `REB_RANK` = '{reb_rank}', `AST_RANK` = '{ast_rank}', `TOV_RANK` = '{tov_rank}', `STL_RANK` = '{stl_rank}', `BLK_RANK` = '{blk_rank}', `BLKA_RANK` = '{blka_rank}', `PF_RANK` = '{pf_rank}', `PFD_RANK` = '{pfd_rank}', `PTS_RANK` = '{pts_rank}', `PLUS_MINUS_RANK` = '{plus_minus_rank}', `PIE` = '{format(pie, '.1f')}', `PIE_W` = '{format(pie_w, '.1f')}', `MIN_P` = '{format(min_p, '.1f')}', `GP.1` = '{gp1}', `W.1` = '{w1}', `L.1` = '{l1}', `W_PCT.1` = '{w_pct1}', `MIN.1` = '{min1}', `FGM.1` = '{fgm1}', `FGA.1` = '{fga1}', `FG_PCT.1` = '{fg_pct1}', `FG3M.1` = '{fg3m1}', `FG3A.1` = '{fg3a1}', `FG3_PCT.1` = '{fg3_pct1}', `FTM.1` = '{ftm1}', `FTA.1` = '{fta1}', `FT_PCT.1` = '{ft_pct1}', `OREB.1` = '{oreb1}', `DREB.1` = '{dreb1}', `REB.1` = '{reb1}', `AST.1` = '{ast1}', `TOV.1` = '{tov1}', `STL.1` = '{stl1}', `BLK.1` = '{blk1}', `BLKA.1` = '{blka1}', `PF.1` = '{pf1}', `PFD.1` = '{pfd1}', `PTS.1` = '{pts1}', `PLUS_MINUS.1` = '{plus_minus1}', `GP_RANK.1` = '{gp_rank1}', `W_RANK.1` = '{w_rank1}', `L_RANK.1` = '{l_rank1}', `W_PCT_RANK.1` = '{w_pct_rank1}', `MIN_RANK.1` = '{min_rank1}', `FGM_RANK.1` = '{fgm_rank1}', `FGA_RANK.1` = '{fga_rank1}', `FG_PCT_RANK.1` = '{fg_pct_rank1}', `FG3M_RANK.1` = '{fg3m_rank1}', `FG3A_RANK.1` = '{fg3a_rank1}', `FG3_PCT_RANK.1` = '{fg3_pct_rank1}', `FTM_RANK.1` = '{ftm_rank1}', `FTA_RANK.1` = '{fta_rank1}', `FT_PCT_RANK.1` = '{ft_pct_rank1}', `OREB_RANK.1` = '{oreb_rank1}', `DREB_RANK.1` = '{dreb_rank1}', `REB_RANK.1` = '{reb_rank1}', `AST_RANK.1` = '{ast_rank1}', `TOV_RANK.1` = '{tov_rank1}', `STL_RANK.1` = '{stl_rank1}', `BLK_RANK.1` = '{blk_rank1}', `BLKA_RANK.1` = '{blka_rank1}', `PF_RANK.1` = '{pf_rank1}', `PFD_RANK.1` = '{pfd_rank1}', `PTS_RANK.1` = '{pts_rank1}', `PLUS_MINUS_RANK.1` = '{plus_minus_rank1}', `PIE.1` = '{format(pie1, '.1f')}', `PIE_W.1` = '{format(pie_w1, '.1f')}', `MIN_P.1` = '{format(min_p1, '.1f')}', `Days-Rest-Home` = '{home_off}', `Days-Rest-Away` = '{away_off}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{row[1]}'""")
            con.commit()

    dataset.close()
    cur.close()
    con.close()

def fix_index():
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    index = 0

    for row in dataset.execute("""SELECT `Date`, `TEAM_NAME`, `index` FROM `dataset_2023-24`"""):
        cur.execute(f"""UPDATE `dataset_2023-24` SET `index` = '{index}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{row[1]}'""")
        con.commit()
        index += 1

    dataset.close()
    cur.close()
    con.close()

def test_days_off():
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()

    for row in dataset.execute("""SELECT `Date`, `TEAM_NAME`, `TEAM_NAME.1`, `index` FROM `dataset_2023-24`"""):
        # if row[0] != '2024-04-06': continue
        print(row[0])

        curr_date = row[0].split('-')
        year = int(curr_date[0])
        month = int(curr_date[1])
        day = int(curr_date[2])
        if day != 1:
            day -= 1
        else:
            if year % 4 == 0:
                if month == 1:
                    year -= 1
                    month = 12
                    day = month_dict_leap[month]
                else:
                    month -= 1
                    day = month_dict_leap[month]
            else:
                if month == 1:
                    year -= 1
                    month = 12
                    day = month_dict[month]
                else:
                    month -= 1
                    day = month_dict[month]
        found_previous = count_days = 0
        home_off = away_off = None

        while found_previous < 2:
            if count_days == 14:
                if home_off == None: home_off = count_days
                if away_off == None: away_off = count_days
                break

            count_days += 1
            curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
            try:
                games = Scoreboard(sport='NBA', date=(curr_day)).games

                for game in games:
                    home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")
                    away_team_name = game['away_team'].replace("Los Angeles Clippers", "LA Clippers")

                    if home_off == None and (home_team_name == row[1] or away_team_name == row[1]):
                        home_off = count_days
                        found_previous += 1
                    if away_off == None and (home_team_name == row[2] or away_team_name == row[2]):
                        away_off = count_days
                        found_previous += 1

                if day != 1:
                    day -= 1
                else:
                    if year % 4 == 0:
                        if month == 1:
                            year -= 1
                            month = 12
                            day = month_dict_leap[month]
                        else:
                            month -= 1
                            day = month_dict_leap[month]
                    else:
                        if month == 1:
                            year -= 1
                            month = 12
                            day = month_dict[month]
                        else:
                            month -= 1
                            day = month_dict[month]
                curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'
            except:
                if day != 1:
                    day -= 1
                else:
                    if year % 4 == 0:
                        if month == 1:
                            year -= 1
                            month = 12
                            day = month_dict_leap[month]
                        else:
                            month -= 1
                            day = month_dict_leap[month]
                    else:
                        if month == 1:
                            year -= 1
                            month = 12
                            day = month_dict[month]
                        else:
                            month -= 1
                            day = month_dict[month]
                curr_day = f'{year}-{str(month).zfill(2)}-{str(day).zfill(2)}'

        # print(row[1], row[2], home_off, away_off)
        cur.execute(f"""UPDATE `dataset_2023-24` SET `Days-Rest-Home` = '{home_off}', `Days-Rest-Away` = '{away_off}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{row[1]}'""")
        con.commit()

    dataset.close()
    cur.close()
    con.close()

def add_table():
    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()

    cur.execute('CREATE TABLE `dataset_2023-24` AS SELECT * FROM `dataset_2012-23`')
    con.commit()

    cur.close()
    con.close()

# start_date = [2023, 10, 27]
# end_date = [2023, 10, 28]
start_date = [2024, 4, 23]
end_date = [2024, 5, 1]

# add_games()
# add_stats()
add_covered()
# fix_index()
# test_days_off()
# add_table()