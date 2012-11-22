import sys
import os
import re
import chardet
import xbmc, xbmcgui, xbmcvfs

DEBUG_MODE = 4

__addon__   = sys.modules[ "__main__" ].__addon__
__profile__ = sys.modules[ "__main__" ].__profile__

# comapatble versions
SETTINGS_VERSIONS = ( "1.7", )
# base paths
BASE_DATA_PATH = sys.modules[ "__main__" ].__profile__
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
LYRIC_SCRAPER_DIR = os.path.join(__cwd__, "resources", "lib", "scrapers")
# special button codes
SELECT_ITEM = ( 11, 256, 61453, )
EXIT_SCRIPT = ( 247, 275, 61467, )
CANCEL_DIALOG  = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
GET_EXCEPTION = ( 216, 260, 61448, )
SETTINGS_MENU = ( 229, 259, 261, 61533, )
SHOW_CREDITS = ( 195, 274, 61507, )
MOVEMENT_UP = ( 166, 270, 61478, )
MOVEMENT_DOWN = ( 167, 271, 61480, )
# special action codes
ACTION_SELECT_ITEM = ( 7, )
ACTION_EXIT_SCRIPT = ( 10, )
ACTION_CANCEL_DIALOG = ACTION_EXIT_SCRIPT + ( 9, )
ACTION_GET_EXCEPTION = ( 0, 11 )
ACTION_SETTINGS_MENU = ( 117, )
ACTION_SHOW_CREDITS = ( 122, )
ACTION_MOVEMENT_UP = ( 3, )
ACTION_MOVEMENT_DOWN = ( 4, )
# Log status codes
LOG_INFO, LOG_ERROR, LOG_NOTICE, LOG_DEBUG = range( 1, 5 )

def _create_base_paths():
    """ creates the base folders """
    if ( not xbmcvfs.exists( BASE_DATA_PATH.decode("utf-8") ) ):
        xbmcvfs.mkdirs( BASE_DATA_PATH.decode("utf-8") )
_create_base_paths()

def get_xbmc_revision():
    try:
        rev = int(re.search("r([0-9]+)",  xbmc.getInfoLabel( "System.BuildVersion" ), re.IGNORECASE).group(1))
    except:
        rev = 0
    return rev

def get_keyboard( default="", heading="", hidden=False ):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    if ( keyboard.isConfirmed() ):
        return keyboard.getText()
    return default

def get_numeric_dialog( default="", heading="", dlg_type=3 ):
    """ shows a numeric dialog and returns a value
        - 0 : ShowAndGetNumber		(default format: #)
        - 1 : ShowAndGetDate			(default format: DD/MM/YYYY)
        - 2 : ShowAndGetTime			(default format: HH:MM)
        - 3 : ShowAndGetIPAddress	(default format: #.#.#.#)
    """
    dialog = xbmcgui.Dialog()
    value = dialog.numeric( type, heading, default )
    return value

def get_browse_dialog( default="", heading="", dlg_type=1, shares="files", mask="", use_thumbs=False, treat_as_folder=False ):
    """ shows a browse dialog and returns a value
        - 0 : ShowAndGetDirectory
        - 1 : ShowAndGetFile
        - 2 : ShowAndGetImage
        - 3 : ShowAndGetWriteableDirectory
    """
    dialog = xbmcgui.Dialog()
    value = dialog.browse( dlg_type, heading, shares, mask, use_thumbs, treat_as_folder, default )
    return value

def LOG( status, format, *args ):
    if ( DEBUG_MODE >= status ):
        xbmc.output( "%s: %s\n" % ( ( "INFO", "ERROR", "NOTICE", "DEBUG", )[ status - 1 ], format % args, ) )

