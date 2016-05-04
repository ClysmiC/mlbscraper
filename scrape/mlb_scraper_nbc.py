from bs4 import BeautifulSoup
from urllib.request import urlopen
from .mlb_scraper import BaseMlbScraper, GameStatus, InningPart

import datetime

class MlbScraperCbs(BaseMlbScraper):
    def __init__(self):
        super(MlbScraperCbs, self).__init__()
        self.scrapeTarget = "http://scores.nbcsports.com/mlb/scoreboard.asp"

    def getGameInfo(self, team, date=None):
        if type(team) is not str:
            raise TypeError("Team name must be a string.")

        team = team.upper()


        # Future proof: 3ORLESS. If new nick-name pops up that is 3
        # letters or less, make changes wherever 3ORLESS tag appears
        # in comments.
        if(len(team) > 3 or team == "AS" or team == "A'S"):
            if(team in self.teamNames):
                team = self.teamNames[team]
            else:
                raise ValueError("Team " + team + " is invalid.")
        elif team not in self.validTeams:
            raise ValueError("Team " + team + " is invalid.")

        # cbs sports uses the convention MLBSTL, MLBNYY, etc.
        team = "MLB" + team

        if date is None:
            date = datetime.date.today()

        dateString = str(date.year).zfill(4) + str(date.month).zfill(2) + str(date.day).zfill(2)

        ##
        ## OPEN AND BEGIN URL PARSE
        ##
        ##
        html = urlopen(self.scrapeTarget + dateString)

        soup = BeautifulSoup(html, "lxml")

        return game
    
