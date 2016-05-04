from enum import Enum
from abc import ABCMeta, abstractmethod

GameStatus = Enum('GameStatus', 'NoGame Pre Live Post')
InningPart = Enum('InningPart', 'Top Mid Bot End')

class BaseMlbScraper(metaclass=ABCMeta):    
    '''Class that contains the mlb-scrape functionality. Created as a
    class, instead of as a list of functions so that methods can reference
    list and dict of valid team names that gets created in init'''
    
    def __init__(self):
        '''Constructs an mlbscraper object.'''
        
        self.validTeams = []
        self.validTeams.append("ARI")
        self.validTeams.append("ATL")
        self.validTeams.append("BAL")
        self.validTeams.append("BOS")
        self.validTeams.append("CHC")
        self.validTeams.append("CHW")
        self.validTeams.append("CIN")
        self.validTeams.append("CLE")
        self.validTeams.append("COL")
        self.validTeams.append("DET")
        self.validTeams.append("HOU")
        self.validTeams.append("KC")
        self.validTeams.append("LAA")
        self.validTeams.append("LAD")
        self.validTeams.append("MIA")
        self.validTeams.append("MIL")
        self.validTeams.append("MIN")
        self.validTeams.append("NYM")
        self.validTeams.append("NYY")
        self.validTeams.append("OAK")
        self.validTeams.append("PHI")
        self.validTeams.append("PIT")
        self.validTeams.append("SD")
        self.validTeams.append("SEA")
        self.validTeams.append("SF")
        self.validTeams.append("STL")
        self.validTeams.append("TB")
        self.validTeams.append("TEX")
        self.validTeams.append("TOR")
        self.validTeams.append("WAS")

        for team in self.validTeams:
            assert len(team) == 2 or len(team) == 3

        self.teamNames = {}
        self.teamNames["DIAMONDBACKS"]       = "ARI"
        self.teamNames["DIAMOND BACKS"]      = "ARI"
        self.teamNames["DBACKS"]             = "ARI"
        self.teamNames["BRAVES"]             = "ATL"
        self.teamNames["ORIOLES"]            = "BAL"
        self.teamNames["RED SOX"]            = "BOS"
        self.teamNames["REDSOX"]             = "BOS"
        self.teamNames["CUBS"]               = "CHC"
        self.teamNames["WHITESOX"]           = "CHW"
        self.teamNames["WHITE SOX"]          = "CHW"
        self.teamNames["REDS"]               = "CIN"
        self.teamNames["INDIANS"]            = "CLE"
        self.teamNames["TRIBE"]              = "CLE"
        self.teamNames["ROCKIES"]            = "COL"
        self.teamNames["TIGERS"]             = "DET"
        self.teamNames["ASTROS"]             = "HOU"
        self.teamNames["ROYALS"]             = "KC"
        self.teamNames["ANGELS"]             = "LAA"
        self.teamNames["DODGERS"]            = "LAD"
        self.teamNames["MARLINS"]            = "MIA"
        self.teamNames["BREWERS"]            = "MIL"
        self.teamNames["TWINS"]              = "MIN"
        self.teamNames["METS"]               = "NYM"
        self.teamNames["YANKEES"]            = "NYY"
        self.teamNames["ATHLETICS"]          = "OAK"
        self.teamNames["A'S"]                = "OAK"
        self.teamNames["AS"]                 = "OAK"
        self.teamNames["PHILLIES"]           = "PHI"
        self.teamNames["PIRATES"]            = "PIT"
        self.teamNames["BUCS"]               = "PIT"
        self.teamNames["BUCCOS"]             = "PIT"
        self.teamNames["PADRES"]             = "SD"
        self.teamNames["MARINERS"]           = "SEA"
        self.teamNames["GIANTS"]             = "SF"
        self.teamNames["CARDINALS"]          = "STL"
        self.teamNames["CARDS"]              = "STL"
        self.teamNames["REDBIRDS"]           = "STL"
        self.teamNames["RAYS"]               = "TB"
        self.teamNames["DEVIL RAYS"]         = "TB"
        self.teamNames["DEVILRAYS"]          = "TB"
        self.teamNames["RANGERS"]            = "TEX"
        self.teamNames["BLUE JAYS"]          = "TOR"
        self.teamNames["BLUEJAYS"]           = "TOR"
        self.teamNames["JAYS"]               = "TOR"
        self.teamNames["NATIONALS"]          = "WAS"
        self.teamNames["NATS"]               = "WAS"

        # Future proof: 3ORLESS. If new nick-name pops up that is 3
        # letters or less, make changes wherever 3ORLESS tag appears
        # in comments.
        for key, value in self.teamNames.items():
            try:
                assert len(key) > 3 or key == "AS" or key == "A'S"
                assert value in self.validTeams
            except AssertionError as e:
                e.args += (key,)
                raise

    def getTeamNick(self, teamName):
        '''Returns the 2 or 3 letter nickname of the team.

        Args: 
            teamName (str): The name of the team (not including
                city). Some alternate names are recognized too, such
                as "Cards" or "Buccos". Capitalization does not matter

        Returns:
            The 2 or 3 letter nickname of the team, or None if the
            team is not found.'''

        if type(teamName) is not str:
            raise TypeError("Team name must be a string.")

        teamName = teamName.upper()

        if teamName in self.validTeams:
            return teamName
        
        if teamName not in self.teamNames:
            return None
        else:
            return self.teamNames[teamName]
        
    def getGameInfo(self, team, date=None):
        '''Return the information for the baseball game on a given date for
        the given team.

        Args:
            team (str): The 2 or 3 letter abbreviation of the
                team. Alternatively, you can pass the team's full name
                without city information (e.g., "STL", "Cardinals", "TB",
                "Rays" are all valid). Capitalization does not matter.

            date (Optional[datetime.date]): The date of the game. If
                omitted, defaults to today's date.

        Returns:
            dict: Dictionary containing various details about the
                specified game.'''
        pass


