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
                
        
    def getGameInfo(self, team, date=None):
        if type(team) is not str:
            raise TypeError("Team name must be a string.")

        team = self.getTeamNick(team)
        
        if team is None:
            raise ValueError("Invalid team name.")

        if date is None:
            date = datetime.date.today()

        dateString = "year_" +  str(date.year).zfill(4) + "/month_" + str(date.month).zfill(2) + "/day_" + str(date.day).zfill(2) + "/master_scoreboard.json"

        try:
            jsonString = urlopen(self.gameScrapeTarget + dateString).read().decode("utf-8")
        except:
            return -1
        
        scoreboard = json.loads(jsonString)

        game = {}
        game["status"] = GameStatus.NoGame
        
        for gameData in scoreboard["data"]["games"]["game"]:
            if gameData["home_name_abbrev"] == team or gameData["away_name_abbrev"] == team:

                game["away"] = {}
                game["home"] = {}
                
                game["away"]["name"] = self.getTeamNick(gameData["away_team_name"])
                game["home"]["name"] = self.getTeamNick(gameData["home_team_name"])

                statusString = gameData["status"]["status"]
                
                # TODO: check the api when there are rainouts or rain
                # delays. I suspect that these are shown in this
                # status attribute.
                if statusString in ("Warmup", "Preview"):
                    game["status"] = GameStatus.Pre
                elif statusString in ("In Progress", "Manager Challenge"):
                    game["status"] = GameStatus.Live
                elif statusString in ("Final", "Game Over"):
                    game["status"] = GameStatus.Post
                else:
                    raise Exception("Unknown status string: " + statusString)
                

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

                    # Determine inning, and part of inning
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

                            
                    game["situation"] = {}

                    # Store baserunner names in list. Empty string
                    # means no runner on.
                    game["situation"]["runners"] = []
                    game["situation"]["pitcher"] = {}
                    game["situation"]["batter"] = {}

                    # If you want first + last name, use a string like this:
                    # gameData["pitcher"]["first"] + " " + gameData["pitcher"]["last"]
                    game["situation"]["batter"]["name"] = gameData["batter"]["name_display_roster"]
                    game["situation"]["batter"]["avg"] = gameData["batter"]["avg"]

                    game["situation"]["pitcher"]["name"] = gameData["pitcher"]["name_display_roster"]
                    game["situation"]["pitcher"]["era"] = gameData["pitcher"]["era"]

                    if "pbp" in gameData and "last" in gameData["pbp"] and gameData["pbp"]["last"] != "":
                        game["situation"]["lastPlay"] = gameData["pbp"]["last"]

                    # Mlb leaves "dangling" data between innings
                    # (Mid/End), such as the b/s/o, batter, pticher
                    # until the next inning starts (is in the
                    # Top/Bot). Between innings, I want b/s/o set to 0
                    # and I want to peek ahead to the upcoming batter
                    # and pitcher
                    if game["inning"]["part"] in (InningPart.Top, InningPart.Bot):
                        game["situation"]["balls"]   = gameData["status"]["b"]
                        game["situation"]["strikes"] = gameData["status"]["s"]
                        game["situation"]["outs"]    = gameData["status"]["o"]

                        if "runner_on_1b" in gameData["runners_on_base"]:
                            game["situation"]["runners"].append(gameData["runners_on_base"]["runner_on_1b"]["name_display_roster"])
                        else:
                            game["situation"]["runners"].append("")

                        if "runner_on_2b" in gameData["runners_on_base"]:
                            game["situation"]["runners"].append(gameData["runners_on_base"]["runner_on_2b"]["name_display_roster"])
                        else:
                            game["situation"]["runners"].append("")

                        if "runner_on_3b" in gameData["runners_on_base"]:
                            game["situation"]["runners"].append(gameData["runners_on_base"]["runner_on_3b"]["name_display_roster"])
                        else:
                            game["situation"]["runners"].append("")


                            
                    # Inning is in Mid/End, peek ahead and put that
                    # data as the situation
                    else:
                        game["situation"]["batter"]["name"] = gameData["due_up_batter"]["name_display_roster"]
                        game["situation"]["batter"]["avg"] = gameData["due_up_batter"]["avg"]
                        
                        game["situation"]["pitcher"]["name"] = gameData["opposing_pitcher"]["name_display_roster"]
                        game["situation"]["pitcher"]["era"] = gameData["opposing_pitcher"]["era"]
                        
                        game["situation"]["balls"]   = "0"
                        game["situation"]["strikes"] = "0"
                        game["situation"]["outs"]    = "0"
                        game["situation"]["runners"].append("")
                        game["situation"]["runners"].append("")
                        game["situation"]["runners"].append("")

                    

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
                    if gameData["save_pitcher"]["name_display_roster"] != "":
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

                    # If in first inning, linescore->inning directly
                    # describes first inning.  Otherwise
                    # linescore->inning is an array, with each entry
                    # describing an inning. Dumb... but I need to work
                    # around it.
                    if type(gameData["linescore"]["inning"] is list):
                        inningArray = gameData["linescore"]["inning"]
                    elif type(gameData["linescore"]["inning"] is dict):
                        inningArray = []
                        inningArray.append(gameData["linescore"]["inning"])
                    else:
                        raise Exception('''Unexpected type of game["linescore"]["inning"]: ''' + str(type(gameData["linescore"]["inning"])))
                    
                    for inning in inningArray:
                        # Inning is live-- I (think) string is only
                        # empty during live inning with no runs
                        # yet. So let's just insert 0.
                        if inning["away"] == "":
                            awayScoreByInning.append("0")
                        else:
                            awayScoreByInning.append(inning["away"])

                        if "home" in inning:
                            if inning["home"] == "":
                                homeScoreByInning.append("0")
                            else:
                                homeScoreByInning.append(inning["home"])
                                
                        elif game["status"] == GameStatus.Post:
                            # Should only occur in inning 9 or beyond
                            homeScoreByInning.append("X")
                            # Else we leave blank, and autofill in with - below

                    # Pad unplayed innings with dashes
                    while len(awayScoreByInning) < 9:
                        awayScoreByInning.append("-")

                    # In extras, this length may be > 9 but still less
                    # than the number of innings the away team has
                    # played, so check against that number as well.
                    while len(homeScoreByInning) < 9 or len(homeScoreByInning) < len(awayScoreByInning):
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

        try:
            html = urlopen(self.standingsScrapeTarget)
        except:
            return -1
        
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

        try:
            html = urlopen(target)
        except:
            return -1
        
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
