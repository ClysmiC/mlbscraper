from scrape.mlb_scraper import GameStatus, InningPart
from scrape.mlb_scraper_mlb_api import MlbScraperMlbApi
from scrape.mlb_scraper_cbs import MlbScraperCbs

mlb = MlbScraperMlbApi()

wins, losses = mlb.getTeamRecord("STL");

print("Record: " + str(wins) + "-" + str(losses))
