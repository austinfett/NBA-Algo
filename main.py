import argparse
from datetime import datetime, timedelta

import pandas as pd
# import tensorflow as tf
from colorama import Fore, Style
from sbrscrape import Scoreboard

from src.DataProviders.SbrOddsProvider import SbrOddsProvider
from src.Predict import XGBoost_Runner
from src.Utils.Dictionaries import team_index_current
from src.Utils.tools import create_todays_games_from_odds, get_json_data, to_data_frame, get_todays_games_json, create_todays_games, get_injuries, get_pie

todays_games_url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2023/scores/00_todays_scores.json'
data_url = 'https://stats.nba.com/stats/leaguedashteamstats?' \
           'Conference=&DateFrom=&DateTo=&Division=&GameScope=&' \
           'GameSegment=&LastNGames=0&LeagueID=00&Location=&' \
           'MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&' \
           'PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&' \
           'PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&' \
           'Season=2023-24&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&' \
           'StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision='

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

def createTodaysGames(games, df, odds):
    match_data = []
    todays_games_uo = []
    home_spread = []
    away_spread = []
    home_team_odds = []
    away_team_odds = []

    home_team_days_rest = []
    away_team_days_rest = []
    count = 0

    for game in games:
        home_team = game[0]
        away_team = game[1]
        if home_team not in team_index_current or away_team not in team_index_current:
            continue
        if odds is not None:
            game_odds = odds[home_team + ':' + away_team]
            todays_games_uo.append(game_odds['under_over_odds'])

            home_spread.append(game_odds[home_team]['line'])
            away_spread.append(game_odds[away_team]['line'])

            home_team_odds.append(game_odds[home_team]['money_line_odds'])
            away_team_odds.append(game_odds[away_team]['money_line_odds'])

        else:
            todays_games_uo.append(input(home_team + ' vs ' + away_team + ': '))

            home_spread.append(input(home_team + ' '))
            away_spread.append(input(away_team + ' '))

            home_team_odds.append(input(home_team + ' odds: '))
            away_team_odds.append(input(away_team + ' odds: '))

        # calculate days rest for both teams
        curr_date = str(datetime.today()).split(' ')[0].split('-')
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

                    if home_off == None and (home_team_name == home_team or away_team_name == home_team):
                        home_off = count_days
                        found_previous += 1
                    if away_off == None and (home_team_name == away_team or away_team_name == away_team):
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

        home_team_days_rest.append(home_off)
        away_team_days_rest.append(away_off)
        home_team_series = df.iloc[team_index_current.get(home_team)]
        away_team_series = df.iloc[team_index_current.get(away_team)]
        stats = pd.concat([home_team_series, away_team_series])
        stats['Days-Rest-Home'] = home_off
        stats['Days-Rest-Away'] = away_off
        stats = pd.concat([stats, pd.Series({'OU':todays_games_uo[count]}), pd.Series({'Spread':home_spread[count]})])
        match_data.append(stats)

        count += 1

    games_data_frame = pd.concat(match_data, ignore_index=True, axis=1)
    games_data_frame = games_data_frame.T

    frame_ml = games_data_frame.drop(columns=['TEAM_ID', 'TEAM_NAME'])
    data = frame_ml.values
    data = data.astype(float)

    return data, todays_games_uo, home_spread, away_spread, frame_ml, home_team_odds, away_team_odds


def main():
    odds = None
    teams = []
    if args.odds:
        odds = SbrOddsProvider(sportsbook=args.odds).get_odds()
        games = create_todays_games_from_odds(odds)
        if len(games) == 0:
            print("No games found.")
            return
        if (games[0][0] + ':' + games[0][1]) not in list(odds.keys()):
            print(games[0][0] + ':' + games[0][1])
            print(Fore.RED,"--------------Games list not up to date for todays games!!! Scraping disabled until list is updated.--------------")
            print(Style.RESET_ALL)
            odds = None
        else:
            print(f"------------------{args.odds} odds data------------------")
            for g in odds.keys():
                home_team, away_team = g.split(":")
                teams.append(home_team)
                teams.append(away_team)
                print(f"{away_team} ({odds[g][away_team]['money_line_odds']}) {odds[g][away_team]['line']} @ {home_team} ({odds[g][home_team]['money_line_odds']}) {odds[g][home_team]['line']}")
    else:
        data = get_todays_games_json(todays_games_url)
        games = create_todays_games(data)
    data = get_json_data(data_url)
    df = to_data_frame(data)
    
    df['PIE'] = 0.0
    df['PIE_W'] = 0.0
    injury_list = get_injuries()
    
    for i in df.index:
        curr_team = df['TEAM_NAME'][i]

        if curr_team in teams:
            pie, pie_w, min_p = get_pie(curr_team, injury_list)
            df.at[i, 'PIE'] = round(pie, 1)
            df.at[i, 'PIE_W'] = round(pie_w, 1)

    # print(df.to_string())
    data, todays_games_uo, home_spread, away_spread, frame_ml, home_team_odds, away_team_odds = createTodaysGames(games, df, odds)
    if args.nn:
        print("------------Neural Network Model Predictions-----------")
        # data = tf.keras.utils.normalize(data, axis=1)
        # NN_Runner.nn_runner(data, todays_games_uo, frame_ml, games, home_team_odds, away_team_odds, args.kc)
        print("-------------------------------------------------------")
    if args.xgb:
        print("---------------XGBoost Model Predictions---------------")
        XGBoost_Runner.xgb_runner(data, todays_games_uo, home_spread, away_spread, frame_ml, games, home_team_odds, away_team_odds, args.kc)
        print("-------------------------------------------------------")
    if args.A:
        print("---------------XGBoost Model Predictions---------------")
        XGBoost_Runner.xgb_runner(data, todays_games_uo, home_spread, away_spread, frame_ml, games, home_team_odds, away_team_odds, args.kc)
        print("-------------------------------------------------------")
        # data = tf.keras.utils.normalize(data, axis=1)
        print("------------Neural Network Model Predictions-----------")
        # NN_Runner.nn_runner(data, todays_games_uo, frame_ml, games, home_team_odds, away_team_odds, args.kc)
        print("-------------------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Model to Run')
    parser.add_argument('-xgb', action='store_true', help='Run with XGBoost Model')
    parser.add_argument('-nn', action='store_true', help='Run with Neural Network Model')
    parser.add_argument('-A', action='store_true', help='Run all Models')
    parser.add_argument('-odds', help='Sportsbook to fetch from. (fanduel, draftkings, betmgm, pointsbet, caesars, wynn, bet_rivers_ny')
    parser.add_argument('-kc', action='store_true', help='Calculates percentage of bankroll to bet based on model edge')
    args = parser.parse_args()
    main()
