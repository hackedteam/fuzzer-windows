#!/usr/bin/env python

import sys
sys.path.append('../')
import parsers.TTF as TTF

import re
import os

import random
import string
import uimodules

import tornado.web
import tornado.ioloop
import tornado.httpserver


FUZZING_INSTANCES = {}

class MainHandler(tornado.web.RequestHandler):
    
    def get(self):

        # force 'IE9 standards' document mode, otherwise it will switch to quirks mode and fonts won't be rendered
        self.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">') 
        self.write('<html><body>')

        self.write('Active instances: {}<br>'.format(len(FUZZING_INSTANCES.keys())))
        for i in FUZZING_INSTANCES:
            self.write('{} <a href="/font/{}">Go</a><br>'.format(i, i))



        # list available folder with samples in a radio button
        self.write('<form action="/" method="post">')

        folders = []
        for d in [ os.path.join( os.path.dirname(__file__), 'static', d) for d in os.listdir(  os.path.join( os.path.dirname(__file__), 'static') ) ]:
            if os.path.isdir(d) and re.match( '[0-9]{10}', os.path.basename(d)) == None: # skip also generated testcases
                folders.append(d)


        for d in folders:
            self.write('<input type="radio" name="folder" value="{}">{}<br>'.format(os.path.basename(d), os.path.basename(d)))
        
        

        self.write('<input type="submit" value="Start fuzzing">'
                   '<input type="hidden" name="newInstance" value="newInstance">'
                   '</form>')


        self.write('</html></body>')


    def post(self):
        
        self.set_header('Content-Type', 'text/plain')

        try:
            self.get_argument("newInstance")
            folder = self.get_argument('folder')
        except tornado.web.MissingArgumentError:
            self.write('Wrong post')
            return


        while True:
            instanceId = ''.join([random.choice(string.digits) for i in range(0, 10) ])
            if instanceId not in FUZZING_INSTANCES.keys():
                break
            
        
        self.redirect('/font/{}/{}'.format(instanceId, folder))



class FontFuzzer(tornado.web.RequestHandler):

    def initialize(self):
                
        # generate samples for this run
        self.fontsPath = []


    
    def get(self, instanceId, folder):


        # don't remember wheter initialize is called upon every call..
        self.fontsPath = []

        testcasesFolder = 'static/{}'.format(instanceId)
        
        if instanceId not in FUZZING_INSTANCES.keys():
            os.mkdir(testcasesFolder)
            FUZZING_INSTANCES[instanceId] = ''


        # 1] folder must exists
        fontSourceFolder = os.path.join(os.path.dirname(__file__), 'static/{}'.format(folder))
        if not os.path.isdir(fontSourceFolder):
            self.write('Folder {} doesn not exist - can\'t create testcases'.format(folder))
            return
        

        # 2] generate samples
        fonts = {}
        for font in os.listdir(fontSourceFolder):
            try:
                abspath = os.path.abspath( os.path.join(fontSourceFolder, font) )
                tt = TTF.TTFont(abspath)
                fonts[abspath] = tt
            
                print '[*] Fuzzing {}'.format(abspath)
            
                #fonts[abspath].fuzzFontBytecode()
                #fonts[abspath].fuzzDirectoriesBitFlipping()
                #fileInMemory = fonts[abspath].fuzzCffTableBitFlipping()
                fileInMemory = fonts[abspath].fuzzFontBytecode()
            
                testcaseName = os.path.abspath( os.path.join( testcasesFolder,
                                                              os.path.basename(abspath).split('.otf')[0] + '_' +
                                                              ''.join( random.choice( string.ascii_lowercase + string.digits) for x in range(8) ) + '.otf')
                                                )

                open( testcaseName, 'wb').write(fileInMemory)
                self.fontsPath.append( '/static' + testcaseName.split('/static')[1] )
                                       

            except Exception as e:
                print e
                



        self.render('testcase.html', fonts=self.fontsPath, instanceId=instanceId, folder=folder) 




if __name__ == '__main__':

    settings = { "ui_modules": uimodules,
                 "static_path": os.path.join( os.path.dirname(__file__), "static"),
                 }    

    
    # map ULRs/patterns to RequestHandlers
    application = tornado.web.Application( 
        handlers = [ (r'/', MainHandler), 
                     (r'/font/([0-9]{10})/(.+)', FontFuzzer), 
                     ],
        **settings)
    
    server = tornado.httpserver.HTTPServer(application)
    server.listen(80)
    tornado.ioloop.IOLoop.instance().start()
