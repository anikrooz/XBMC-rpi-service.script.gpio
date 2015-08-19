#!/usr/bin/python
#GPIO Script

import os, time, datetime
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
#from Utils import log, prettyprint
#import RPi.GPIO as GPIO
import subprocess

__addon__		= xbmcaddon.Addon()
__addonid__	  = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__	 = __addon__.getLocalizedString

AdditionalParams = []
Window = 10000

def log(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def passHomeDataToSkin(data, debug = True):
	wnd = xbmcgui.Window(Window)
	if data != None:
		for (key,value) in data.iteritems():
			wnd.setProperty('%s' % (str(key)), unicode(value))
			if debug:
				log('%s' % (str(key)) + unicode(value))
			   
def passDataToSkin(name, data, prefix="",debug = False):
	wnd = xbmcgui.Window(Window)
	if data != None:
		log( "%s%s.Count = %s" % (prefix, name, str(len(data)) ) )
		for (count, result) in enumerate(data):
			if debug:
				log( "%s%s.%i = %s" % (prefix, name, count + 1, str(result) ) )
			for (key,value) in result.iteritems():
				wnd.setProperty('%s%s.%i.%s' % (prefix, name, count + 1, str(key)), unicode(value))
				if debug:
					log('%s%s.%i.%s --> ' % (prefix, name, count + 1, str(key)) + unicode(value))
		wnd.setProperty('%s%s.Count' % (prefix, name), str(len(data)))
	else:
		wnd.setProperty('%s%s.Count' % (prefix, name), '0')
		log( "%s%s.Count = None" % (prefix, name ) )
		
class Main:
	def __init__( self ):
		log("version %s started" % __addonversion__ )
		xbmc.executebuiltin('SetProperty(extendedinfo_running,True,home)')
		self._init_vars()
		self._parse_argv()		
		# run in backend if parameter was set
		if self.ons:
			self._StartOnActions()
		if self.offs:
			self._StartOffActions()
		#if self.exportsettings:
			#from Utils import export_skinsettings
			#export_skinsettings()		
		#elif self.importsettings:
			#from Utils import import_skinsettings
			#import_skinsettings()
		if self.backend and xbmc.getCondVisibility("IsEmpty(Window(home).Property(extendedinfo_backend_running))"):
			log("running backend")
			xbmc.executebuiltin('SetProperty(extendedinfo_backend_running,True,home)')
			self.run_backend()
		# only set new properties if artistid is not smaller than 0, e.g. -1
		#elif self.artistid and self.artistid > -1:
		#	self._set_details(self.artistid)
		# else clear old properties
		#No arguments: Do setup
		elif not len(sys.argv) >1:
			self._selection_dialog()
		xbmc.executebuiltin('ClearProperty(extendedinfo_running,home)')
		
	def _StartOnActions(self):
		if not self.silent:
			xbmc.executebuiltin( "ActivateWindow(busydialog)" ) #This won't take long!
		for info in self.ons:
			log("Turning on GPIO "+info)
			#os.system("echo "+info+" > /sys/class/gpio/export")
			#os.system("echo out > /sys/class/gpio/gpio"+info+"/direction")
			os.system("gpio -g mode "+info+" out")
			os.system("gpio -g write "+info+" 1")
		self.ons = []
		if not self.silent:
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			
	def _StartOffActions(self):
		#if not self.silent:
		#	xbmc.executebuiltin( "ActivateWindow(busydialog)" )
		for info in self.offs:
			log("Turning off GPIO "+info)
			#os.system("echo "+info+" > /sys/class/gpio/export")
			#os.system("echo out > /sys/class/gpio/gpio"+info+"/direction")
			os.system("gpio -g write "+info+" 0")
		self.offs = []		
		if not self.silent:
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		
	def run_backend(self):	
		self._stop = False
		self.previousitem = ""
		self.previousartist = ""
		self.previoussong = ""
		self.ons = []
		self.offs = []
		for port in self.ins:
			os.system("gpio -g mode "+port+" in")
		#from Utils import create_musicvideo_list, create_movie_list
		#self.musicvideos = create_musicvideo_list()
		#self.movies = create_movie_list()
		while (not self._stop) and (not xbmc.abortRequested):
			if xbmc.getCondVisibility("!IsEmpty(Window(home).Property(GPIOon))"):
				self.ons.append(self.window.getProperty('GPIOon'))
				self._StartOnActions()
				self.window.clearProperty('GPIOon')
			if xbmc.getCondVisibility("!IsEmpty(Window(home).Property(GPIOoff))"):
				self.offs.append(self.window.getProperty('GPIOoff'))
				self._StartOffActions()
				self.window.clearProperty('GPIOoff')	
			if xbmc.getCondVisibility("Window.IsActive(home)"):
				#passDataToSkin('Stuff', ['bob', 'fred'], self.prop_prefix)
				for port in self.ins:
					read_data = subprocess.check_output(["gpio",  "-g", "read",  port])
					if str(read_data) != self.window.getProperty('GPIO'+port):
						log("GPIO"+port+": CHANGE -> "+str(read_data))
					self.window.setProperty("GPIO"+port, str(read_data))
			elif xbmc.getCondVisibility('Window.IsActive(screensaver)'):
				xbmc.sleep(1000)
			else:
				self.previousitem = ""
				self.selecteditem = ""	
				self._clear_properties()
				xbmc.sleep(500)	 
			if xbmc.getCondVisibility("IsEmpty(Window(home).Property(extendedinfo_backend_running))"):
				self._clear_properties()
				self._stop = True
			xbmc.sleep(500)
		#os.system("echo 0 > /sys/class/gpio/unexport")
			
	def _init_vars(self):
		self.window = xbmcgui.Window(10000) # Home Window default
		self.cleared = False
		self.prop_prefix = ""
		self.ons = []
		self.offs = []
		self.ins = []
		self.silent = True
		
	def _parse_argv(self):
		try:
			params = dict( arg.split("=") for arg in sys.argv[1].split("&"))
		except:
			params = {}
		self.backend = params.get("backend", False)
		self.exportsettings = params.get("exportsettings", False)
		self.importsettings = params.get("importsettings", False)
		for arg in sys.argv:
			log("ARGS: "+arg)
			if arg == 'script.GPIO':
				continue
			param = arg.lower()
			if param.startswith('ons='):
				self.ons.append(param[4:])
			elif param.startswith('offs='):
				self.offs.append(param[5:])
			elif param.startswith('window='):
				Window = int(arg[7:])
			elif param.startswith('ins='):
				self.ins.append(arg[4:])
			else:
				AdditionalParams.append(param)
	
	def _clear_properties( self ):
		self.cleared = False
		#self.window.clearProperty('Stuff')
		self.cleared = True
	
if ( __name__ == "__main__" ):
	Main()
log('finished')