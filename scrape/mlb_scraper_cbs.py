from bs4 import BeautifulSoup
from urllib.request import urlopen
from .mlb_scraper import BaseMlbScraper, GameStatus, InningPart

import datetime

class MlbScraperCbs(BaseMlbScraper):
    def __init__(self):
        super(MlbScraperCbs, self).__init__()
        self.scrapeTarget = "http://www.cbssports.com/mlb/scoreboard/"

    def getGameInfo(self, team, date=None):
        if type(team) is not str:
            raise TypeError("Team name must be a string.")

        team = team.upper()
        team = self.getTeamNick(team)
        
        if team is None:
            raise ValueError("Invalid team name.")
        
        # TODO: convert team name to NBC's strings
        team = "MLB" + team

        if date is None:
            date = datetime.date.today()

        dateQuery = "?day=" +  str(date.year).zfill(4) + str(date.month).zfill(2) + str(date.day).zfill(2)

        ##
        ## OPEN AND BEGIN URL PARSE
        ##
        ##
        html = urlopen(self.scrapeTarget + dateQuery)

        soup = BeautifulSoup(html, "lxml")
        foundRows = soup.findAll("tr", class_ = team)


        ##
        ## EXTRACT GAME INFO FROM HTML
        ##
        ##
        game = {}
        game["status"] = GameStatus.NoGame

        # Determine status of the current game.
        for row in foundRows:
            tag = row.parent
            if "liveEvent" in tag["class"]:
                game["status"] = GameStatus.Live
            if "preEvent" in tag["class"]:
                game["status"] = GameStatus.Pre
            if "postEvent" in tag["class"]:
                game["status"] = GameStatus.Post

        # Couldn't find game on site. Must be no game today.
        if game["status"] == GameStatus.NoGame:
            return game

        game["away"] = {}
        game["home"] = {}

        awayTeam = tag.find("tr", class_ = "awayTeam")
        awayName = awayTeam["class"][2][3:]

        homeTeam = tag.find("tr", class_ = "homeTeam")
        homeName = homeTeam["class"][2][3:]

        game["away"]["name"] = awayName
        game["home"]["name"] = homeName

        if game["status"] == GameStatus.Pre:
            # Note: CBS has a div called gmtTime that instantly gets
            # updated by javascript to be called gmtTimeUpdated. I
            # assume this is after checking my local timezone and
            # changing the contents of the div. However, even before
            # it updates, it has correctly had the EDT timezone in
            # this div for me. I don't know if this is just a default,
            # or if it is something done server-side. Look into
            # this... I would prefer to get the actual GMT time so any
            # application using this module can do the converting
            # themself. Do more investigation once I get out to
            # Seattle, as spoofing into a different timezone by
            # changing OS settings has not had an effect.
            game["startTime"] = tag.find("span", class_ = "gmtTime").string
            return game

        if game["status"] == GameStatus.Live:
            inningString = tag.find("td", class_= "gameStatus").string
            inningHalf, inningNumber = inningString.split(" ")

            # Strip off st, nd, rd, th in 1st, 2nd, 3rd, 4th, etc.
            inningNumber = inningNumber[:-2]

            inningHalf = inningHalf.upper()

            game["inning"] = {}
            game["inning"]["number"] = int(inningNumber)

            if(inningHalf == "TOP"):
                game["inning"]["part"] = InningPart.Top
            elif(inningHalf == "MIDDLE"):
                game["inning"]["part"] = InningPart.Mid
            elif(inningHalf == "BOTTOM"):
                game["inning"]["part"] = InningPart.Bot
            elif(inningHalf == "END"):
                game["inning"]["part"] = InningPart.End
            else:
                raise Exception("Inning part " + inningHalf + " invalid. Maybe CBS changed web page format?")

            # TODO: Scrape current pitcher and hitter

            # TODO: Scrape strikes/balls/outs and runners on. Might be
            # impossible on CBS without executing the javascript?

        awayScoreByInning = awayTeam.findAll("td", class_ = "periodScore")
        homeScoreByInning = homeTeam.findAll("td", class_ = "periodScore")

        # Save the inner string of all the periodScore td's
        for index, score in enumerate(awayScoreByInning):
            awayScoreByInning[index] = score.string

        for index, score in enumerate(homeScoreByInning):
            homeScoreByInning[index] = score.string

        # Note: Unfortunately, scoreByInning arrays are 0-indexed,
        # so to get the 7th inning score one would have to do
        # scoreByInning[6]. We could make index 0 empty, but that
        # would make it harder to iterate over.
        game["away"]["scoreByInning"] = awayScoreByInning
        game["home"]["scoreByInning"] = homeScoreByInning

        awayRuns = awayTeam.find("td", class_ = "runsScore").string
        homeRuns = homeTeam.find("td", class_ = "runsScore").string

        game["away"]["runs"] = awayRuns
        game["home"]["runs"] = homeRuns

        awayHits = awayTeam.find("td", class_ = "hitsScore").string
        homeHits = homeTeam.find("td", class_ = "hitsScore").string

        game["away"]["hits"] = awayHits
        game["home"]["hits"] = homeHits

        awayErrors = awayTeam.find("td", class_ = "errorsScore").string
        homeErrors = homeTeam.find("td", class_ = "errorsScore").string

        game["away"]["errors"] = awayErrors
        game["home"]["errors"] = homeErrors

        # NOTE: Check during live games to see how we can determine
        # what inning it is currently in, where runners are, how many
        # balls, strikes, and outs there are.

        # TODO: See what happens during the following situations, and
        # implement support for them:
        # Delay (rain)
        # Cancellation
        # Double-header

        # TODO: Consider the following additions: See who is hitting,
        # pitching. On client side, we could have database of images
        # to put into a graphic based on the current hitter and
        # pitcher.

        return game
    
