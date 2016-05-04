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

        self.validDivisions = []
        self.validDivisions.append("ALW")
        self.validDivisions.append("ALC")
        self.validDivisions.append("ALE")
        self.validDivisions.append("NLW")
        self.validDivisions.append("NLC")
        self.validDivisions.append("NLE")

        # NOTE: These are not "true" divisions, but they may be passed
        # to the getDivisionStandings(..) method to return the
        # wild-card race standings, which can be displayed the same
        # way as normal divisions.
        self.validDivisions.append("ALWC")
        self.validDivisions.append("NLWC")

        # Names and nicknames that map to the corresponding 2 or 3
        # letter codes. All input to methods get transformed to the
        # codes for uniformity.
        self.teamNames = {}
        self.teamNames["DIAMONDBACKS"]       = "ARI"
        self.teamNames["DIAMOND BACKS"]      = "ARI"
        self.teamNames["DBACKS"]             = "ARI"
        self.teamNames["D-BACKS"]            = "ARI"
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

        # Valid names for the various divisions, that get mapped to
        # the codes that the methods involving divisions operate on.
        self.divisionNames = {}
        self.divisionNames["AL WEST"] = "ALW"
        self.divisionNames["AMERICAN LEAGUE WEST"] = "ALW"
        self.divisionNames["AMERICAN WEST"] = "ALW"
        self.divisionNames["AL CENTRAL"] = "ALC"
        self.divisionNames["AMERICAN LEAGUE CENTRAL"] = "ALC"
        self.divisionNames["AMERICAN CENTRAL"] = "ALC"
        self.divisionNames["AL EAST"] = "ALE"
        self.divisionNames["AMERICAN LEAGUE EAST"] = "ALE"
        self.divisionNames["AMERICAN EAST"] = "ALE"

        self.divisionNames["NL WEST"] = "NLW"
        self.divisionNames["NATIONAL LEAGUE WEST"] = "NLW"
        self.divisionNames["NATIONAL WEST"] = "NLW"
        self.divisionNames["NL CENTRAL"] = "NLC"
        self.divisionNames["NATIONAL LEAGUE CENTRAL"] = "NLC"
        self.divisionNames["NATIONAL CENTRAL"] = "NLC"
        self.divisionNames["NL EAST"] = "NLE"
        self.divisionNames["NATIONAL LEAGUE EAST"] = "NLE"
        self.divisionNames["NATIONAL EAST"] = "NLE"

        self.divisionNames["AL WC"] = "ALWC"
        self.divisionNames["AL WILDCARD"] = "ALWC"
        self.divisionNames["AL WILD CARD"] = "ALWC"
        self.divisionNames["AL WILD-CARD"] = "ALWC"             
        self.divisionNames["AMERICAN LEAGUE WC"] = "ALWC"
        self.divisionNames["AMERICAN LEAGUE WILDCARD"] = "ALWC"
        self.divisionNames["AMERICAN LEAGUE WILD CARD"] = "ALWC"
        self.divisionNames["AMERICAN LEAGUE WILD-CARD"] = "ALWC"     
        self.divisionNames["AMERICAN WC"] = "ALWC"
        self.divisionNames["AMERICAN WILDCARD"] = "ALWC"
        self.divisionNames["AMERICAN WILD CARD"] = "ALWC"
        self.divisionNames["AMERICAN WILD-CARD"] = "ALWC"

        self.divisionNames["NL WC"] = "NLWC"
        self.divisionNames["NL WILDCARD"] = "NLWC"
        self.divisionNames["NL WILD CARD"] = "NLWC"
        self.divisionNames["NL WILD-CARD"] = "NLWC"               
        self.divisionNames["NATIONAL LEAGUE WC"] = "NLWC"
        self.divisionNames["NATIONAL LEAGUE WILDCARD"] = "NLWC"
        self.divisionNames["NATIONAL LEAGUE WILD CARD"] = "NLWC"
        self.divisionNames["NATIONAL LEAGUE WILD-CARD"] = "NLWC"     
        self.divisionNames["NATIONAL WC"] = "NLWC"
        self.divisionNames["NATIONAL WILDCARD"] = "NLWC"
        self.divisionNames["NATIONAL WILD CARD"] = "NLWC"
        self.divisionNames["NATIONAL WILD-CARD"] = "NLWC"

        for key, value in self.divisionNames.items():
            try:
                assert value in self.validDivisions
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
            string: The 2 or 3 letter nickname of the team, or
                None if the team is not found.'''

        if type(teamName) is not str:
            raise TypeError("Team name must be a string.")

        teamName = teamName.upper()

        if teamName in self.validTeams:
            return teamName
        
        if teamName not in self.teamNames:
            return None
        else:
            return self.teamNames[teamName]

    def getDivisionNick(self, divisionName):
        '''Returns the 3 or 4 letter nickname of the division.

        Args:
            divisionName (str): The name of the division. Accepts
                many forms, such as "NL Central", "National League
                Central", "National Central". Capitalization does not
                matter.

        Returns:
            string: The 3 or 4 letter nickname of the division, or
                None if the team is not found.'''

        if type(divisionName) is not str:
            raise TypeError("Division name must be a string.")

        divisionName = divisionName.upper()

        if divisionName in self.validDivisions:
            return divisionName
        
        if divisionName not in self.divisionNames:
            return None
        else:
            return self.divisionNames[divisionName]

    @abstractmethod
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

    @abstractmethod
    def getTeamRecord(self, team):
        '''Return the current record of the given team.

        Args:
            team (str): The 2 or 3 letter abbreviation of the
                team. Alternatively, you can pass the team's full name
                without city information (e.g., "STL", "Cardinals", "TB",
                "Rays" are all valid). Capitalization does not matter.
 
        Returns:
            int: The numer of wins.
            int: The number of losses.'''
        pass

    @abstractmethod
    def getDivisionStandings(self, division):
        '''Return the standings of the given division.

        Args:
            division (str): The 3 or 4 letter abbreviation of the

                division. These abbreviations are "ALW", "ALC", "ALE",
                "NLW", "NLC", "NLE", "ALWC", and "NLWC" (note: "ALWC"
                and "NLWC" return wildcard standings). Alternatively,
                you can pass the division's full name (e.g., "NATIONAL
                LEAGUE CENTRAL", "NL CENTRAL", "NATIONAL CENTRAL" are
                all valid). Capitalization does not matter.

        Returns:
            list: The standings of the division, sorted from
                first to last. Each entry in the list is a dict with
                the keys "name", "wins", "losses", and "gb" (games
                back).'''
        pass
    
