from scrape.mlb_scraper import GameStatus, InningPart
from scrape.mlb_scraper_mlb_api import MlbScraperMlbApi
from weather.weather_info_wunderground import hourlyForecast

import datetime
import time
import pygame as pg

months = ["NONE", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 0 = Monday for some reason in datetime module
daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

wundergroundApiKey = "6d48850a7f579fe7"


fontName = "inputsansblack"
fontColor = (0xBC, 0xBC, 0xBC)

pg.init()
displaySize = pg.display.Info()
resolution = (displaySize.current_w, displaySize.current_h)
screen = pg.display.set_mode(resolution, pg.FULLSCREEN)
pg.mouse.set_visible(False)


class LiveScoreboard:
    def __init__(self):

        FPS = 30

        # See what fonts are available
        # fontlist = pg.font.get_fonts()
        # fontlist.sort()
        
        # for font in fontlist:
        #     print (font)
        
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
        
        timePanel = TimePanel(timePanelX2 - timePanelX1, timePanelY2 - timePanelY1)
        weatherPanel = WeatherPanel(weatherPanelX2 - weatherPanelX1, weatherPanelY2 - weatherPanelY1)
        
        # Store the time of when we last requested these things. This
        # is used to make our requests at a reasonable rate.
        weatherQueryMade = False         # (This hour)
        lastGameQueryTime = 0
        lastDivisionQueryTime = 0

        weatherQueryMinuteMark    = 40   # Query at XX:40
        
        gameNonLiveQueryCooldown  = 900  # Once per 15 minutes
        gameLiveQueryCooldown     = 20   # Once per 20 seconds
        divisionQueryCooldown     = 900  # Once per 15 minutes

        gameState = GameStatus.NoGame


        movie = pg.movie.Movie('moving_background.mpg')
        movie_screen = pg.Surface(movie.get_size()).convert()
        movie.set_display(movie_screen)
        movie.play()
        
        clock = pg.time.Clock()
        appLive = True
        firstLoop = True
        
        now = datetime.datetime.now()
        previousTime = now
        
        while appLive:
            # Get current date and wall clock time
            now = datetime.datetime.now()

            # Get program execution time (separate from wall time... not
            # affected by leapyear, timezones, etc.)
            executionTime = time.time()


            # Loop video if it ended
            if not movie.get_busy():
                movie.rewind()
                movie.play()


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

        fontSize = 1
        self.font = pg.font.SysFont(fontName, fontSize)

        # Find largest font that takes up <80% of either horizontal or
        # vertical space
        while True:
            fontSize += 1
            biggerFont = pg.font.SysFont(fontName, fontSize)

            if 2 * biggerFont.get_linesize() >= panelHeight * 0.8 or self.font.size("Thu, May 12")[0] >= panelWidth * 0.8:
                break
            
            self.font = biggerFont

        # Vertically center the 2 lines of text
        self.lineYStart = (panelHeight - 2 * self.font.get_linesize()) // 2
        
        self.background = (0, 0, 0, 120)

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
        self.surface.fill(self.background)
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
    # Each date label (should be no more than 2) has new line before
    # it, and then a text line (2 units per label = 4 units
    # total). Each weather line takes up a text line (1 unit per line
    # = 12 units total). Add 1 new line to the end (1 unit).

    # Grand total of 17 units, so text size is panel height * 1/17
    
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)
        fontSize = 1
        self.font = pg.font.SysFont(fontName, fontSize)
        
        while True:
            fontSize += 1
            biggerFont = pg.font.SysFont(fontName, fontSize)

            if 18 * biggerFont.get_linesize() >= panelHeight:
                break
            
            self.font = biggerFont
            
        self.background = (0, 0, 0, 120)
        self.weather = None

        # Get width of example string w/ 3 digit temperature, and
        # space alloted for weather icons.  This width will be used
        # when centering text in panel.
        stringWidth = self.font.size("00:00 - 100" + u'\N{DEGREE SIGN}' + " F        ")[0]
        self.lineY = 0
        self.lineX = (panelWidth - stringWidth) // 2
        
        self.iconX = self.lineX + self.font.size("00:00 - 100" + u'\N{DEGREE SIGN}' + " F    ")[0]
        
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
        self.surface.fill(self.background)
        
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


#
#
#
#
#
#
#

scoreboard = LiveScoreboard()
