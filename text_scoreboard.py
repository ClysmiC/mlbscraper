import sys
import datetime

from scrape.mlb_scraper import GameStatus, InningPart
from scrape.mlb_scraper_mlb_api import MlbScraperMlbApi
from scrape.mlb_scraper_cbs import MlbScraperCbs

mlb = MlbScraperCbs()

argError = False
date = None
team = None

if len(sys.argv) > 3:
    argError = True

if len(sys.argv) > 1:
    sys.argv[1] = sys.argv[1].replace("-", "")
    if sys.argv[1].isdigit():
        try:
            date = datetime.date(int(sys.argv[1][0:4]), int(sys.argv[1][4:6]), int(sys.argv[1][6:8]))
        except:
            argError = True
    else:
        team = sys.argv[1]
        
if len(sys.argv) > 2:
    sys.argv[2] = sys.argv[2].replace("-", "")
    if sys.argv[2].isdigit():
        if date is None:
            try:
                date = datetime.date(int(sys.argv[2][0:4]), int(sys.argv[2][4:6]), int(sys.argv[2][6:8]))
            except:
                argError = True
        else:
            argError = True
    else:
        if team is None:
            team = sys.argv[2]
        else:
            argError = True
    
if argError:
    print("Usage:")
    print("\tmlb_scoreboard.py [team] [date]")
    print("Examples:")
    print("\tmlb_scoreboard.py")
    print("\tmlb_scoreboard.py STL")
    print("\tmlb_scoreboard.py 2016-07-17")
    print("\tmlb_scoreboard.py STL 2016-07-17")
    print("\tmlb_scoreboard.py Cardinals 20160717")
    exit()
    
if team is None:
    team = input("\nEnter team name or initials (e.g., \"STL\"): ")

if date is None:
    date = input("\nEnter date in following form: \"2016-07-17\n(Dashes optional, leave blank for current date): ")
    date = date.replace("-", "")
    if len(date) == 0:
        # mlb_scraper defaults to today when date is omitted or None
        date = None
    else:
        try:
            date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))
        except:
            print("Invalid date. Exiting...")
            exit()

try:
    game = mlb.getGameInfo(team, date)
except Exception as e:
    print("Error. Perhaps you typed an invalid team name?")
    raise e # NOTE: only for dev / debugging purposes do we re-raise
            # error

print("")

if(game["status"] == GameStatus.NoGame):
    print("No game today.")
    
elif(game["status"] == GameStatus.Pre):
    print(game["away"]["name"] + " vs. " + game["home"]["name"])
    print("Game Time: " + game["startTime"])
    
else:
    if(game["status"] == GameStatus.Post):
        print("-FINAL-")
        print(game["away"]["name"] + ": " + game["away"]["runs"])
        print(game["home"]["name"] + ": " + game["home"]["runs"])

    # TODO: Implement support for games in extra innings.
    print("")
    print("          1    2    3    4    5    6    7    8    9    R    H    E")
    print("------------------------------------------------------------------")

    if game["status"] == GameStatus.Live:
        if game["inning"]["part"] in (InningPart.Top, InningPart.End):
            awayString = " * "
            homeString = "   "
        else:
            awayString = "   "
            homeString = " * "
    else:
        awayString = "   "
        homeString = "   "
        
    awayString += game["away"]["name"] + (" " * (3 - len(game["away"]["name"])))
    for inningScore in game["away"]["scoreByInning"]:
        awayString += (" " * (5 - len(inningScore))) + inningScore
        
    awayString += " |" + (" " * (3 - len(game["away"]["runs"]))) + game["away"]["runs"]
    awayString += " |" + (" " * (3 - len(game["away"]["hits"]))) + game["away"]["hits"]
    awayString += " |" + (" " * (3 - len(game["away"]["errors"]))) + game["away"]["errors"]
        
    homeString += game["home"]["name"] + (" " * (3 - len(game["home"]["name"])))
    for inningScore in game["home"]["scoreByInning"]:
        homeString += (" " * (5 - len(inningScore))) + inningScore
            
    homeString += " |" + (" " * (3 - len(game["home"]["runs"]))) + game["home"]["runs"]
    homeString += " |" + (" " * (3 - len(game["home"]["hits"]))) + game["home"]["hits"]
    homeString += " |" + (" " * (3 - len(game["home"]["errors"]))) + game["home"]["errors"]

    print(awayString)
    print(homeString)

