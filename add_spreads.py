from webbrowser import get
import pandas as pd
import sqlite3
from sbrscrape import Scoreboard

team_dict = {
    "BOS" : "Boston Celtics",
    "BRK" : "Brooklyn Nets",
    "BKN" : "Brooklyn Nets",
    "NYK" : "New York Knicks",
    "PHI" : "Philadelphia 76ers",
    "TOR" : "Toronto Raptors",
    "CHI" : "Chicago Bulls",
    "CLE" : "Cleveland Cavaliers",
    "DET" : "Detroit Pistons",
    "IND" : "Indiana Pacers",
    "MIL" : "Milwaukee Bucks",
    "ATL" : "Atlanta Hawks",
    "CHA" : "Charlotte Bobcats",
    "CHO" : "Charlotte Hornets",
    "MIA" : "Miami Heat",
    "ORL" : "Orlando Magic",
    "WAS" : "Washington Wizards",
    "DEN" : "Denver Nuggets",
    "MIN" : "Minnesota Timberwolves",
    "OKC" : "Oklahoma City Thunder",
    "POR" : "Portland Trail Blazers",
    "UTA" : "Utah Jazz",
    "GSW" : "Golden State Warriors",
    "LAC" : "LA Clippers",
    "LAL" : "Los Angeles Lakers",
    "PHO" : "Phoenix Suns",
    "PHX" : "Phoenix Suns",
    "SAC" : "Sacramento Kings",
    "DAL" : "Dallas Mavericks",
    "HOU" : "Houston Rockets",
    "MEM" : "Memphis Grizzlies",
    "NOP" : "New Orleans Pelicans",
    "NOH" : "New Orleans Hornets",
    "SAS" : "San Antonio Spurs"
}

def add_spreads_git():
    spread_data = pd.read_csv('https://raw.githubusercontent.com/austinfett/ML-Capstone/main/working_spreads.csv')

    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    # count = 1
    not_found = 0

    for row in dataset.execute("""SELECT `Date`, `TEAM_NAME`, `TEAM_NAME.1`, `Spread`, `Spread-Cover` FROM `dataset_2012-23`"""):
        if row[3] != None and row[4] != None : continue

        # if int(row[0].split('-')[0]) < 2022:
        #     not_found += 1
        #     continue

        result, line = get_game(spread_data, row[0], row[1].replace('Los Angeles Clippers', 'LA Clippers'))

        if result != None and line != None:
            cur.execute(f"""UPDATE `dataset_2012-23` SET `Spread` = '{line}', `Spread-Cover` = '{result}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{row[1]}'""")
            con.commit()

        # if count == 1000: break
        # count += 1

    dataset.close()
    cur.close()
    con.close()

    print(not_found)

def get_game(data, date, home_team):
    spread_result = line = None
    for i in data.index:
        if data['date'][i] == date:
            if team_dict[data['team'][i]] == home_team:
                line = int(data['Line'][i])
                spread_result = 1.0 if int(data['PointDifference'][i]) < line else 0.0 if int(data['PointDifference'][i]) > line else 2.0
                return spread_result, line
            elif team_dict[data['team_opp'][i]] == home_team:
                line = -int(data['Line'][i])
                spread_result = 1.0 if -int(data['PointDifference'][i]) < line else 0.0 if -int(data['PointDifference'][i]) > line else 2.0
                return spread_result, line

    return None, None

def add_spreads_sbr():
    sportsbook = 'fanduel'

    con = sqlite3.connect('Data/dataset.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    count = 0

    for row in dataset.execute("""SELECT `Date`, `TEAM_NAME`, `TEAM_NAME.1`, `Spread`, `Spread-Cover` FROM `dataset_2012-23`"""):
        if row[3] != None and row[4] != None : continue

        try:
            games = Scoreboard(sport='NBA', date=(row[0])).games

            for game in games:
                home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")

                home_score = away_score = home_line = None

                # Get team scores
                home_score = game['home_score']
                away_score = game['away_score']

                # Get spreads bet value
                if sportsbook in game['home_spread']:
                    home_line = game['home_spread'][sportsbook]

                    spread_cover = 1 if (away_score - home_score) < home_line else 0 if (away_score - home_score) > home_line else 2

                    cur.execute(f"""UPDATE `dataset_2012-23` SET `Spread` = '{home_line}', `Spread-Cover` = '{spread_cover}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{home_team_name}'""")
                    con.commit()
        except: count += 1

    dataset.close()
    cur.close()
    con.close()
    print('Missing spreads: ' + str(count))

def count_missing():
    con = sqlite3.connect('Data/dataset.sqlite')
    dataset = con.cursor()
    count = 0

    for row in dataset.execute("""SELECT `Spread` FROM `dataset_2012-23`"""):
        if row[0] == None: count += 1

    dataset.close()
    con.close()

    print('Missing spreads: ' + str(count))

add_spreads_git()
add_spreads_sbr()
# count_missing()