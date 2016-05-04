from bs4 import BeautifulSoup
from urllib.request import urlopen
from .mlb_scraper import BaseMlbScraper, GameStatus, InningPart

import datetime
import json

class MlbScraperMlbApi(BaseMlbScraper):
    def __init__(self):
        super(MlbScraperMlbApi, self).__init__()
        self.gameScrapeTarget = "http://gd2.mlb.com/components/game/mlb/"

        # Couldn't find this in all one concentrated location in the
        # MLB API, and the MLB website had to load javascript. Espn
        # loads the info just fine though
        self.standingsScrapeTarget = "http://espn.go.com/mlb/standings"
        self.wildcardStandingsScrapeTarget = "http://espn.go.com/mlb/standings/_/view/wild-card"
        
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
        
        jsonString = urlopen(self.gameScrapeTarget + dateString).read().decode("utf-8")
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
                    game["startTime"] = gameData["time"]

                    if gameData["away_probable_pitcher"]["name_display_roster"] != "":
                        game["away"]["starter"] = {}
                        game["away"]["starter"]["name"] = gameData["away_probable_pitcher"]["name_display_roster"]
                        game["away"]["starter"]["wins"] = gameData["away_probable_pitcher"]["wins"]
                        game["away"]["starter"]["losses"] = gameData["away_probable_pitcher"]["losses"]
                        game["away"]["starter"]["era"] = gameData["away_probable_pitcher"]["era"]
                        
                    if gameData["home_probable_pitcher"]["name_display_roster"] != "":
                        game["home"]["starter"] = {}
                        game["home"]["starter"]["name"] = gameData["home_probable_pitcher"]["name_display_roster"]
                        game["home"]["starter"]["wins"] = gameData["home_probable_pitcher"]["wins"]
                        game["home"]["starter"]["losses"] = gameData["home_probable_pitcher"]["losses"]
                        game["home"]["starter"]["era"] = gameData["home_probable_pitcher"]["era"]
                    
                
                if game["status"] == GameStatus.Live:

                    game["situation"] = {}
                    
                    # If you want first + last name, use a string like this:
                    # gameData["pitcher"]["first"] + " " + gameData["pitcher"]["last"]
                    game["situation"]["pitcher"] = gameData["pitcher"]["name_display_roster"]
                    game["situation"]["batter"] = gameData["batter"]["name_display_roster"]
                    
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
                    

                # Add pitcher information for finished games.  This
                # includes winning, losing, and saving pitcher, and
                # their relevant updated stats (wins, losses, saves,
                # save opportunities).
                if game["status"] == GameStatus.Post:
                    game["pitcherResults"] = {}
                    game["pitcherResults"]["win"] = {}
                    game["pitcherResults"]["loss"] = {}
                    
                    game["pitcherResults"]["win"]["name"] = gameData["winning_pitcher"]["name_display_roster"]
                    game["pitcherResults"]["win"]["updatedWins"] = gameData["winning_pitcher"]["wins"]
                    game["pitcherResults"]["win"]["updatedLosses"] = gameData["winning_pitcher"]["losses"]

                    game["pitcherResults"]["loss"]["name"] = gameData["losing_pitcher"]["name_display_roster"]
                    game["pitcherResults"]["loss"]["updatedWins"] = gameData["losing_pitcher"]["wins"]
                    game["pitcherResults"]["loss"]["updatedLosses"] = gameData["losing_pitcher"]["losses"]                    
                    if gameData["savePitcher"]["name_display_roster"] != "":
                        game["pitcherResults"]["save"] = {}
                        game["pitcherResults"]["save"]["name"] = gameData["save_pitcher"]["name_display_roster"]
                        game["pitcherResults"]["save"]["updatedSaves"] = gameData["save_pitcher"]["saves"]
                        game["pitcherResults"]["save"]["updatedSaveOpportunities"] = gameData["save_pitcher"]["svo"]


                # Add score by inning for home and away teams. Fill
                # not-yet-completed innings with '-', and unnecessary
                # bottom of the last inning with 'X'
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
                            # Should only occur in inning 9 or beyond
                            homeScoreByInning.append("X")

                    # Pad unplayed innings with dashes
                    while len(awayScoreByInning) < 9:
                        awayScoreByInning.append("-")
                    while len(homeScoreByInning) < 9:
                        homeScoreByInning.append("-")
                        
                    game["away"]["scoreByInning"] = awayScoreByInning
                    game["home"]["scoreByInning"] = homeScoreByInning
                
                # Breaking out of looping over all games. Since our
                # game was found and the data was filled out, we
                # shouldn't be able to find another game with our team
                # name.
                #
                # TODO: Look at the API output when there is a
                # double-header... see what the info looks like and
                # figure out how we handle that. We might have to
                # _not_ break out of the loop and figure out which
                # game(s) are active, and which to display ?
                break
            
        return game


    def getTeamRecord(self, team):
        if type(team) is not str:
            raise TypeError("Team name must be a string.")

        team = self.getTeamNick(team)
        
        if team is None:
            raise ValueError("Invalid team name.")

        html = urlopen(self.standingsScrapeTarget)
        soup = BeautifulSoup(html, "lxml")

        tags = soup.find("abbr", text=team)
        row = tags.find_parent(class_ = "standings-row")
        columns = row.find_all("td")

        wins = int(columns[1].string)
        losses = int(columns[2].string)
        
        return wins, losses
        
    def getDivisionStandings(self, divisionAbbrev):
        wildCardQuery = False
        
        if type(divisionAbbrev) is not str:
            raise TypeError("Division name must be a string.")

        divisionAbbrev = self.getDivisionNick(divisionAbbrev)
        
        if divisionAbbrev is None:
            raise ValueError("Invalid division name.")

        if divisionAbbrev[0:2] == "AL":
            league = "American League"
        else:
            league = "National League"
                
        if divisionAbbrev[-2:] == "WC":
            wildCardQuery = True
            target = self.wildcardStandingsScrapeTarget
            division = ""
            
        else:
            target = self.standingsScrapeTarget

            if divisionAbbrev[2] == "W":
                division = "West"
            elif divisionAbbrev[2] == "C":
                division = "Central"
            else:
                division = "East"

        html = urlopen(target)
        soup = BeautifulSoup(html, "lxml")

        tableHeader = soup.find(class_="long-caption", text=league).parent
        table = tableHeader.find_next_sibling(class_="responsive-table-wrap")
        divisionHeader = table.find("span", text=division)

        divisionHeader = divisionHeader.find_parent(class_="standings-categories")

        rowsToGet = (12 if wildCardQuery else 5)
        
        divisionRows = divisionHeader.find_next_siblings(class_="standings-row", limit=rowsToGet)

        standings = []

        for row in divisionRows:
            entry = {}
            entry["name"] = str(row.find("abbr").string)

            columns = row.find_all("td")
            entry["wins"] = int(columns[1].string)
            entry["losses"] = int(columns[2].string)

            gamesBackString = columns[4].string

            if gamesBackString[0] == "+":
                entry["gb"] = -float(gamesBackString[1:])
            elif gamesBackString[0] == "-":
                entry["gb"] = float(0)
            else:
                entry["gb"] = float(gamesBackString)

            standings.append(entry)

        return standings
