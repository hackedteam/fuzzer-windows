#!/usr/bin/env python

# awful
import sys
sys.path.append('../')
import parsers.TTF as TTF

import os
import time
import random
import shutil
import string
import struct
import hashlib
import win32api
import win32gui
import threading

from ctypes import *
from struct import *
from win32con import *
from fontTools import ttLib



FONT_SPECIFIER_NAME_ID = 4
FONT_SPECIFIER_FAMILY_ID = 1
FR_PRIVATE=0x10


def shortName(font):
    name = ""
    family = ""

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
            400,
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
    

def deploy(fontPath, ttfInstance=None):


    # setup
    fontName = ''.join( random.choice(string.digits) for i in range(0,6) ) #shortName(ttfInstance)[1]
    lf = win32gui.LOGFONT()
    number_of_font_added = windll.gdi32.AddFontResourceExA(fontPath, FR_PRIVATE, None)
    assert number_of_font_added == 1,  'Font not added' # TODO: what happens when a font is not added?

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
    windll.user32.ReleaseDC(hwnd, hdc)
    windll.user32.DestroyWindow(hwnd)
    print '[*] Destroy window'
    time.sleep(1)



def generateTestCases(fontSourceDir):
    fonts = {}

    testcasesFolder = 'testcases'
    
    for i in os.listdir(sys.argv[1]):
            
        print '----------- Start -------------------'
        print '[*] Loading {}'.format(i)
        abspath =  os.path.abspath(sys.argv[1] + '\\' + i)

        try:
            tt = TTF.TTFont(abspath)
            fonts[abspath] = tt
            
            print '[*] Fuzzing {}'.format(abspath)
            
            fileInMemory, isFontFuzzed = fonts[abspath].fuzzFontBytecode()
            #fonts[abspath].fuzzDirectoriesBitFlipping()
            #fileInMemory = fonts[abspath].fuzzCffTableBitFlipping()


            if isFontFuzzed:
                testcaseName = os.path.abspath( os.path.join( testcasesFolder,
                                                              os.path.basename(abspath).split('.otf')[0] + '_' +
                                                              ''.join( random.choice( string.ascii_lowercase + string.digits) for x in range(8) ) + '.otf')
                                                )

                open( testcaseName, 'wb').write(fileInMemory)
                self.fontsPath.append( '/static' + testcaseName.split('/static')[1] )

            else:
                print '[*] Font {} not fuzzed'.format(abspath)
           

            print '------------ End -------------------'
        except Exception as e:
            print e
            continue
    
    return len( os.listdir(testcasesFolder) )


def viewerDeploy():

    print '[*] Deploy fonts found in testcases folder'
    for i in os.listdir('testcases'):
        try:
            print '[*] Testing {}'.format(i)
            abspath = os.path.abspath('testcases' + '\\' + i)
            deploy(abspath, None) #ttLib.TTFont(abspath) )

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
    for i in os.listdir('testcases'):
        try:
            #shutil.move('testcases\\' + i, 'archive\\' + i)
            os.remove('testcases\\' + i)
        except:
            continue

'''
For fuzzing framework
'''
class NativeFuzzer(threading.Thread):
    
    def __init__(self, folder):
        self.fontsFolder = folder
        self.stopMe = False

   
    def run(self):
    
        while not self.stopMe:
        
            # 2] generate test cases
            numberOfTestCases = generateTestCases(self.fontsFolder)
        
            print '[*] Generated {} test cases'.format(numberOfTestCases)
        

            for i in os.listdir('testcases'):
                m = hashlib.md5()
                m.update(open('testcases' + '\\' + i, "rb").read())
                print '[*]\t {} : {}'.format(i, m.hexdigest())
                            
            # 3] deploy
            viewerDeploy()

    def stop(self):
        self.stopMe = True        
        
    
    def getDescription(self):
        return 'Native fuzzer'


def getFuzzerInstance(folder):
    return NativeFuzzer(folder)


if __name__ == '__main__':
 
 
    if( len(sys.argv[1:]) < 1 ):
        print 'Usage: {} font_directory'.format(sys.argv[0])

    elif( len(sys.argv[1:]) == 2 and sys.argv[1] == 'd'):
        try:
            print '[*] Testing {}'.format(sys.argv[2])
            abspath = os.path.abspath(sys.argv[2])
            deploy(abspath, ttLib.TTFont(abspath) )

        except Exception as e:
            print '[E] Issues parsing font {}: {}'.format(sys.argv[2], e)
            
        
    else:

        # display font
        if len(sys.argv[1:]) == 2 and sys.argv[1] == 'd':
            abspath = os.path.abspath(sys.argv[2])
            deploy(abspath, ttLib.TTFont(abspath))

        # fuzz
        else:
            for i in range(0, 2):
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


        
        