def get_settings():
    settings = {}
    settings[ "scraper" ] = __addon__.getSetting( "scraper" )
    settings[ "save_lyrics" ] = __addon__.getSetting( "save_lyrics" ) == "true"
    settings[ "lyrics_path" ] = __addon__.getSetting( "lyrics_path" )
    if ( settings[ "lyrics_path" ] == "" ):
        settings[ "lyrics_path" ] = os.path.join( BASE_DATA_PATH, "lyrics" )
        __addon__.setSetting(id="lyrics_path", value=settings[ "lyrics_path" ])
    settings[ "smooth_scrolling" ] = __addon__.getSetting( "smooth_scrolling" ) == "true"
    settings[ "use_filename" ] = __addon__.getSetting( "use_filename" ) == "true"
    settings[ "filename_format" ] = __addon__.getSetting( "filename_format" )
    settings[ "artist_folder" ] = __addon__.getSetting( "artist_folder" ) == "true"
    settings[ "subfolder" ] = __addon__.getSetting( "subfolder" ) == "true"
    settings[ "subfolder_name" ] = __addon__.getSetting( "subfolder_name" )
    return settings

def get_textfile(filepath):
    try:
        if (not xbmcvfs.exists(filepath)):
            return ""
        file = xbmcvfs.File( filepath )
        data = file.read()
        file.close()
        # Detect text encoding
        enc = chardet.detect(data)
        if (enc['encoding'] == 'utf-8'):
            return data
        else:
            return unicode( data, enc['encoding'] ).encode( "utf-8")
    except UnicodeDecodeError:
        return data
    except IOError:
        return ""

def log(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__,msg,),level=xbmc.LOGDEBUG )

def deAccent(str):
    return unicodedata.normalize('NFKD', unicode(unicode(str, 'utf-8'))).encode('ascii','ignore')

def replace(string):
    replace_char = [" ",",","'","&","and"]
    for char in replace_char:
        string.replace(char,"-")
    return string

class Lyrics:
    def __init__( self ):
        self.song = Song()
        self.lyrics = ""
        self.source = ""

class Song:
    def __init__( self ):
        self.artist = ""
        self.title = ""

    def __str__(self):
        return "Artist: %s, Title: %s" % ( self.artist, self.title)

    def __cmp__(self, song):
        if (self.artist != song.artist):
            return cmp(self.artist, song.artist)
        else:
            return cmp(self.title, song.title)

    def sanitize(self, str):
        return str.replace( "\\", "_" ).replace( "/", "_" ).replace(":","_").replace("?","_").replace("!","_")

    def path(self):
        return unicode( os.path.join( __profile__, "lyrics", self.sanitize(self.artist), self.sanitize(self.title) + ".txt" ), "utf-8" )

    @staticmethod
    def current():
        song = Song.by_offset(0)

        if not song.artist and not xbmc.getInfoLabel( "MusicPlayer.TimeRemaining"):
            # no artist and infinite playing time ? We probably listen to a radio
            # which usually set the song title as "Artist - Title" (via ICY StreamTitle)
            sep = song.title.find("-")
            if sep > 1:
                song.artist = song.title[:sep - 1].strip()
                song.title = song.title[sep + 1:].strip()
                # The title in the radio often contains some additional
                # bracketed information at the end:
                #  Radio version, short version, year of the song...
                # It often disturbs the lyrics search so we remove it
                song.title = re.sub(r'\([^\)]*\)$', '', song.title)

        log( "Current Song: %s:%s" % (song.artist, song.title))
        return song

    @staticmethod
    def next():
        song = Song.by_offset(1)
        log( "Next Song: %s:%s" % (song.artist, song.title))
        if song.artist != '' and song.title != '':
            return song

    @staticmethod
    def by_offset(offset = 0):
        song = Song()
    	if offset > 0:
            offset_str = ".offset(%i)" % offset
        else:
            offset_str = ""	
        song.title = xbmc.getInfoLabel( "MusicPlayer%s.Title" % offset_str)
        song.title = deAccent(song.title)
        song.artist = xbmc.getInfoLabel( "MusicPlayer%s.Artist" % offset_str)
        song.artist = deAccent(song.artist)

        return song