# Author: Ludovic SARAKHA
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import re
import threading

import sickbeard
from sickbeard import db
from sickbeard import logger, show_name_helpers
from sickbeard import providers
from sickbeard import search
from sickbeard.common import SNATCHED_FRENCH, SEASON_RESULT
from sickbeard.common import showLanguages
from sickrage.show.Show import Show
from sickrage.providers.GenericProvider import GenericProvider

resultFilters = ["sub(pack|s|bed)", "nlsub(bed|s)?", "swesub(bed)?",
                 "(dir|sample|nfo)fix", "sample", "(dvd)?extras"]



class FrenchFinder():

    #def __init__(self, force=None, show=None):
    def __init__(self):
        self.lock = threading.Lock()
        #TODOif not sickbeard.DOWNLOAD_FRENCH:
        #    return



    def run(self, force=None, show=None):
        if sickbeard.showList==None:
            return
        logger.log(u"Beginning the search for french episodes older than "+ str(sickbeard.FRENCH_DELAY) +" days")
        foundResults = {}
        finalResults = []
        #show = self
        frenchlist=[]
        #get list of english episodes that we want to search in french
        myDB = db.DBConnection()
        today = datetime.date.today().toordinal()
        if show:
            frenchsql=myDB.select("SELECT showid, season, episode from tv_episodes where audio_langs='eng' and tv_episodes.showid =? and (? - tv_episodes.airdate) > ? order by showid, airdate asc",[show,today,sickbeard.FRENCH_DELAY])
            logger.log("SELECT showid, season, episode from tv_episodes where audio_langs='eng' and tv_episodes.showid =" + str(show) +"and (" +str(today)+" - tv_episodes.airdate) > "+ str(sickbeard.FRENCH_DELAY) +"order by showid, airdate asc")
            count=myDB.select("SELECT count(*) from tv_episodes where audio_langs='eng' and tv_episodes.showid =? and (? - tv_episodes.airdate) > ?",[show,today,sickbeard.FRENCH_DELAY])
        else:
            frenchsql=myDB.select("SELECT showid, season, episode from tv_episodes, tv_shows where audio_langs='eng' and tv_episodes.showid = tv_shows.indexer_id and tv_shows.frenchsearch = 1 and (? - tv_episodes.airdate) > ? order by showid, airdate asc",[today,sickbeard.FRENCH_DELAY])
            count=myDB.select("SELECT count(*) from tv_episodes, tv_shows where audio_langs='eng' and tv_episodes.showid = tv_shows.indexer_id and tv_shows.frenchsearch = 1 and (? - tv_episodes.airdate) > ?",[today,sickbeard.FRENCH_DELAY])
        #make the episodes objects

        #logger.log("SELECT showid, season, episode from tv_episodes where audio_langs='eng' and tv_episodes.showid =" + str(show) +"and (" +str(today)+" - tv_episodes.airdate) > "+ str(sickbeard.FRENCH_DELAY) +"order by showid, airdate asc")
        logger.log("SELECT showid, season, episode from tv_episodes, tv_shows where audio_langs='eng' and tv_episodes.showid = tv_shows.indexer_id and tv_shows.frenchsearch = 1 and ("+ str(today) +" - tv_episodes.airdate) > "+ str(sickbeard.FRENCH_DELAY) +" order by showid, airdate asc")
        logger.log(u"Searching for "+str(count[0][0]) +" episodes in french")

        #logger.log(frenchsql)

        #logger.log(sickbeard.showList.)



        for episode in frenchsql:

            showObj = Show.find(sickbeard.showList, int(episode[0]))
            if showObj == None:
                logger.log( "Show not in show list")

            #showObj = helpers.findCertainShow(sickbeard.showList, episode[0])
            epObj = showObj.getEpisode(episode[1], episode[2])

            #epObj = showObj.getEpisode(int(epInfo[0]), int(epInfo[1]))
            frenchlist.append(epObj)

        #for each episode in frenchlist fire a search in french
        delay=[]
        temp=None
        rest=count[0][0]
        for frepisode in frenchlist:
            rest=rest-1
            if frepisode.show.indexerid in delay:
                logger.log(u"Previous episode for show "+str(frepisode.show.name)+" not found in french so skipping this search", logger.DEBUG)
                continue
            result=[]
            for curProvider in providers.sortedProviderList():

                foundResults[curProvider.name] = {}

                if not curProvider.is_active():
                    continue

                logger.log(u"Searching for french episode on "+curProvider.name +" for " +frepisode.show.name +" season "+str(frepisode.season)+" episode "+str(frepisode.episode))
                #try:
                #    logger.log(frepisode)
                #    temp = GenericProvider()
                #    curfrench = temp.findFrench(self, episode=frepisode, manualSearch=True)
                    #curfrench =  GenericProvider.findFrench(episode=frepi  sode,manualSearch=True)
                    #curProvider.findFrench(frepisode, manualSearch=True)
                #except:
                #    logger.log(u"Exception", logger.DEBUG)
                #    pass

                #for curProvider in providers:
                #    if curProvider.anime_only and not show.is_anime:
                #        logger.log(u"" + str(show.name) + " is not an anime, skipping", logger.DEBUG)
                #        continue

                curfrench = curProvider.find_search_results(frepisode.show, frenchlist, 'sponly', True, True, 'french')

                #curfrench = curProvider.findFrench(frepisode, True)


                #temp = GenericProvider('temp')
                #curfrench = temp.findFrench( episode=frepisode, manualSearch=True)

                if len(curfrench):
                #make a list of all the results for this provider
                    for curEp in curfrench:
                        if curEp in foundResults:
                            foundResults[curProvider.name][curEp] += curfrench[curEp]
                        else:
                            foundResults[curProvider.name][curEp] = curfrench[curEp]



                if not foundResults[curProvider.name]:
                    continue

                bestSeasonResult = None
                #if SEASON_RESULT in foundResults[curProvider.name]:
                #    bestSeasonResult = search.pickBestResult(foundResults[curProvider.name][SEASON_RESULT], show)
                #_______________________________________________________
                test=0
                if foundResults[curProvider.name]:
                    for cur_episode in foundResults[curProvider.name]:
                        for x in foundResults[curProvider.name][cur_episode]:
                            tmp = x
                            if not show_name_helpers.filterBadReleases(x.name):         #x.name):
                                logger.log(u"French "+x.name+" isn't a valid scene release that we want, ignoring it", logger.DEBUG)
                                test+=1
                                continue
                            if sickbeard.IGNORE_WORDS == "":
                                ignore_words="ztreyfgut"
                            else:
                                ignore_words=str(sickbeard.IGNORE_WORDS)
                            for fil in resultFilters + ignore_words.split(','):
                                if fil == showLanguages.get(u"fre"):
                                    continue
                                if re.search('(^|[\W_])'+fil+'($|[\W_])', x.url, re.I) or re.search('(^|[\W_])'+fil+'($|[\W_])', x.name, re.I) :
                                    logger.log(u"Invalid scene release: "+x.url+" contains "+fil+", ignoring it", logger.DEBUG)
                                    test+=1

                    if test==0:
                        result.append(x)



            best=None
            try:
                epi={}
                epi[1]=frepisode
                best = search.pickBestResult(result, showObj)
            except:
                pass
            if best:
                best.name=best.name + ' snatchedfr'
                logger.log(u"Found french episode for " +frepisode.show.name +" season "+str(frepisode.season)+" episode "+str(frepisode.episode))
                try:
                    search.snatchEpisode(best, SNATCHED_FRENCH)
                except:
                    logger.log(u"Exception", logger.DEBUG)
                    pass
            else:
                delay.append(frepisode.show.indexerid)
                logger.log(u"No french episode found for " +frepisode.show.name +" season "+str(frepisode.season)+" episode "+str(frepisode.episode))
            logger.log(str(rest) + u" episodes left")
