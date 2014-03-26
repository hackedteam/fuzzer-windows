#!/usr/bin/env python

# awful
import sys
sys.path.append('../')
sys.path.append('.')
import parsers.TTF as TTF

import os
import time
import random
import shutil
import string
import struct
import sqlite3
import hashlib
import datetime
import win32api
import win32gui
import threading

from ctypes import *
from struct import *
from win32con import *
from fontTools import ttLib
from multiprocessing import Process, Queue


# N.B not working anymore


FONT_SPECIFIER_NAME_ID = 4
FONT_SPECIFIER_FAMILY_ID = 1
FR_PRIVATE=0x10



def shortName(font):

    for record in font['name'].names:
        if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
            if '\000' in record.string:
                name = unicode(record.string, 'utf-16-be').encode('utf-8')
            else:
                name = record.string
        elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family:
            if '\000' in record.string:
                family = unicode(record.string, 'utf-16-be').encode('utf-8')
            else:
                family = record.string
        if name and family:
            break
    print 'AAAA', name, family
    return name, family


# for deployment
class mainWindow():

    def __init__(self):
        win32gui.InitCommonControls()
        self.hinst = windll.kernel32.GetModuleHandleW(None)
        self.classNameRandom = ''.join( random.choice(string.ascii_lowercase + string.digits) for x in range(6) )

    def CreateWindow(self):
        reg = self.RegisterClass()
        hwnd = self.BuildWindow(reg)
        return hwnd


    def RegisterClass(self):
        WndProc = { WM_DESTROY: self.OnDestroy }
        wc = win32gui.WNDCLASS()
        wc.hInstance = self.hinst
        wc.hbrBackground = COLOR_BTNFACE + 1
        wc.hCursor = win32gui.LoadCursor(0, IDC_ARROW)
        wc.hIcon = win32gui.LoadIcon(0, IDI_APPLICATION)
        wc.lpszClassName = 'FontFuzzer{}'.format(self.classNameRandom)
        wc.lpfnWndProc = WndProc
        reg = win32gui.RegisterClass(wc)
        return reg

    def BuildWindow(self, reg):
        hwnd = windll.user32.CreateWindowExW (
            WS_EX_TOPMOST | WS_EX_NOACTIVATE,
            reg, # atom returned by RegisterClass
            'FontFuzzer{}'.format(self.classNameRandom),
            WS_POPUP,
            10,
            10,
            2000,
            200,
            0,
            0,
            self.hinst,
            0 )

        windll.user32.ShowWindow(hwnd, SW_SHOW)
        windll.user32.UpdateWindow(hwnd)
        return hwnd


    def OnDestroy(self, hwnd, message, wparam, lparam):
        win32gui.PostQuitMessage(0)
        return True


def draw(handleDeviceContext, char_map):

        chars_not_rendered = 0
        chars_rendered = 0

        array_types = c_wchar * len(char_map)
        var1 = array_types()

        for y in range(0, len(char_map) ):

            var1[y] = char_map[y]

            ETO_GLYPH_INDEX = 16
            
            result = windll.gdi32.ExtTextOutW(  handleDeviceContext,
                                                5,
                                                5,
                                                ETO_GLYPH_INDEX,
                                                None,
                                                var1,
                                                len(var1),
                                                None )

            #try:
            #    print '[D]\t{} : {}'.format(var1[y], result)
            #except:
            #    continue

            if result == 0:
                chars_not_rendered +=1
            elif result == 1:
                chars_rendered += 1

        return chars_rendered, chars_not_rendered


def deployMultiProcess(fontPath, queue):
    
    try:
        charsRendered, charsNotRendered = deploy(fontPath, ttLib.TTFont(fontPath))
        queue.put(charsRendered)
        queue.put(charsNotRendered)
    except IOError as e:
        print '[E] Issues', e







