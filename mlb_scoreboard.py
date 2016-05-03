from mlb_scraper.mlb_scraper import MlbScraper
import sys

mlb = MlbScraper()

if len(sys.argv) < 2:
    team = input("Enter team name or initials (e.g., \"STL\"): ")
else:
    team = sys.argv[1]
        
game = mlb.getGameInfo(team)

if(game["status"] == "none"):
    print("No game today.")
    
elif(game["status"] == "pre"):
    print(game["away"]["name"] + " vs. " + game["home"]["name"])
    print("Game Time: " + game["startTime"])
    
else:
    if(game["status"] == "post"):
        print("-FINAL-")
        print(game["away"]["name"] + ": " + game["away"]["runs"])
        print(game["home"]["name"] + ": " + game["home"]["runs"])

    # TODO: Implement support for games in extra innings.
    print("")
    print("       1    2    3    4    5    6    7    8    9    R    H    E")
    print("---------------------------------------------------------------")
    
    awayString = game["away"]["name"] + (" " * (3 - len(game["away"]["name"])))
    for inningScore in game["away"]["scoreByInning"]:
        awayString += (" " * (5 - len(str(inningScore)))) + inningScore
        
    awayString += " |" + (" " * (3 - len(game["away"]["runs"]))) + game["away"]["runs"]
    awayString += " |" + (" " * (3 - len(game["away"]["hits"]))) + game["away"]["hits"]
    awayString += " |" + (" " * (3 - len(game["away"]["errors"]))) + game["away"]["errors"]
        
    homeString = game["home"]["name"]
    for inningScore in game["home"]["scoreByInning"]:
        homeString += (" " * (5 - len(str(inningScore)))) + inningScore
            
    homeString += " |" + (" " * (3 - len(game["home"]["runs"]))) + game["home"]["runs"]
    homeString += " |" + (" " * (3 - len(game["home"]["hits"]))) + game["home"]["hits"]
    homeString += " |" + (" " * (3 - len(game["home"]["errors"]))) + game["home"]["errors"]

    print(awayString)
    print(homeString)

