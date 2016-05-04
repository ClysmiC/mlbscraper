from bs4 import BeautifulSoup
from urllib.request import urlopen
from .mlb_scraper import BaseMlbScraper, GameStatus, InningPart

import datetime
import json

class MlbScraperMlbApi(BaseMlbScraper):
    def __init__(self):
        super(MlbScraperMlbApi, self).__init__()
        self.scrapeTarget = "http://gd2.mlb.com/components/game/mlb/"
        self.mlbApiTeamNames = {}
        self.mlbApiTeamNames["ARI"] = "D-backs"
        self.mlbApiTeamNames["ATL"] = "Braves"
        self.mlbApiTeamNames["BAL"] = "Orioles"
        self.mlbApiTeamNames["BOS"] = "Red Sox"
        self.mlbApiTeamNames["CHC"] = "Cubs"
        self.mlbApiTeamNames["CHW"] = "White Sox"
        self.mlbApiTeamNames["CIN"] = "Reds"
        self.mlbApiTeamNames["CLE"] = "Indians"
        self.mlbApiTeamNames["COL"] = "Rockies"
        self.mlbApiTeamNames["DET"] = "Tigers"
        self.mlbApiTeamNames["HOU"] = "Astros"
        self.mlbApiTeamNames["KC"]  = "Royals"
        self.mlbApiTeamNames["LAA"] = "Angels"
        self.mlbApiTeamNames["LAD"] = "Dodgers"
        self.mlbApiTeamNames["MIA"] = "Marlins"
        self.mlbApiTeamNames["MIL"] = "Brewers"
        self.mlbApiTeamNames["MIN"] = "Twins"
        self.mlbApiTeamNames["NYM"] = "Mets"
        self.mlbApiTeamNames["NYY"] = "Yankees"
        self.mlbApiTeamNames["OAK"] = "Athletics"
        self.mlbApiTeamNames["PHI"] = "Phillies"
        self.mlbApiTeamNames["PIT"] = "Pirates"
        self.mlbApiTeamNames["SD"]  = "Padres"
        self.mlbApiTeamNames["SEA"] = "Mariners"
        self.mlbApiTeamNames["SF"]  = "Giants"
        self.mlbApiTeamNames["STL"] = "Cardinals"
        self.mlbApiTeamNames["TB"]  = "Rays"
        self.mlbApiTeamNames["TEX"] = "Rangers"
        self.mlbApiTeamNames["TOR"] = "Blue Jays"
        self.mlbApiTeamNames["WAS"] = "Nationals"
        
        
    def getGameInfo(self, team, date=None):
        if type(team) is not str:
            raise TypeError("Team name must be a string.")

        team = self.getTeamNick(team)
        
        if team is None:
            raise ValueError("Invalid team name.")

        team = self.mlbApiTeamNames[team]

        if date is None:
            date = datetime.date.today()

        dateString = "year_" +  str(date.year).zfill(4) + "/month_" + str(date.month).zfill(2) + "/day_" + str(date.day).zfill(2) + "/master_scoreboard.json"
        
        jsonString = urlopen(self.scrapeTarget + dateString).read().decode("utf-8")
        scoreboard = json.loads(jsonString)

        game = {}
        game["status"] = GameStatus.NoGame
        
        for gameData in scoreboard["data"]["games"]["game"]:
            if gameData["home_team_name"] == team or gameData["away_team_name"] == team:

                game["away"] = {}
                game["home"] = {}
                
                game["away"]["name"] = self.getTeamNick(gameData["away_team_name"])
                game["home"]["name"] = self.getTeamNick(gameData["home_team_name"])

                statusString = gameData["status"]["status"]
                
                # TODO: check the api when there are rainouts or rain
                # delays. I suspect that these are shown in this
                # status attribute.
                if statusString == "Preview":
                    game["status"] = GameStatus.Pre
                elif statusString == "In Progress":
                    game["status"] = GameStatus.Live
                elif statusString == "Final":
                    game["status"] = GameStatus.Post
                else:
                    raise Exception("Unknown status string: " + statusString)
                
                # TODO: Handle pre-game. Return following extra info:
                #
                # Start time
                # Starting Pitchers + Records
                if game["status"] == GameStatus.Pre:
                    pass

                
                if game["status"] == GameStatus.Live:

                    game["situation"] = {}
                    
                    # If you want first + last name, use a string like this:
                    # gameData["pitcher"]["first"] + " " + gameData["pitcher"]["last"]
                    game["situation"]["pitcher"] = gameData["pitcher"]["name_display_roster"]
                    game["satuation"]["batter"] = gameData["batter"]["name_display_roster"]
                    
                    game["situation"]["balls"]   = gameData["status"]["b"]
                    game["situation"]["strikes"] = gameData["status"]["s"]
                    game["situation"]["outs"]    = gameData["status"]["o"]

                    game["inning"] = {}
                    game["inning"]["number"] = gameData["status"]["inning"]

                    isTopInningString = gameData["status"]["top_inning"]
                    
                    if isTopInningString == "Y":
                        
                        if gameData["status"]["inning_state"] == "Middle":
                            game["inning"]["part"] = InningPart.Mid
                        else:
                            game["inning"]["part"] = InningPart.Top
                            
                    else:
                        
                        if gameData["status"]["inning_state"] == "End":
                            game["inning"]["part"] = InningPart.End
                        else:
                            game["inning"]["part"] = InningPart.Bot
                    

                # TODO: Handle post-game. Return following extra info:
                #
                # Winning pitcher
                # Losing Pitcher
                # Save Pitcher (if one exists)
                if game["status"] == GameStatus.Post:
                    pass


                if game["status"] in (GameStatus.Live, GameStatus.Post):
                    game["away"]["hits"] = gameData["linescore"]["h"]["away"]
                    game["home"]["hits"] = gameData["linescore"]["h"]["home"]
                    game["away"]["runs"] = gameData["linescore"]["r"]["away"]
                    game["home"]["runs"] = gameData["linescore"]["r"]["home"]
                    game["away"]["errors"] = gameData["linescore"]["e"]["away"]
                    game["home"]["errors"] = gameData["linescore"]["e"]["home"]

                    awayScoreByInning = []
                    homeScoreByInning = []
                    
                    for inning in gameData["linescore"]["inning"]:
                        awayScoreByInning.append(inning["away"])

                        if "home" in inning:
                            homeScoreByInning.append(inning["home"])
                        elif game["status"] == GameStatus.Post:
                            # Should only occur in inning 9
                            homeScoreByInning.append("X")

                    # Pad unplayed innings with dashes
                    while len(awayScoreByInning) < 9:
                        awayScoreByInning.append("-")
                    while len(homeScoreByInning) < 9:
                        homeScoreByInning.append("-")
                        
                    game["away"]["scoreByInning"] = awayScoreByInning
                    game["home"]["scoreByInning"] = homeScoreByInning
                
                # Breaking out of looping over all games
                break
            
        return game