def deploy(fontPath, ttfInstance=None):

    # setup
    fontName = shortName(ttfInstance)[1] #''.join( random.choice(string.digits) for i in range(0,6) )
    lf = win32gui.LOGFONT()
    number_of_font_added = windll.gdi32.AddFontResourceExA(fontPath, FR_PRIVATE, None)

    if number_of_font_added != 1:
        print "[WTF] Clusterfuck: invalid font"
        return 0,0

    win = mainWindow()
    hwnd = win.CreateWindow()
    hdc = windll.user32.GetDC(hwnd)

   

    # draw some crap
    chars_not_rendered = 0
    chars_rendered = 0
    
    for j in range(10, 100, 10):
        time.sleep(.1)
        lf.lfHeight     = j #int(random.choice(string.digits))
        lf.lfFaceName   = fontName
        lf.lfWidth      = j #int(random.choice(string.digits))
        lf.lfEscapement = 0
        lf.lfOrientation= 0
        lf.lfWeight     = FW_NORMAL
        lf.lfItalic     = False  
        lf.lfUnderline  = False
        lf.lfStrikeOut  = False
        lf.lfCharSet    = DEFAULT_CHARSET
        lf.lfOutPrecision = OUT_DEFAULT_PRECIS
        lf.lfClipPrecision = CLIP_DEFAULT_PRECIS
        lf.lfPitchAndFamily = DEFAULT_PITCH|FF_DONTCARE

        hFont = win32gui.CreateFontIndirect(lf)
        oldFt = win32gui.SelectObject(hdc, hFont) # replace font

        #print '[*]', lf.lfFaceName, ':', lf.lfWidth, ' - ', lf.lfHeight

        # chars to draw
        char_map = [ chr(i) for i in range(1,255) ]


        chars_rendered_current, chars_not_rendered_current = draw(hdc, char_map)
        chars_rendered += chars_rendered_current
        chars_not_rendered += chars_not_rendered_current
            
        windll.gdi32.DeleteObject( win32gui.SelectObject(hdc, oldFt) )
        windll.gdi32.GdiFlush()
        windll.gdi32.RemoveFontResourceExW( fontPath, FR_PRIVATE, None)
        
    print '[*]\t{} chars not rendered'.format(chars_not_rendered)
    print '[*]\t{} chars rendered'.format(chars_rendered)

    # bail    
    releaseResult = windll.user32.ReleaseDC(hwnd, hdc)
    if releaseResult == 0:
        print '[E] ReleaseDc failed'
    
    
    destroyResult = windll.user32.DestroyWindow(hwnd)
    if destroyResult == 0:
        print '[E] Destroy Window error {}'.format(GetLastError())
    

    print '[*] Destroy window'
    return chars_rendered, chars_not_rendered




def generateTestCases(fontSourceDir, dbConnection):
    fonts = {}
    testcasesFolder = 'testcases'

    print '[D] ', os.path.abspath( fontSourceDir )

    for i in os.listdir( fontSourceDir ):
            
        

        print '----------- Start -------------------'
        
        try:
            print '[*] Loading', i
        except UnicodeEncodeError as e:
            print '[D] Font name\'s screwed:', e
            
            
        abspath =  os.path.abspath( fontSourceDir + '\\' + i)

        try:
            tt = TTF.TTFont(abspath)
            fonts[abspath] = tt
            
            print '[*] Fuzzing {}'.format(abspath)
            
            fileInMemory, isFontFuzzed, numberOfBytesChanged = fonts[abspath].fuzzFontBytecode()
            #fonts[abspath].fuzzDirectoriesBitFlipping()
            #fileInMemory = fonts[abspath].fuzzCffTableBitFlipping()


            if isFontFuzzed:
                testcaseName = os.path.abspath( os.path.join( testcasesFolder,
                                                              os.path.basename(abspath).split('.ttf')[0] + '_' +
                                                              ''.join( random.choice( string.ascii_lowercase + string.digits) for x in range(8) ) + '.ttf')
                                                )

                open( testcaseName, 'wb').write(fileInMemory)
                
                b = hashlib.md5()
                b.update(fileInMemory)
                h = b.hexdigest()

                query = "INSERT INTO results(md5, bytesChanged, fuzzer, fileName, createTime) VALUES ( '{}', '{}', 'native', '{}', '{}')".format(h, numberOfBytesChanged, os.path.basename(abspath), datetime.datetime.now() )
                print "WTF", query
                try:
                    res = dbConnection.execute(query)
                    res = dbConnection.commit()

                    
                except Exception as e:
                    print '[F]', e
                    
                
                #self.fontsPath.append( '/static' + testcaseName.split('/static')[1] )

            else:
                print '[*] Font {} not fuzzed'.format(abspath)
           

            print '------------ End -------------------'
        except Exception as e:
            print e
            continue
        
    return len( os.listdir(testcasesFolder) )


