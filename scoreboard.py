teamToSearch = None;

if(len(sys.argv) < 1):
    teamToSearch = raw_input("Enter team initials (e.g., STL): ")
else:
    teamToSearch = sys.argv[1]

teamToSearch = "MLB" + teamToSearch.strip(" ").upper()

url = "http://www.cbssports.com/mlb/scoreboard"

print("Opening url . . .")
html = urlopen(url).read()
print("Soupifying . . .")
soup = BeautifulSoup(html, "lxml")

print("Finding " + teamToSearch + " rows . . .")
foundRows = soup.findAll("tr", class_ = teamToSearch)

preGame = None
liveGame = None
postGame = None

print(str(len(foundRows)) + " " + teamToSearch + " rows")
print("")
print("")
print("")

for game in foundRows:
	parent = game.parent
	if "liveEvent" in parent["class"]:
		liveGame = parent
	if "preEvent" in parent["class"]:
		preGame = parent
	if "postEvent" in parent["class"]:
		postGame = parent

#TO-DO: investigate displaying post-game

if liveGame is None:
	if preGame is None:
		if postGame is None:
			print("No game today or invalid team.")
		else:
			#Post-game results
			#To-do, display this in box score like a live game
			info = getGameInfo(postGame)

			print("-FINAL-")
			print(info["away"]["name"] + ": " + info["away"]["runs"])
			print(info["home"]["name"] + ": " + info["home"]["runs"])
	else:
		info = getGameInfo(preGame)

		print(info["away"]["name"] + " vs. " + info["home"]["name"])
		print("Game Time: " + info["startTime"])
else:
	#Display live score
	gameInfo = getGameInfo(liveGame)
	away = gameInfo["away"]
	home = gameInfo["home"]

	print("       1    2    3    4    5    6    7    8    9    R    H    E")
	print("---------------------------------------------------------------")

	awayString = away["name"] + (" " * (3 - len(away["name"])))
	for inningScore in away["scoreByInning"]:
		awayString += (" " * (5 - len(str(inningScore)))) + inningScore

	awayString += " |" + (" " * (3 - len(away["runs"]))) + away["runs"]
	awayString += " |" + (" " * (3 - len(away["hits"]))) + away["hits"]
	awayString += " |" + (" " * (3 - len(away["errors"]))) + away["errors"]

	homeString = home["name"]
	for inningScore in home["scoreByInning"]:
		homeString += (" " * (5 - len(str(inningScore)))) + inningScore

	homeString += " |" + (" " * (3 - len(home["runs"]))) + home["runs"]
	homeString += " |" + (" " * (3 - len(home["hits"]))) + home["hits"]
	homeString += " |" + (" " * (3 - len(home["errors"]))) + home["errors"]

	print(awayString)
	print(homeString)
