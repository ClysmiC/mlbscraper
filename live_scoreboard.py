# TODO: switch to monospaced font to make everything less of a pain in
# the ass?

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

fontColor = (0xBC, 0xBC, 0xBC)

class LiveScoreboard:
    def __init__(self):
        pg.init()

        displaySize = pg.display.Info()
        resolution = (displaySize.current_w, displaySize.current_h)
        FPS = 30

        pg.init()
        screen = pg.display.set_mode(resolution, pg.FULLSCREEN)
        pg.mouse.set_visible(False)

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
        lastWeatherQueryTime = 0
        lastGameQueryTime = 0
        lastDivisionQueryTime = 0

        weatherQueryCooldown      = 1800 # Once per half-hour
        gameNonLiveQueryCooldown  = 900  # Once per 15 minutes
        gameLiveQueryCooldown     = 20   # Once per 20 seconds
        divisionQueryCooldown     = 900  # Once per 15 minutes

        gameState = GameStatus.NoGame

        # NOTE:
        # Weather to show:
        # 12 times that fit the following criteria
        # ALWAYS show first 3 hours in the list.

        # Don't show odd hours (unless it is in first 3 hours)
        # Don't show weather from 00:00 - 6:00 (unless it is in first 3 hours)

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
                
            # Update weather panel
            if firstLoop or executionTime >= lastWeatherQueryTime + weatherQueryCooldown:
                lastWeatherQueryTime = executionTime
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
    # 10 % - gap
    # 35 % - line 1 (date)
    # 10 % - gap
    # 35 % - line 2 (time)
    # 10 % - gap

    # NOTE: The math isn't pixel perfect, since we specify the FONT
    # height, which isn't necessarily the line height. But it has
    # looked good on every monitor that I've tried. If I find a
    # monitor that it looks bad on, do an approach similar to the
    # weather panel to find the biggest acceptable font size.
    def __init__(self, panelWidth, panelHeight):
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)
        self.time = None
        
        self.font = pg.font.SysFont('franklingothicdemi', int(panelHeight * 0.35))
        self.background = (0, 0, 0, 120)

        # Font is not monospaced, so the updating time string changes
        # slightly each tick. Since the text is centered, this makes
        # it move a bit each tick. Instead, we will treat each text
        # surface as if it had the width of the following surface, so
        # it will always be drawn in the same place.
        self.timeTextWidth = self.font.render("00:00:00", True, fontColor).get_width()
        
    def setTime(self, time):
        self.time = time
        
    def update(self):
        self.surface.fill(self.background)

        string1 = daysOfWeek[self.time.weekday()] + ", " + months[self.time.month] + " " + str(self.time.day)
        string2 = "{:02d}:{:02d}:{:02d}".format(self.time.hour, self.time.minute, self.time.second)
        
        # 1st line of text
        textSurface = self.font.render(string1, True, fontColor)
        self.surface.blit(textSurface, ((self.surface.get_width() - textSurface.get_width()) // 2, int(self.surface.get_height() * 0.1)))

        textSurface = self.font.render(string2, True, fontColor)
        self.surface.blit(textSurface, ((self.surface.get_width() - self.timeTextWidth) // 2, int(self.surface.get_height() * (0.1 + 0.35 + 0.1))))
        
        return self.surface
        



class WeatherPanel:
    # Each date label (should be no more than 2) has new line, and
    # then a text line (2 units per label = 4 units total). Each
    # weather line takes up a text line (1 unit per line = 12 units
    # total).

    # Grand total of 16 units, so text size is panel height * 1/16
    
    def __init__(self, panelWidth, panelHeight):
        # TODO: add h and v padding. Some letters are being weird as
        # hell, maybe try a new font ?
        self.surface = pg.Surface((panelWidth, panelHeight), flags=pg.SRCALPHA)

        fontSize = 1
        self.font = pg.font.SysFont('franklingothicdemi', fontSize)
        
        while 16 * self.font.get_linesize() < panelHeight:
            fontSize += 1
            self.font = pg.font.SysFont('franklingothicdemi', fontSize)
            
        self.background = (0, 0, 0, 120)
        self.weather = None
        
    def setWeather(self, weather):
        self.weather = weather
        
    def update(self):
        self.surface.fill(self.background)
        
        lastDateLabelDay = None
        lineY = 0
        firstHour = True
        
        for hour in self.weather:
            time = hour["time"]
            if time.day != lastDateLabelDay:
                self.font.set_underline(True)
                dayString = months[time.month] + " " + str(time.day)
                daySurface = self.font.render(dayString, True, fontColor)

                # New line
                lineY += self.font.get_height()
                self.surface.blit(daySurface, (0, lineY))
                lineY += self.font.get_height()

                self.font.set_underline(False)
                lastDateLabelDay = time.day

            hourString = "{:02d}:{:02d}".format(time.hour, time.minute) + " -- " + hour["temp"] + u'\N{DEGREE SIGN}' + " F -- " + hour["condition"]

            if firstHour:
                hourSurface = self.font.render(hourString, True, (0, 0, 0), (255,255,153))
            else:
                hourSurface = self.font.render(hourString, True, fontColor)

            
            self.surface.blit(hourSurface, (0, lineY))
            lineY += self.font.get_height()
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
