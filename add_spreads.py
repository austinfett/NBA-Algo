from webbrowser import get
import pandas as pd
import sqlite3

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

def add_spreads():
    spread_data = pd.read_csv('https://raw.githubusercontent.com/austinfett/ML-Capstone/main/2021_2023_Box_Scores.csv')

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

        home, away, line = get_game(spread_data, row[0], row[1], row[2])

        diff = away - home
        covered = 1.0 if diff < line else 0.0 if diff > line else 2.0

        cur.execute(f"""UPDATE `dataset_2012-23` SET `Spread` = '{line}', `Spread-Cover` = '{covered}' WHERE `Date` = '{row[0]}' AND `TEAM_NAME` = '{row[1]}'""")
        con.commit()

        # if count == 1000: break
        # count += 1

    dataset.close()
    cur.close()
    con.close()

    print(not_found)

def get_game(data, date, home_team, away_team):
    home = away = None
    for i in data.index:
        if data['Date'][i] == date:
            if team_dict[data['Opponent'][i]] == home_team:
                away = int(data['Points'][i])
            elif team_dict[data['Opponent'][i]] == away_team:
                home = int(data['Points'][i])
                line = int(data['line'][i])
            
            if home != None and away != None: return home, away, line

    return None, None, None

add_spreads()