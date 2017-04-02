#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 M.King
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import random

import xbmcaddon
import xbmcgui
import xbmc
import urllib, time, json, os, codecs

addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')
addon_path = addon.getAddonInfo('path').decode("utf-8")

addon_temp = xbmc.translatePath("special://temp").decode("utf-8") 
addon_bing = os.path.join(addon_temp, 'bing')

addon_use_files = addon.getSetting('use_files')
addon_clear_files = addon.getSetting('delete_files')

class Screensaver(xbmcgui.WindowXMLDialog):

    class ExitMonitor(xbmc.Monitor):

        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            self.exit_callback()

    def onInit(self):
        self.abort_requested = False
        self.started = False
        self.exit_monitor = self.ExitMonitor(self.exit)

        self.picture_control = self.getControl(30001)
        self.loader_control = self.getControl(30002)
        self.source_control = self.getControl(30003)
        self.title_control = self.getControl(30004)
        self.description_control = self.getControl(30005)
        self.next_picture_control = self.getControl(30006)

        self.picture_duration = (
            int(addon.getSetting('picture_duration')) * 1000
        )
        self.picture_select = int(addon.getSetting('site_version'))
        
        if not os.path.exists(addon_bing):
            os.makedirs(addon_bing)
            
        if(addon_clear_files == 'true'):
            self.deleteCache()
            addon.setSetting('delete_files', 'false')

        self.slideshow()

    def slideshow(self):
    
        while not self.abort_requested:

            opt = ['en-AU','pt-BR','en-CA','zh-CN','de-DE','fr-FR','ja-JP','en-NZ','en-US','en-UK']
            # Australia ,Brazil, Canada, China, Germnay, France, Japan, Netherland, United States, United Kingdom
                
            if(addon_use_files == 'false'):
            
                # normal mode ( actual 8 pictures)
                
                location = opt[self.picture_select]
                days = str(8)
                tomorrow = str(-1) # str(int(time.time() + (24*3600)))

                url = "http://www.bing.com/HPImageArchive.aspx?format=js&idx=" + tomorrow + "&n=" + str(days) + "&mkt=" + location;
                #self.log('Load ' + url)
                json_object = json.load(urllib.urlopen(url))

                for i, photo in enumerate(json_object['images']):
            
                    photo['source'] = 'Microsoft Bing'
                    self.set_photo(photo)
                
                    if i + 1 < len(json_object):
                        next_photo = json_object['images'][i + 1]
                        self.preload_next_photo(next_photo)            
                    for i in xrange(self.picture_duration / 500):
                        #self.log('check abort %d' % (i + 1))
                        if self.abort_requested:
                            self.log('slideshow abort_requested')
                            self.exit()
                            return
                        xbmc.sleep(500)
            else:
                
               # extended mode use cached files and fetch online
               
               location = opt[self.picture_select]
               days = str(8)
               tomorrow = str(-1) # str(int(time.time() + (24*3600)))

               url = "http://www.bing.com/HPImageArchive.aspx?format=js&idx=" + tomorrow + "&n=" + str(days) + "&mkt=" + location;
               #self.log('Load ' + url)
               json_object = json.load(urllib.urlopen(url))

               for i, photo in enumerate(json_object['images']):
                   self.load_photo(photo)
                   
               list = self.getDir(addon_bing)
               
               if not self.started:
	           self.loader_control.setVisible(False)
                   self.started = True
                            
               for i, photo in enumerate(list):
                   self.source_control.setLabel('Microsoft Bing')
                   
                   fileDate = photo.replace('.jpg','')
                   
		   self.title_control.setLabel(fileDate)
		   
		   #decription
		   fileName = os.path.join(addon_bing, fileDate)
		   fileName = fileName + '.txt'
		   f2 = codecs.open(fileName,'r' ,'utf-8')
		   self.description_control.setText(f2.read())
                   f2.close()
                   
                   # picture
                   fileName = os.path.join(addon_bing, photo)
                   self.picture_control.setImage(fileName)
                   
                   for i in xrange(self.picture_duration / 500):
		       #self.log('check abort %d' % (i + 1))
		       if self.abort_requested:
		           self.log('slideshow abort_requested')
		           self.exit()
		           return
                       xbmc.sleep(500)
               
    def set_photo(self, photo):
        if not self.started:
            self.loader_control.setVisible(False)
            self.started = True
            
        picture_url = 'http://www.bing.com' + photo['url']
        #self.log('photo: %s' % picture_url)
        
        self.source_control.setLabel(photo['source'])
        self.title_control.setLabel(photo['startdate'])
        self.description_control.setText(photo['copyright'])
        
        file = photo['startdate'] + '.jpg'
        desc = photo['startdate'] + '.txt'

        fileName = os.path.join(addon_bing, file)
        fileDesc = os.path.join(addon_bing, desc)

        #can we use cache ?
        if(not os.path.exists(fileName)):
            # no cache 
            self.log('load without cache ' + file)
            self.picture_control.setImage(picture_url)
        
            # save to cache
            f1 = urllib.URLopener()
            f1.retrieve(picture_url, fileName)
            f1.close()

            f2 = codecs.open(fileDesc,'w' ,'utf-8')
            f2.write(photo['copyright'])
            f2.close()
        
        else:
            # use cache 

            self.log('load use cache ' + file)
            self.picture_control.setImage(fileName)
            
            f2 = codecs.open(fileDesc,'r' ,'utf-8')
            self.description_control.setText(f2.read())
            f2.close()
       
    def preload_next_photo(self, photo):
        picture_url = 'http://www.bing.com' + photo['url']
        
        # try ti use cached file
        file = photo['startdate'] + '.jpg'
        fileName = os.path.join(addon_bing, file)
        
        if(os.path.exists(fileName)):
            picture_url = fileName
            self.log('preload use cache ' + file)
        
        self.next_picture_control.setImage(picture_url)

    def load_photo(self, photo):
        picture_url = 'http://www.bing.com' + photo['url']
        
        file = photo['startdate'] + '.jpg'
	desc = photo['startdate'] + '.txt'
	
	fileName = os.path.join(addon_bing, file)
        fileDesc = os.path.join(addon_bing, desc)
        
        if(not os.path.exists(fileName)):
            # no cache 
            self.log('load photo ' + file)
               
            # save to cache
            f1 = urllib.URLopener()
            f1.retrieve(picture_url, fileName)
            f1.close()
       
            f2 = codecs.open(fileDesc,'w' ,'utf-8')
            f2.write(photo['copyright'])
            f2.close()

    def deleteCache(self):
        if os.path.exists(addon_bing):
            for f in os.listdir(addon_bing):
                fpath = os.path.join(addon_bing, f)
                try:
                    if os.path.isfile(fpath):
                        os.unlink(fpath)
                except Exception as e:
                    self.log(str(e))
                    
    def getDir(self, path):
        list = [s for s in os.listdir(path) if s.endswith('.jpg')]
        list.sort(reverse=True)
        return list


    def exit(self):
        self.abort_requested = True
        self.exit_monitor = None
        self.log('exit')
        self.close()

    def log(self, msg):
        xbmc.log(u'Bing Pictures Screensaver: %s' % msg)


if __name__ == '__main__':
    screensaver = Screensaver(
        'script-%s-main.xml' % addon_name,
        addon_path,
        'default',
    )
    screensaver.doModal()
    del screensaver
    sys.modules.clear()
