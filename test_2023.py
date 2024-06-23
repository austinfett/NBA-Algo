import xgboost as xgb
import pandas as pd
import numpy as np
import sqlite3
from colorama import Fore, Style, init, deinit
from src.Utils import Expected_Value
import matplotlib.pyplot as plt
import datetime

xgb_ml = xgb.Booster()
# xgb_ml.load_model('Models/XGBoost_Models/XGBoost_70.7%_ML-4.json')
xgb_ml.load_model('Models/XGBoost_Models/XGBoost_69.6%_ML-min.json')
xgb_uo = xgb.Booster()
# xgb_uo.load_model('Models/XGBoost_Models/XGBoost_55.4%_UO-5.json')
xgb_uo.load_model('Models/XGBoost_Models/XGBoost_55.4%_UO-min.json')
xgb_spread = xgb.Booster()
# xgb_spread.load_model('Models/XGBoost_Models/XGBoost_62.9%_Spread-4.json')
xgb_spread.load_model('Models/XGBoost_Models/XGBoost_63.5%_Spread-min.json')

def payout(odds):
    if odds > 0:
        return odds
    else:
        return (100 / (-1 * odds)) * 100

def test_season(chart=False):
    con = sqlite3.connect('Data/dataset.sqlite')
    dataset = con.cursor()

    unit_size = 100
    count = ml_wins = ml_losses = ml_money = ou_wins = ou_losses = ou_money = spread_wins = spread_losses = spread_money = wl_wins = wl_losses = wl_money = 0
    day_1 = '2023-10-26'
    daily_profit = {day_1: {'ML': 0, 'Spread': 0, 'O/U': 0, 'Total': 0}}

    for row in dataset.execute(f"""SELECT * FROM `dataset_2023-24`"""):
        # if count == 5: break

        data = pd.DataFrame(row).T
        # Columns 121 and 122 are home_ml and away_ml respectively
        curr_date = data.iloc[0, 114]
        c = datetime.datetime(int(curr_date.split('-')[0]), int(curr_date.split('-')[1]), int(curr_date.split('-')[2]))
        if c < datetime.datetime(2024, 3, 12): continue
        # if c != datetime.datetime(2024, 4, 6): continue
        home_win = data.iloc[0, 118]
        ou_cover = data.iloc[0, 120]
        spread_cover = data.iloc[0, 122]
        home_ml = data.iloc[0, 123]
        away_ml = data.iloc[0, 124]
        # Columns 56 and 113 are min_p and min_p.1 respectively
        data_cleaned = data.drop(columns=[0, 1, 57, 58, 114, 117, 118, 120, 122, 123, 124])
        
        for r in data_cleaned.values.astype(float):
            ml = xgb_ml.predict(xgb.DMatrix(np.array([r])))
            ou = xgb_uo.predict(xgb.DMatrix(np.array([r])))
            spread = xgb_spread.predict(xgb.DMatrix(np.array([r])))

        try:
            ev_home = float(Expected_Value.expected_value(ml[0][1], int(home_ml)))
            ev_away = float(Expected_Value.expected_value(ml[0][0], int(away_ml)))
        except:
            ev_home = float(Expected_Value.expected_value(ml[0], -110))
            ev_away = float(Expected_Value.expected_value(1 - ml[0], -110))
        try:
            ev_over = float(Expected_Value.expected_value(ou[0][1], -110))
            ev_under = float(Expected_Value.expected_value(ou[0][0], -110))
        except:
            ev_over = float(Expected_Value.expected_value(ou[0], -110))
            ev_under = float(Expected_Value.expected_value(1 - ou[0], -110))
        try:
            ev_home_spread = float(Expected_Value.expected_value(spread[0][1], -110))
            ev_away_spread = float(Expected_Value.expected_value(spread[0][0], -110))
        except:
            ev_home_spread = float(Expected_Value.expected_value(spread[0], -110))
            ev_away_spread = float(Expected_Value.expected_value(1 - spread[0], -110))

        # print(f"""({ev_home}, {ev_away}), ({ev_home_spread}, {ev_away_spread}), ({ev_over}, {ev_under})""")

        if ev_home > 0:
            if home_win == 1:
                ml_wins += 1
                pay = payout(home_ml) / 100 * unit_size
                ml_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['ML'] = daily_profit.get(curr_date, {}).get('ML', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay
            elif home_win == 0:
                ml_losses += 1
                ml_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['ML'] = daily_profit.get(curr_date, {}).get('ML', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size
        elif ev_away > 0:
            if home_win == 0:
                ml_wins += 1
                pay = payout(away_ml) / 100 * unit_size
                ml_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['ML'] = daily_profit.get(curr_date, {}).get('ML', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay                
            elif home_win == 1:
                ml_losses += 1
                ml_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['ML'] = daily_profit.get(curr_date, {}).get('ML', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size

        if ev_over > 0:
            if ou_cover == 1:
                ou_wins += 1
                pay = payout(-110) / 100 * unit_size
                ou_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['O/U'] = daily_profit.get(curr_date, {}).get('O/U', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay
            elif ou_cover == 0:
                ou_losses += 1
                ou_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['O/U'] = daily_profit.get(curr_date, {}).get('O/U', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size
        elif ev_under > 0:
            if ou_cover == 0:
                ou_wins += 1
                pay = payout(-110) / 100 * unit_size
                ou_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['O/U'] = daily_profit.get(curr_date, {}).get('O/U', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay
            elif ou_cover == 1:
                ou_losses += 1
                ou_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['O/U'] = daily_profit.get(curr_date, {}).get('O/U', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size

        if ev_home_spread > 0:
            if spread_cover == 1:
                spread_wins += 1
                pay = payout(-110) / 100 * unit_size
                spread_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['Spread'] = daily_profit.get(curr_date, {}).get('Spread', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay
            elif spread_cover == 0:
                spread_losses += 1
                spread_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['Spread'] = daily_profit.get(curr_date, {}).get('Spread', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size
        elif ev_away_spread > 0:
            if spread_cover == 0:
                spread_wins += 1
                pay = payout(-110) / 100 * unit_size
                spread_money += pay
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['Spread'] = daily_profit.get(curr_date, {}).get('Spread', 0) + pay
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) + pay
            elif spread_cover == 1:
                spread_losses += 1
                spread_money -= unit_size
                daily_profit[curr_date] = daily_profit.get(curr_date, {})
                daily_profit[curr_date]['Spread'] = daily_profit.get(curr_date, {}).get('Spread', 0) - unit_size
                daily_profit[curr_date]['Total'] = daily_profit.get(curr_date, {}).get('Total', 0) - unit_size

        if ml[0][1] > 0.5:
            if home_win == 1:
                wl_wins += 1
                wl_money += payout(home_ml) / 100 * unit_size
            elif home_win == 0:
                wl_losses += 1
                wl_money -= unit_size
        elif ml[0][0] > 0.5:
            if home_win == 0:
                wl_wins += 1
                wl_money += payout(away_ml) / 100 * unit_size
            elif home_win == 1:
                wl_losses += 1
                wl_money -= unit_size

        count += 1

    dataset.close()
    con.close()

    ml_color = Fore.GREEN if ml_money > 0 else Fore.RED if ml_money < 0 else Fore.YELLOW
    spread_color = Fore.GREEN if spread_money > 0 else Fore.RED if spread_money < 0 else Fore.YELLOW
    ou_color = Fore.GREEN if ou_money > 0 else Fore.RED if ou_money < 0 else Fore.YELLOW
    total_wins = ml_wins + ou_wins + spread_wins
    total_losses = ml_losses + ou_losses + spread_losses
    total_money = ml_money + ou_money + spread_money
    total_color = Fore.GREEN if total_money > 0 else Fore.RED if total_money < 0 else Fore.YELLOW
    wl_color = Fore.GREEN if wl_money > 0 else Fore.RED if wl_money < 0 else Fore.YELLOW

    ml_percent = ml_wins / (ml_wins + ml_losses) * 100 if ml_wins + ml_losses > 0 else 0.0
    spread_percent = spread_wins / (spread_wins + spread_losses) * 100 if spread_wins + spread_losses > 0 else 0.0
    ou_percent = ou_wins / (ou_wins + ou_losses) * 100 if ou_wins + ou_losses > 0 else 0.0
    total_percent = total_wins / (total_wins + total_losses) * 100 if total_wins + total_losses > 0 else 0.0
    wl_percent = wl_wins / (wl_wins + wl_losses) * 100 if wl_wins + wl_losses > 0 else 0.0
    wl_string = f"{wl_wins}-{wl_losses}"
    ml_padding1 = ou_padding1 = spread_padding1 = total_padding1 = wl_padding1 = ml_padding2 = ou_padding2 = spread_padding2 = total_padding2 = wl_padding2 = ''
    long_padding1 = max(len(str(ml_money).split('.')[0]), len(str(ou_money).split('.')[0]), len(str(spread_money).split('.')[0]), len(str(total_money).split('.')[0]), len(str(wl_money).split('.')[0]))
    long_padding2 = max(len(str(ml_percent).split('.')[0]), len(str(ou_percent).split('.')[0]), len(str(spread_percent).split('.')[0]), len(str(total_percent).split('.')[0]), len(str(wl_percent).split('.')[0]))

    for _ in range(len(str(ml_money).split('.')[0]), long_padding1): ml_padding1 += ' '
    for _ in range(len(str(spread_money).split('.')[0]), long_padding1): spread_padding1 += ' '
    for _ in range(len(str(ou_money).split('.')[0]), long_padding1): ou_padding1 += ' '
    for _ in range(len(str(total_money).split('.')[0]), long_padding1): total_padding1 += ' '
    for _ in range(len(str(wl_money).split('.')[0]), long_padding1): wl_padding1 += ' '
    for _ in range(len(str(ml_percent).split('.')[0]), long_padding2): ml_padding2 += ' '
    for _ in range(len(str(spread_percent).split('.')[0]), long_padding2): spread_padding2 += ' '
    for _ in range(len(str(ou_percent).split('.')[0]), long_padding2): ou_padding2 += ' '
    for _ in range(len(str(total_percent).split('.')[0]), long_padding2): total_padding2 += ' '
    for _ in range(len(str(wl_percent).split('.')[0]), long_padding2): wl_padding2 += ' '

    init()
    print("----------------------Pick Results---------------------")
    print(f"""\tW/L:     \t{wl_color    }${format(wl_money, '.2f')    }{wl_padding1    }     {format(wl_percent, '.1f')    }%{ml_padding2    }     {wl_string                  }{Style.RESET_ALL}""".replace('$-','-$'))
    print("-------------------------------------------------------")
    print(f"""\tML:      \t{ml_color    }${format(ml_money, '.2f')    }{ml_padding1    }     {format(ml_percent, '.1f')    }%{ml_padding2    }     {ml_wins    }-{ml_losses    }{Style.RESET_ALL}""".replace('$-','-$'))
    print(f"""\tSpread:  \t{spread_color}${format(spread_money, '.2f')}{spread_padding1}     {format(spread_percent, '.1f')}%{spread_padding2}     {spread_wins}-{spread_losses}{Style.RESET_ALL}""".replace('$-','-$'))
    print(f"""\tO/U:     \t{ou_color    }${format(ou_money, '.2f')    }{ou_padding1    }     {format(ou_percent, '.1f')    }%{ou_padding2    }     {ou_wins    }-{ou_losses    }{Style.RESET_ALL}""".replace('$-','-$'))
    print("-------------------------------------------------------")
    print(f"""\tTotal:   \t{total_color }${format(total_money, '.2f') }{total_padding1 }     {format(total_percent, '.1f') }%{total_padding2 }     {total_wins }-{total_losses }{Style.RESET_ALL}""".replace('$-','-$'))
    deinit()

    if chart:
        total_profit = daily_profit.copy()
        skip_first = True
        last_day = ''
        for day in daily_profit.keys():
            if not skip_first:
                for bet in daily_profit[day_1].keys():
                    total_profit[day][bet] = total_profit[day].get(bet, 0) + total_profit[last_day].get(bet, 0)

            last_day = day
            skip_first = False

        ml_values = [total_profit[day]['ML'] for day in total_profit.keys()]
        spread_values = [total_profit[day]['Spread'] for day in total_profit.keys()]
        ou_values = [total_profit[day]['O/U'] for day in total_profit.keys()]
        total_values = [total_profit[day]['Total'] for day in total_profit.keys()]

        plt.plot(total_profit.keys(), ml_values, marker='.', c='r', ls='--')
        plt.plot(total_profit.keys(), spread_values, marker='.', c='b', ls='--')
        plt.plot(total_profit.keys(), ou_values, marker='.', c='g', ls='--')
        plt.plot(total_profit.keys(), total_values, marker='.', c='purple')
        plt.xlabel('Date')
        plt.ylabel('Total Profit')
        plt.title('Pick Profit')
        plt.legend(['ML', 'Spread', 'O/U', 'Total'], loc='lower left')
        plt.show()

test_season(chart=True)