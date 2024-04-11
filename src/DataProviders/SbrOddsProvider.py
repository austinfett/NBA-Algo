from sbrscrape import Scoreboard

class SbrOddsProvider:
    
    """ Abbreviations dictionary for team location which are sometimes saved with abbrev instead of full name. 
    Moneyline options name require always full name
    Returns:
        string: Full location name
    """    

    def __init__(self, sportsbook="fanduel"):
        sb = Scoreboard(sport="NBA")
        self.games = sb.games if hasattr(sb, 'games') else []
        self.sportsbook = sportsbook

    
    def get_odds(self):
        """Function returning odds from Sbr server's json content

        Returns:
            dictionary: [home_team_name + ':' + away_team_name: { home_team: money_line_odds, away_team: money_line_odds }, under_over_odds: val]
        """
        dict_res = {}
        for game in self.games:
            # Get team names
            home_team_name = game['home_team'].replace("Los Angeles Clippers", "LA Clippers")
            away_team_name = game['away_team'].replace("Los Angeles Clippers", "LA Clippers")
            
            money_line_home_value = money_line_away_value = totals_value = home_line = away_line = None

            # Get money line bet values
            if self.sportsbook in game['home_ml']:
                money_line_home_value = game['home_ml'][self.sportsbook]
            if self.sportsbook in game['away_ml']:
                money_line_away_value = game['away_ml'][self.sportsbook]
            
            # Get totals bet value
            if self.sportsbook in game['total']:
                totals_value = game['total'][self.sportsbook]

            # Get spreads bet value
            if self.sportsbook in game['home_spread']:
                home_line = game['home_spread'][self.sportsbook]
            if self.sportsbook in game['away_spread']:
                away_line = game['away_spread'][self.sportsbook]

            if money_line_home_value is None: money_line_home_value = input(home_team_name + ' ML: ')
            if money_line_away_value is None: money_line_away_value = input(away_team_name + ' ML: ')
            if totals_value is None: totals_value = input(away_team_name + ' at ' + home_team_name + ' Total: ')
            if home_line is None: home_line = input(home_team_name + ' Spread: ')
            if away_line is None: away_line = input(away_team_name + ' Spread: ')
            
            dict_res[home_team_name + ':' + away_team_name] =  { 
                'under_over_odds': totals_value,
                home_team_name: { 'money_line_odds': money_line_home_value,
                                  'line': home_line }, 
                away_team_name: { 'money_line_odds': money_line_away_value,
                                  'line': away_line }
            }
        return dict_res