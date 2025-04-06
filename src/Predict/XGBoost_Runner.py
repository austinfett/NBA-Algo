import copy

import numpy as np
import pandas as pd
import xgboost as xgb
from colorama import Fore, Style, init, deinit
from datetime import date
from src.Utils import Expected_Value
from src.Utils import Kelly_Criterion as kc
from src.Utils.tools import add_to_results


# from src.Utils.Dictionaries import team_index_current
# from src.Utils.tools import get_json_data, to_data_frame, get_todays_games_json, create_todays_games
init()
xgb_ml = xgb.Booster()
xgb_ml.load_model('Models/XGBoost_Models/XGBoost_69.6%_ML-min.json')
xgb_uo = xgb.Booster()
xgb_uo.load_model('Models/XGBoost_Models/XGBoost_55.4%_UO-min.json')
xgb_spread = xgb.Booster()
xgb_spread.load_model('Models/XGBoost_Models/XGBoost_63.5%_Spread-min.json')


def xgb_runner(data, todays_games_uo, home_spread, away_spread, frame_ml, games, home_team_odds, away_team_odds, kelly_criterion):
    ml_predictions_array = []
    print(frame_ml.columns.values)

    for row in data:
        ml_predictions_array.append(xgb_ml.predict(xgb.DMatrix(np.array([row]))))
        # print(f"""{format(row[54], '.1f')}, {format(row[55], '.1f')}, {format(row[111], '.1f')}, {format(row[112], '.1f')}""")
    
    frame_uo = copy.deepcopy(frame_ml)
    frame_uo['OU'] = np.asarray(todays_games_uo)
    data = frame_uo.values
    data = data.astype(float)

    ou_predictions_array = []

    for row in data:
        ou_predictions_array.append(xgb_uo.predict(xgb.DMatrix(np.array([row]))))

    frame_spread = copy.deepcopy(frame_ml)
    frame_spread['Spread'] = np.asarray(home_spread)
    data = frame_spread.values
    data = data.astype(float)

    spread_predictions_array = []

    for row in data:
        spread_predictions_array.append(xgb_spread.predict(xgb.DMatrix(np.array([row]))))

    count = 0
    for game in games:
        home_team = game[0]
        away_team = game[1]
        winner = int(np.argmax(ml_predictions_array[count]))
        under_over = int(np.argmax(ou_predictions_array[count]))
        winner_confidence = ml_predictions_array[count]
        un_confidence = ou_predictions_array[count]
        if winner == 1:
            try:
                winner_confidence = round(winner_confidence[0][1] * 100, 1)
            except:
                winner_confidence = round(winner_confidence[0] * 100, 1)
            if under_over == 0:
                try:
                    un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                except:
                    un_confidence = round(ou_predictions_array[count][0] * 100, 1)
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                    Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
            else:
                try:
                    un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                except:
                    un_confidence = round(ou_predictions_array[count][0] * 100, 1)
                print(
                    Fore.GREEN + home_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ' vs ' + Fore.RED + away_team + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
        else:
            try:
                winner_confidence = round(winner_confidence[0][0] * 100, 1)
            except:
                winner_confidence = round(winner_confidence[0] * 100, 1)
            if under_over == 0:
                try:
                    un_confidence = round(ou_predictions_array[count][0][0] * 100, 1)
                except:
                    un_confidence = round(ou_predictions_array[count][0] * 100, 1)
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.MAGENTA + 'UNDER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)
            else:
                try:
                    un_confidence = round(ou_predictions_array[count][0][1] * 100, 1)
                except:
                    un_confidence = round(ou_predictions_array[count][0] * 100, 1)
                print(
                    Fore.RED + home_team + Style.RESET_ALL + ' vs ' + Fore.GREEN + away_team + Style.RESET_ALL + Fore.CYAN + f" ({winner_confidence}%)" + Style.RESET_ALL + ': ' +
                    Fore.BLUE + 'OVER ' + Style.RESET_ALL + str(
                        todays_games_uo[count]) + Style.RESET_ALL + Fore.CYAN + f" ({un_confidence}%)" + Style.RESET_ALL)

        try:
            ev_home = float(Expected_Value.expected_value(ml_predictions_array[count][0][1], int(home_team_odds[count])))
            ev_away = float(Expected_Value.expected_value(ml_predictions_array[count][0][0], int(away_team_odds[count])))
        except:
            ev_home = float(Expected_Value.expected_value(ml_predictions_array[count][0], int(home_team_odds[count])))
            ev_away = float(Expected_Value.expected_value(1 - ml_predictions_array[count][0], int(away_team_odds[count])))
        favorite = home_team if ev_home > 0 else away_team if ev_away > 0 else None
        if favorite != None:
            try:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, home_team_odds[count], away_team_odds[count], ml_predictions_array[count][0][1], ml_predictions_array[count][0][0], ev_home, ev_away, 'ML', favorite + ' ML')
            except:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, home_team_odds[count], away_team_odds[count], ml_predictions_array[count][0], 1 - ml_predictions_array[count][0], ev_home, ev_away, 'ML', favorite + ' ML')

        try:
            ev_home = float(Expected_Value.expected_value(spread_predictions_array[count][0][1], -110))
            ev_away = float(Expected_Value.expected_value(spread_predictions_array[count][0][0], -110))
        except:
            ev_home = float(Expected_Value.expected_value(spread_predictions_array[count][0], -110))
            ev_away = float(Expected_Value.expected_value(1 - spread_predictions_array[count][0], -110))
        favorite = home_team if ev_home > 0 else away_team if ev_away > 0 else None
        spread = float(home_spread[count]) if ev_home > 0 else float(away_spread[count]) if ev_away > 0 else None
        if spread != None: spread = ('+' + str(spread)) if spread > 0 else str(spread)
        if favorite != None and spread != None:
            try:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, -110, -110, spread_predictions_array[count][0][1], spread_predictions_array[count][0][0], ev_home, ev_away, 'Spread', favorite + ' ' + spread)
            except:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, -110, -110, spread_predictions_array[count][0], 1 - spread_predictions_array[count][0], ev_home, ev_away, 'Spread', favorite + ' ' + spread)

        try:
            ev_over = float(Expected_Value.expected_value(ou_predictions_array[count][0][1], -110))
            ev_under = float(Expected_Value.expected_value(ou_predictions_array[count][0][0], -110))
        except:
            ev_over = float(Expected_Value.expected_value(ou_predictions_array[count][0], -110))
            ev_under = float(Expected_Value.expected_value(1 - ou_predictions_array[count][0], -110))
        favorite = 'O' if ev_over > 0 else 'U' if ev_under > 0 else None
        if favorite != None:
            try:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, -110, -110, ou_predictions_array[count][0][1], ou_predictions_array[count][0][0], ev_over, ev_under, 'O/U', favorite + ' ' + str(todays_games_uo[count]))
            except:
                add_to_results(date.today().strftime('%Y-%m-%d'), home_team, away_team, -110, -110, ou_predictions_array[count][0], 1 - ou_predictions_array[count][0], ev_over, ev_under, 'O/U', favorite + ' ' + str(todays_games_uo[count]))


        count += 1

    if kelly_criterion:
        print("------------Expected Value & Kelly Criterion-----------")
    else:
        print("---------------------Expected Value--------------------")
    count = 0
    for game in games:
        home_team = game[0]
        away_team = game[1]
        ev_home = ev_away = 0
        if home_team_odds[count] and away_team_odds[count]:
            ev_home = float(Expected_Value.expected_value(ml_predictions_array[count][0][1], int(home_team_odds[count])))
            ev_away = float(Expected_Value.expected_value(ml_predictions_array[count][0][0], int(away_team_odds[count])))
        expected_value_colors = {'home_color': Fore.GREEN if ev_home > 0 else Fore.RED,
                        'away_color': Fore.GREEN if ev_away > 0 else Fore.RED}
        bankroll_descriptor = ' Fraction of Bankroll: '
        bankroll_fraction_home = bankroll_descriptor + str(kc.calculate_kelly_criterion(home_team_odds[count], ml_predictions_array[count][0][1])) + '%'
        bankroll_fraction_away = bankroll_descriptor + str(kc.calculate_kelly_criterion(away_team_odds[count], ml_predictions_array[count][0][0])) + '%'

        print(home_team + ' EV: ' + expected_value_colors['home_color'] + str(ev_home) + Style.RESET_ALL + (bankroll_fraction_home if kelly_criterion else ''))
        print(away_team + ' EV: ' + expected_value_colors['away_color'] + str(ev_away) + Style.RESET_ALL + (bankroll_fraction_away if kelly_criterion else ''))
        count += 1

    deinit()
