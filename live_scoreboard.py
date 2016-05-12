from scrape.mlb_scraper import GameStatus, InningPart
from scrape.mlb_scraper_mlb_api import MlbScraperMlbApi
from weather.weather_info_wunderground import hourlyForecast

from datetime import datetime, timedelta
import time
import pygame as pg

months = ["NONE", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 0 = Monday for some reason in datetime module
daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

wundergroundApiKey = "6d48850a7f579fe7"

panelBackgroundColor = (0, 0, 0, 120)

fontName = "inputmonoblack"
fontColor = (0xBC, 0xBC, 0xBC)

# Initializing pygame
pg.init()
displaySize = pg.display.Info()
resolution = (displaySize.current_w, displaySize.current_h)
screen = pg.display.set_mode(resolution, pg.FULLSCREEN)
pg.mouse.set_visible(False)

# Initialize mlb scraper
mlb = MlbScraperMlbApi()
mlbTeams = mlb.validTeams
mlbLogos = {}

# Initialize list of MLB team logos
for __team in mlbTeams:
    mlbLogos[__team] = pg.image.load("scrape/logos/" + __team + ".png")

def fontFit(name, stringToFit, dimensionsToFit):
    fontSize = 1
    font = pg.font.SysFont(name, fontSize)
    
    # Find largest font that fits within the space for the given string.
    while True:
        fontSize += 1
        biggerFont = pg.font.SysFont(fontName, fontSize)

        if biggerFont.get_linesize() >= dimensionsToFit[1] or font.size(stringToFit)[0] >= dimensionsToFit[0]:
            break

        font = biggerFont

    return font

class LiveScoreboard:
    def __init__(self):

        FPS = 30
        
        # Split the screen up into these virtual rows and columns. Use these
        # to determine where to position each element. This lets the elements
        # automatically resize on different sized monitors
        numColumns = 30
        numRows = 20

        columns = []
        rows = []

        for i in range(numColumns):
            columns.append(int(screen.get_width() / numColumns * i))

        for i in range(numRows):
            rows.append(int(screen.get_height() / numRows * i))

        columnWidth = columns[1] - columns[0]
        rowWidth = rows[1] - rows[0]

        timePanelX1 = columns[1]
        timePanelY1 = rows[1]
        timePanelX2 = columns[13]
        timePanelY2 = rows[6]

        weatherPanelX1 = columns[1]
        weatherPanelY1 = rows[7]
        weatherPanelX2 = columns[9]
        weatherPanelY2 = rows[19]
        
        gameScorePanelX1 = columns[14]
        gameScorePanelY1 = rows[1]
        gameScorePanelX2 = columns[29]
        gameScorePanelY2 = rows[6]

        gamePreviewPanelX1 = gameScorePanelX1
        gamePreviewPanelY1 = gameScorePanelY1
        gamePreviewPanelX2 = gameScorePanelX2
        gamePreviewPanelY2 = gameScorePanelY2
        
        timePanel = TimePanel(timePanelX2 - timePanelX1, timePanelY2 - timePanelY1)
        weatherPanel = WeatherPanel(weatherPanelX2 - weatherPanelX1, weatherPanelY2 - weatherPanelY1)
        gameScorePanel = GameScorePanel(gameScorePanelX2 - gameScorePanelX1, gameScorePanelY2 - gameScorePanelY1)
        gamePreviewPanel = GamePreviewPanel(gamePreviewPanelX2 - gamePreviewPanelX1, gamePreviewPanelY2 - gamePreviewPanelY1)
        
        # Store the time of when we last requested these things. This
        # is used to make our requests at a reasonable rate.
        weatherQueryMade = False         # (This hour)
        lastGameQueryTime = 0
        lastDivisionQueryTime = 0

        weatherQueryMinuteMark    = 40   # Query at XX:40
        
        gameNonLiveQueryCooldown  = 900  # Once per 15 minutes
        gameLiveQueryCooldown     = 20   # Once per 20 seconds
        divisionQueryCooldown     = 900  # Once per 15 minutes

        
        movie = pg.movie.Movie('moving_background.mpg')
        movie_screen = pg.Surface(movie.get_size()).convert()
        movie.set_display(movie_screen)
        
        clock = pg.time.Clock()
        appLive = True
        firstLoop = True
        
        now = datetime.now()
        previousTime = now
        
        movie.play()
        
        while appLive:
            # Get current date and wall clock time
            now = datetime.now()

            # Get program execution time (separate from wall time... not
            # affected by leapyear, timezones, etc.)
            executionTime = time.time()


            # Loop video if it ended
            if not movie.get_busy():
                movie.rewind()
                movie.play()


            # Query game information
            if (firstLoop) or (game["status"] == GameStatus.Live and executionTime - lastGameQueryTime >= gameLiveQueryCooldown) or (
                    executionTime - lastGameQueryTime >= gameNonLiveQueryCooldown):
                if now.hour < 4:
                    dateOfInterest = now - timedelta(days=1)
                else:
                    dateOfInterest = now
                    
                game = mlb.getGameInfo("STL", dateOfInterest)

                # If no game found for today, look ahead up to 10 days
                # until we find a game
                lookaheadDays = 0
                while game["status"] == GameStatus.NoGame and lookaheadDays < 10:
                    lookaheadDays += 1
                    dateOfInterest = dateOfInterest + timedelta(days=1)
                    game = mlb.getGameInfo("STL", dateOfInterest)

                if game["status"] in (GameStatus.Live, GameStatus.Post):
                    gameScorePanel.setScore(game)
                    gameScoreOrPreviewPanelSurface = gameScorePanel.update()
                else:
                    gamePreviewPanel.setPreview(game)
                    gameScoreOrPreviewPanelSurface = gamePreviewPanel.update()
                    
                lastGameQueryTime = executionTime
                    
            # Update day/time panel
            if firstLoop or now.second != previousTime.second:
                timePanel.setTime(now)
                timePanelSurface = timePanel.update()

            # Weather query not yet made this hour... but wait for the
            # minute mark to make it.
            if now.minute <= weatherQueryMinuteMark:
                weatherQueryMade = False
                
            # Update weather panel
            if firstLoop or (now.minute >= weatherQueryMinuteMark and not weatherQueryMade):
                weatherQueryMade = True
                weatherInfo = hourlyForecast("Saint Louis", "MO", wundergroundApiKey)
                weatherInfoToDisplay = []

                # Only display up to 12 hours, using the following rules.
                #
                # 1. Next 3 hours are always displayed
                # 2. Only even hours are displayed (except when rule 1)
                # 3. 00:00 - 05:59 are not displayed (except when rule 1)
                for i, hour in enumerate(weatherInfo):
                    if len(weatherInfoToDisplay) == 12:
                        break

                    if i < 3:
                        weatherInfoToDisplay.append(hour)
                    elif hour["time"].hour % 2 == 0 and hour["time"].hour > 5:
                        weatherInfoToDisplay.append(hour)
                        
                weatherPanel.setWeather(weatherInfoToDisplay)
                weatherPanelSurface = weatherPanel.update()
            
            # Stretch video to fit display. Transfer the stretched video onto
            # the screen.
            pg.transform.scale(movie_screen, screen.get_size(), screen)

            # Blit various panels on top of the video background
            screen.blit(timePanelSurface, (timePanelX1, timePanelY1))
            screen.blit(weatherPanelSurface, (weatherPanelX1, weatherPanelY1))
            screen.blit(gameScoreOrPreviewPanelSurface, (gameScorePanelX1, gameScorePanelY1))
            pg.display.update()
            
            # Check for quit event or ESC key press
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    movie.stop()
                    appLive = False

            previousTime = now
            firstLoop = False
            
            # Sleep to keep application running at 30 FPS
            clock.tick(FPS)

        pg.quit()


class TimePanel:
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)
        self.time = None
        
        self.font = fontFit(fontName, "Thu, May 12", (panelWidth * 0.8, panelHeight * 0.8 / 2))

        # Vertically center the 2 lines of text
        self.lineYStart = (panelHeight - 2 * self.font.get_linesize()) // 2
        

        # Font is not monospaced, so the updating time string changes
        # slightly each tick. Since the text is centered, this makes
        # it move a bit each tick. Instead, we will treat each text
        # surface as if it had the width of the following surface, so
        # it will always be drawn in the same place.

        # Note: not needed if using monospace font
        # self.timeTextWidth = self.font.render("00:00:00", True, fontColor).get_width()
        
    def setTime(self, time):
        self.time = time
        
    def update(self):
        self.surface.fill(panelBackgroundColor)
        string1 = daysOfWeek[self.time.weekday()] + ", " + months[self.time.month] + " " + str(self.time.day)
        string2 = "{:02d}:{:02d}:{:02d}".format(self.time.hour, self.time.minute, self.time.second)
        
        lineY = self.lineYStart
        
        textSurface = self.font.render(string1, True, fontColor)
        self.surface.blit(textSurface, ((self.surface.get_width() - textSurface.get_width()) // 2, lineY))

        lineY += self.font.get_linesize()
        
        textSurface = self.font.render(string2, True, fontColor)
        self.surface.blit(textSurface, ((self.surface.get_width() - textSurface.get_width()) // 2, lineY))
        
        return self.surface
        



class WeatherPanel:
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)
        
        # 12 lines for the 12 entries shown, plus various lines for
        # padding. If you change this number, you have to manually
        # add/remove padding lines around the lines that print the
        # date to make sure things are sized properly.
        numLines = 18

        # Get width of example string w/ 3 digit temperature, and
        # space alloted for weather icons.  This width will be used
        # when centering text in panel.
        exampleString = "00:00 - 100" + u'\N{DEGREE SIGN}' + " F  "

        # Extra spaces after example string to ensure icons fit
        self.font = fontFit(fontName, exampleString + "  ", (panelWidth * 0.8, panelHeight // numLines))           

        self.lineY = 0
        
        stringWidth = self.font.size(exampleString)[0]
        self.lineX = (panelWidth - stringWidth) // 2
        
        self.iconX = self.lineX + self.font.size(exampleString)[0]
        
        # TODO: find places where it is raining, snowing, and has chance of
        # rain, snow, so I know what the condition string is.
        self.weatherIcons = {}
        iconSize = self.font.get_height()

        self.weatherIcons["Clear"] = pg.transform.smoothscale(pg.image.load("weather/icons/clear.png"), (iconSize, iconSize))
        self.weatherIcons["Partly Cloudy"] = pg.transform.smoothscale(pg.image.load("weather/icons/partly_cloudy.png"), (iconSize, iconSize))
        self.weatherIcons["Mostly Cloudy"] = self.weatherIcons["Partly Cloudy"]
        self.weatherIcons["Overcast"] = pg.transform.smoothscale(pg.image.load("weather/icons/cloudy.png"), (iconSize, iconSize))
        self.weatherIcons["Chance of a Thunderstorm"] = pg.transform.smoothscale(pg.image.load("weather/icons/chance_tstorm.png"), (iconSize, iconSize))
        self.weatherIcons["Thunderstorm"] = pg.transform.smoothscale(pg.image.load("weather/icons/tstorm.png"), (iconSize, iconSize))
        
    def setWeather(self, weather):
        self.weather = weather
        
    def update(self):
        self.surface.fill(panelBackgroundColor)
        
        lastDateLabelDay = None
        self.lineY = 0
        firstHour = True
        
        for hour in self.weather:
            time = hour["time"]
            if time.day != lastDateLabelDay:
                self.font.set_underline(True)
                dayString = months[time.month] + " " + str(time.day)
                daySurface = self.font.render(dayString, True, fontColor)

                # New lines
                if lastDateLabelDay is not None:
                    self.lineY += self.font.get_linesize()
                    
                self.lineY += self.font.get_linesize()
                self.surface.blit(daySurface, (max(0, self.lineX - self.font.size("  ")[0]), self.lineY))
                self.lineY += self.font.get_linesize()

                self.font.set_underline(False)
                lastDateLabelDay = time.day

            hourString = "{:02d}:{:02d}".format(time.hour, time.minute) + " - " + "{:>3s}".format(hour["temp"]) + u'\N{DEGREE SIGN}' + " F"

            if firstHour:
                hourSurface = self.font.render(hourString, True, (0, 0, 0), (255,255,153))
            else:
                hourSurface = self.font.render(hourString, True, fontColor)

            self.surface.blit(hourSurface, (self.lineX, self.lineY))
            self.surface.blit(self.weatherIcons[hour["condition"]], (self.iconX, self.lineY))
            self.lineY += self.font.get_linesize()
            firstHour = False

        return self.surface


class GameScorePanel():
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)

        # Leading spaces leave room for logo
        self.numLeadingSpacesForLogo = 4
        exampleString = " " * self.numLeadingSpacesForLogo +  "STL 10"
        self.font = fontFit(fontName, exampleString, (panelWidth * .5 * .8, panelHeight * 0.8 / 2))

        # Center 2 lines of text vertically
        self.lineYStart = (panelHeight - 2 * self.font.get_linesize()) // 2

        # Center left half strings horizontally
        self.leftHalfX = (panelWidth * .5 - self.font.size(exampleString)[0]) // 2

        # Center right half strings horizontally
        self.rightHalfX = panelWidth * .5 + (panelWidth * .5 - self.font.size("Top 10")[0]) // 2
        
        self.scaledLogos = {}
        self.logoLinePortion = 0.9 # logo takes up this % of line height

        # Initialize list of MLB team logos
        for key, logo in mlbLogos.items():
            logoHeight = logo.get_height()
            logoWidth = logo.get_width()
            scale = self.font.get_linesize() * self.logoLinePortion / logoHeight

            self.scaledLogos[key] = pg.transform.smoothscale(logo, (int(scale * logoWidth), int(scale * logoHeight)))
        

    def setScore(self, game):
        self.game = game

    def update(self):
        self.surface.fill(panelBackgroundColor)

        # TEMP HACK CODE
        self.game["home"]["name"] = "SF"
        self.game["away"]["runs"] = 15
        self.game["home"]["runs"] = 3
        
        awayString   = " " * self.numLeadingSpacesForLogo + self.game["away"]["name"] + " {:2d}".format(self.game["away"]["runs"])
        awayLogo = self.scaledLogos[self.game["away"]["name"]]

        homeString   = " " * self.numLeadingSpacesForLogo + self.game["home"]["name"] + " {:2d}".format(self.game["home"]["runs"])
        homeLogo = self.scaledLogos[self.game["home"]["name"]]

        inningString = "Top  3"

        lineY = self.lineYStart

        logoSpace = " " * self.numLeadingSpacesForLogo
        logoSpaceWidth = self.font.size(logoSpace)[0]
        awayLogoOffset = (logoSpaceWidth - awayLogo.get_width()) // 2
        homeLogoOffset = (logoSpaceWidth - homeLogo.get_width()) // 2
        
        self.surface.blit(awayLogo, (self.leftHalfX + awayLogoOffset, lineY + self.font.get_linesize() * 0.5 * (1 * self.logoLinePortion)))
        self.surface.blit(self.font.render(awayString, True, fontColor), (self.leftHalfX, lineY))
        self.surface.blit(self.font.render(inningString, True, fontColor), (self.rightHalfX, lineY))

        lineY += self.font.get_linesize()

        self.surface.blit(homeLogo, (self.leftHalfX + homeLogoOffset, lineY + self.font.get_linesize() * 0.5 * (1 - self.logoLinePortion)))
        self.surface.blit(self.font.render(homeString, True, fontColor), (self.leftHalfX, lineY))

        return self.surface

class GamePreviewPanel:
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)

        # Leading spaces leave room for logo
        self.numLeadingSpacesForLogo = 4
        exampleTopString = " " * self.numLeadingSpacesForLogo +  "CHC @ STL" + " " * self.numLeadingSpacesForLogo
        exampleBotString = "May 12, 15:28"
        self.font = fontFit(fontName, exampleTopString, (panelWidth * .8, panelHeight * 0.8 / 2))

        # Center 2 lines of text vertically
        self.lineYStart = (panelHeight - 2 * self.font.get_linesize()) // 2

        # Center top line horizontally
        self.topX = (panelWidth - self.font.size(exampleTopString)[0]) // 2
        
        # Center bot line horizontally
        self.botX = (panelWidth - self.font.size(exampleBotString)[0]) // 2
        
        self.scaledLogos = {}
        self.logoLinePortion = 0.9
        
        # Initialize list of MLB team logos
        for key, logo in mlbLogos.items():
            logoHeight = logo.get_height()
            logoWidth = logo.get_width()
            scale = self.font.get_linesize() * self.logoLinePortion / logoHeight

            self.scaledLogos[key] = pg.transform.smoothscale(logo, (int(scale * logoWidth), int(scale * logoHeight)))
            

    def setPreview(self, game):
        self.game = game

    def update(self):
        self.surface.fill(panelBackgroundColor)

        if self.game["status"] == GameStatus.Pre:
            topString   = " " * self.numLeadingSpacesForLogo + "{:3s} @ {:3s}".format(self.game["away"]["name"], self.game["home"]["name"]) + " " * self.numLeadingSpacesForLogo
            botString = self.game["startTime"]

            awayLogo = self.scaledLogos[self.game["away"]["name"]]
            homeLogo = self.scaledLogos[self.game["home"]["name"]]

            logoSpace = " " * self.numLeadingSpacesForLogo
            logoWidth = self.font.size(logoSpace)[0]

            awayLogoOffset = (logoWidth - awayLogo.get_width()) // 2
            homeLogoOffset = self.font.size(topString)[0] - logoWidth + (logoWidth - homeLogo.get_width()) // 2

            lineY = self.lineYStart

            self.surface.blit(awayLogo, (self.topX + awayLogoOffset, lineY + self.font.get_linesize() * 0.5 * (1 - self.logoLinePortion)))
            self.surface.blit(homeLogo, (self.topX + homeLogoOffset, lineY + self.font.get_linesize() * 0.5 * (1 - self.logoLinePortion)))
            self.surface.blit(self.font.render(topString, True, fontColor), (self.topX, lineY))

            lineY += self.font.get_linesize()

            self.surface.blit(self.font.render(botString, True, fontColor), (self.botX, lineY))
        else:
            self.surface.blit(self.font.render("No games found...", True, fontColor), (0, 0))
            
        return self.surface
    
#
#
#
#
#
#
#

scoreboard = LiveScoreboard()