def viewerDeploy(dbConnection, fuzzerRef):

    print '[*] Deploy fonts found in testcases folder'
    for i in os.listdir('testcases'):
        
        if fuzzerRef.stopMe:
            return
        
        try:
            print '[*] Testing {}'.format(i)
            abspath = os.path.abspath('testcases' + '\\' + i)


            renderTime = str(datetime.datetime.now())
            print '[*] Spawn a process for rendering {}'.format(abspath)
            queue = Queue()
            p = Process( target=deployMultiProcess, args=( abspath, queue) )
            p.start()
            p.join()

            charsRendered = queue.get()
            charsNotRendered = queue.get()
            

            # performance wise it's crap
            b = hashlib.md5()
            b.update(open(abspath, 'rb').read())
            h = b.hexdigest()

            try:
                res = dbConnection.execute("UPDATE results SET charsRendered=?, charsNotRendered=?, renderTime=? WHERE md5=?", (charsRendered, charsNotRendered, renderTime, h))
                dbConnection.commit()

                # crap, clear the 1 elem queue
                with fuzzerRef.queue.mutex:
                    fuzzerRef.queue.queue.clear()
                    
                result = dbConnection.execute("SELECT * FROM results WHERE md5=?", (h,)).fetchone()

                # time now - font name - fuzzer name - bytes changed - chars rendered - chars not rendered - ctime - render time
                message = str( datetime.datetime.now() ) + '@@@' + str(result[5]) + '@@@' + str(result[4]) + '@@@' + str(result[1]) + '@@@'+ str(result[2]) + '@@@'+ str(result[3]) + '@@@'+ str(result[6]) + '@@@'+ str(result[7])
                fuzzerRef.queue.put( message )

                
            finally:
                # in case shit happens and the sqlite is pure crap
                dbConnection.commit()
            

        except Exception as e:
            print '[E] Issues parsing font {}: {}'.format(i, e)
            continue
  
   


def validateInputFonts(fontSourceDir):
    fonts = {}
    for i in os.listdir(sys.argv[1]):
        try:
            abspath =  os.path.abspath(sys.argv[1] + '\\' + i)
            tt = ttLib.TTFont(abspath)
            fonts[abspath] = tt
            print '[*] Validated {} TTF'.format(shortName(tt)[1])
        except Exception as e:
            print '[E] Issues parsing font {}: {}'.format(i, e)
            continue


def cleanUp():
    
    print '[*] Cleaning up fuzzed fonts'
    
    old   = 'old_testcases'
    tbdel = 'testcases_to_be_deleted'
    curr  = 'testcases'
    
    shutil.rmtree(tbdel)
    shutil.move(old, tbdel)
    shutil.move(curr, old)
    os.mkdir(curr)
    

'''
For fuzzing framework
'''
class NativeFuzzer(threading.Thread):
    
    def __init__(self, folder, queue):
        threading.Thread.__init__(self)
        self.fontsFolder = folder
        self.stopMe = False
        self.dbConnection = sqlite3.connect('agent1.db', check_same_thread = False, timeout=1, detect_types=sqlite3.PARSE_DECLTYPES)
        self.queue = queue


        # setup code
        try:
            os.mkdir('testcases_to_be_deleted')
            os.mkdir('testcases')
            os.mkdir('old_testcases')
        except OSError as e:
            print e


    def run(self):
    
        while not self.stopMe:
        
            # 2] generate test cases
            numberOfTestCases = generateTestCases(self.fontsFolder, self.dbConnection)
        
            print '[*] Generated {} test cases'.format(numberOfTestCases)
        
            # 3] deploy
            viewerDeploy(self.dbConnection, self) # shit args
            cleanUp()

        self.dbConnection.commit()
        self.dbConnection.close()
            

    def stop(self):
        self.stopMe = True
        
    
    def getDescription(self):
        return 'Native fuzzer'


def getFuzzerInstance(folder, queue):
    return NativeFuzzer(os.path.join('fonts_extracted', folder), queue)


if __name__ == '__main__':
 
 
    if( len(sys.argv[1:]) < 1 ):
        print 'Usage: {} font_directory'.format(sys.argv[0])

    elif( len(sys.argv[1:]) == 2 and sys.argv[1] == 'd'):
        try:
            abspath = os.path.abspath(sys.argv[2])
            print 'Testing font {}'.format(abspath)
            deploy(abspath, ttLib.TTFont(abspath) )

        except Exception as e:
            print '[E] Issues parsing font {}: {}'.format(sys.argv[2], e)
            
    # fuzz
    else:
        for i in range(0, 1):
            #break

            # 2] generate test cases
            numberOfTestCases = generateTestCases(sys.argv[1])

            print '[*] Generated {} test cases'.format(numberOfTestCases)


            for i in os.listdir('testcases'):
                m = hashlib.md5()
                m.update(open('testcases' + '\\' + i, "rb").read())
                print '[*]\t {} : {}'.format(i, m.hexdigest())


            # 3] deploy
            viewerDeploy()


        
        
