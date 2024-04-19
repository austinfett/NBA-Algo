import sqlite3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import MaxRetryError
from selenium import webdriver
from colorama import Fore, Style, init, deinit
from datetime import date
import matplotlib.pyplot as plt
from sbrscrape import Scoreboard

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

def expected_value(Pwin, odds):
    Ploss = 1 - Pwin
    Mwin = payout(odds)
    return round((Pwin * Mwin) - (Ploss * 100), 2)

def payout(odds):
    if odds > 0:
        return odds
    else:
        return (100 / (-1 * odds)) * 100

def update_picks():
    con = sqlite3.connect('Data/results.sqlite')
    cur = con.cursor()
    dataset = con.cursor()
    found_list = []

    for row in dataset.execute("""SELECT `Date`, `Home_Team`, `Home_EV`, `Bet_Type`, `Bet`, `Results` FROM `Picks`"""):
        if row[5] != None:
            continue

        home_points = away_points = None
        already_found = False
        for found in found_list:
            if found[0] == row[0] and found[1] == row[1]:
                home_points = found[2]
                away_points = found[3]
                already_found = True
                break

        if not already_found:
            games = Scoreboard(sport='NBA', date=(row[0])).games

            for game in games:
                home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")

                if home_team_name == row[1]:
                    status = game['status']

                    if 'Final' in status:
                        # Get team scores
                        home_points = game['home_score']
                        away_points = game['away_score']
                        found_list.append([row[0], row[1], home_points, away_points])
                    else: return
                    break

        results = None

        if home_points != None and away_points != None:
            if row[3] == 'ML':
                if row[2] > 0:
                    if home_points > away_points:
                        results = 'W'
                    else:
                        results = 'L'
                elif row[2] < 0:
                    if away_points > home_points:
                        results = 'W'
                    else:
                        results = 'L'
            elif row[3] == 'O/U':
                line = float(row[4].split(' ')[1])
                if row[2] > 0:
                    if home_points + away_points > line:
                        results = 'W'
                    elif home_points + away_points < line:
                        results = 'L'
                    else:
                        results = 'P'
                elif row[2] < 0:
                    if home_points + away_points < line:
                        results = 'W'
                    elif home_points + away_points > line:
                        results = 'L'
                    else:
                        results = 'P'
            elif row[3] == 'Spread':
                line = float(row[4].split(' ')[-1].replace('+', ''))
                if row[2] > 0:
                    if away_points - home_points < line:
                        results = 'W'
                    elif away_points - home_points > line:
                        results = 'L'
                    else:
                        results = 'P'
                elif row[2] < 0:
                    if home_points - away_points < line:
                        results = 'W'
                    elif home_points - away_points > line:
                        results = 'L'
                    else:
                        results = 'P'

            cur.execute(f"""UPDATE `Picks` SET `Results` = '{results}' WHERE `Date` = '{row[0]}' AND `Home_Team` = '{row[1]}' AND `Bet_Type` = '{row[3]}'""")
            con.commit()

    dataset.close()
    cur.close()
    con.close()

def check_results(update=True, chart=False):
    if update:
        update_picks()

    con = sqlite3.connect('Data/results.sqlite')
    dataset = con.cursor()
    ml_wins = ml_losses = ml_money = ou_wins = ou_losses = ou_money = spread_wins = spread_losses = spread_money = wl_wins = wl_losses = wl_money = 0
    unit_size = 100
    day_1 = '2024-03-11'
    daily_profit = {day_1: {'ML': 0, 'Spread': 0, 'O/U': 0, 'Total': 0}}

    for row in dataset.execute("""SELECT `Date`, `Home_Team`, `Away_Team`, `Home_Odds`, `Away_Odds`, `Home_Percent`, `Away_Percent`, `Home_EV`, `Away_EV`, `Bet_Type`, `Bet`, `Results` FROM `Picks`"""):
        if row[11] == None:
            continue

        if row[9] == 'ML':
            if row[11] == 'W':
                ml_wins += 1
                pay = 0

                if row[7] > 0:
                    pay = payout(row[3]) / 100 * unit_size
                elif row[8] > 0:
                    pay = payout(row[4]) / 100 * unit_size

                ml_money += pay
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['ML'] = daily_profit.get(row[0], {}).get('ML', 0) + pay
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) + pay
            elif row[11] == 'L':
                ml_losses += 1
                ml_money -= unit_size
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['ML'] = daily_profit.get(row[0], {}).get('ML', 0) - unit_size
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) - unit_size
            
            if row[5] > 0.5 and row[7] > 0:
                if row[11] == 'W': 
                    wl_wins += 1
                    wl_money += payout(row[3]) / 100 * unit_size
                elif row[11] == 'L':
                    wl_losses += 1
                    wl_money -= unit_size
            elif row[5] > 0.5 and row[7] < 0:
                if row[11] == 'W':
                    wl_losses += 1
                    wl_money -= unit_size
                elif row[11] == 'L':
                    wl_wins += 1
                    wl_money += payout(row[3]) / 100 * unit_size
            elif row[6] > 0.5 and row[8] > 0:
                if row[11] == 'W':
                    wl_wins += 1
                    wl_money += payout(row[4]) / 100 * unit_size
                elif row[11] == 'L':
                    wl_losses += 1
                    wl_money -= unit_size
            elif row[6] > 0.5 and row[8] < 0:
                if row[11] == 'W':
                    wl_losses += 1
                    wl_money -= unit_size
                elif row[11] == 'L':
                    wl_wins += 1
                    wl_money += payout(row[4]) / 100 * unit_size

        elif row[9] == 'Spread':
            if row[11] == 'W':
                spread_wins += 1
                pay = 0

                if row[7] > 0:
                    pay = payout(row[4]) / 100 * unit_size
                elif row[8] > 0:
                    pay = payout(row[4]) / 100 * unit_size

                spread_money += pay
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['Spread'] = daily_profit.get(row[0], {}).get('Spread', 0) + pay
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) + pay
            elif row[11] == 'L':
                spread_losses += 1
                spread_money -= unit_size
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['Spread'] = daily_profit.get(row[0], {}).get('Spread', 0) - unit_size
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) - unit_size

        elif row[9] == 'O/U':
            if row[11] == 'W':
                ou_wins += 1
                pay = 0

                if row[7] > 0:
                    pay = payout(row[3]) / 100 * unit_size
                elif row[8] > 0:
                    pay = payout(row[4]) / 100 * unit_size

                ou_money += pay
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['O/U'] = daily_profit.get(row[0], {}).get('O/U', 0) + pay
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) + pay
            elif row[11] == 'L':
                ou_losses += 1
                ou_money -= unit_size
                daily_profit[row[0]] = daily_profit.get(row[0], {})
                daily_profit[row[0]]['O/U'] = daily_profit.get(row[0], {}).get('O/U', 0) - unit_size
                daily_profit[row[0]]['Total'] = daily_profit.get(row[0], {}).get('Total', 0) - unit_size

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
        plt.legend(['ML', 'Spread', 'O/U', 'Total'], loc='upper left')
        plt.show()

# h_o = -420
# a_o = 330
# h_p = 0.571
# a_p = 0.429
# add_to_results(date.today().strftime('%Y-%m-%d'), 'Phoenix Suns', 'Houston Rockets', h_o, a_o, h_p, a_p, float(expected_value(h_p, h_o)), float(expected_value(a_p, a_o)), 'ML', 'Houston Rockets ML')
# update_picks()
check_results(update=True, chart=False)