#!/usr/bin/env python

import os
import sys
import time
import base64
import urllib
import netaddr
import sqlite3
import tarfile
import cStringIO
import netifaces


import tornado.gen
import tornado.web
import tornado.escape
import tornado.ioloop
import tornado.httpclient
import tornado.httpserver



# db filename
SERVER_DB = 'server.db'
DB_CONNECTION = None

class ServerDashboardHandler(tornado.web.RequestHandler):
    
    def get(self, uri):
        
        # fetch the connected agents
        availableAgents = []
      
        results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
        for row in results:
            availableAgents.append( row[0] )
                  
                  
        self.render('templates/serverDashboard.html', agents = availableAgents )        
        
    

class ServerMainHandler(tornado.web.RequestHandler):

    def get(self):
        self.write('Available modules')
        self.write('<ul>')
        self.write('<li><a href="/dashboard">/dashboard/</a>')
        self.write('<li><a href="/fonts">/fonts/</a>')
        self.write('<li><a href="/fuzzers">/fuzzers/</a>')
        self.write('<li><a href="/results">/results/</a>')
        self.write('<li><a href="/communication">/communication/</a>')
        self.write('<li><a href="/updates">/updates</a>')
        self.write('</ul>')


'''
Handle font requests from clients
'''
class ServerFontsHandler(tornado.web.RequestHandler):
    
    def get(self, uri):

        uriFields = uri.split('/')

        # path of folder containing fonts 
        # FIXME: should come up with more clever design to keep this path 'global'
        fontsFolder = os.path.join(os.path.dirname(__file__), 'fonts')

        # top level request returns a list of the folders available
        # and a list of connected agents. A user can assign a folder
        # to an agent
        if uri == '':
            

            # fetch the fonts folder available
            availableFontsFolder = []

            for folder in os.listdir(fontsFolder):
                folder = os.path.join( fontsFolder, folder)
                if os.path.isdir( folder ):
                    availableFontsFolder.append( os.path.basename(folder))


            # fetch the connected agents
            availableAgents = []

            results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
            for row in results:
                availableAgents.append( row[0] )
            
            
            self.render('templates/serverFonts.html', fontsFolder = availableFontsFolder, agents = availableAgents )
             
        # fonts requests
        #
        # e.g. 
        elif len(uriFields) == 2 and  uriFields[0] == 'folder':
            
            print 'font pull request'
            
            # FIXME: better design than tarbz2 on demand
            archive = cStringIO.StringIO()
            tar = tarfile.open( fileobj=archive, mode='w:bz2')

            home = os.getcwd()
         
            try:
                os.chdir('fonts')
                tar.add( uriFields[1] )
                tar.close()
            finally:
                os.chdir(home)

            print '{} size {}'.format(uriFields[1], len(archive.getvalue()) )
            

            # send tar.bz2 as body
            self.set_header('Content-Type','application/octet-stream')
            self.write(archive.getvalue())
            
            
        else:
            self.write('GET ServerFontsHandler {}'.format(uri))
                    

class ServerFuzzersHandler(tornado.web.RequestHandler):
    
    @tornado.gen.coroutine        
    def get(self, uri):
        
        uriFields = uri.split('/')

        if uri == '':
            
            # fetch the connected agents
            availableAgents = []

            results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
            for row in results:
                availableAgents.append( row[0] )


            # fetch available fuzzers
            availableFuzzers = []
            
            # FIXME: just pick all the *py from 'fuzzers' folder atm
            fuzzersFolder = 'fuzzers'

            for f in os.listdir(fuzzersFolder):
                f = os.path.join(fuzzersFolder, f)
                if os.path.isfile(f) and f.endswith('.py') and not os.path.basename(f).startswith('__'):
                    availableFuzzers.append( os.path.basename(f) )
            
            self.render('templates/serverFuzzers.html', fuzzers = availableFuzzers, agents = availableAgents)

        elif len(uriFields) == 1:
            
            self.set_header('Content-Type','text/plain')
            data = open('fuzzers/{}'.format(uriFields[0]), 'r').read()
            self.write( data )

        else:
            self.write("GET {}".format(uri))


    @tornado.gen.coroutine        
    def post(self, uri):
        uriFields = uri.split('/')
                 
                    
        # extract from json array the list of nodes
        # we need to send the fuzzer to, then proceed
        if len(uriFields) == 1:        
            
            fuzzer = uriFields[0]
                        
            agents = tornado.escape.json_decode(self.request.body)
      
            if len(agents) == 0:
                self.write('No agents')
                return
      
      
            for a in agents:
                
                      
                url = 'http://{}/fuzzers/{}'.format(a, fuzzer)
                      
                httpClient = tornado.httpclient.AsyncHTTPClient()
                httpRequest = tornado.httpclient.HTTPRequest(url, method='POST', headers=None, body='', request_timeout=120 )
                httpResponse = yield httpClient.fetch(httpRequest)
                  
                  
        else:
            self.write('Krap', uri)        
        

class ServerUpdatesHandler(tornado.web.RequestHandler):
    
    
    def get(self, uri):
        uriFields = uri.split('/')
        
        # show list of available nodes
        if uri == '':

            # fetch the connected agents
            availableAgents = []
          
            results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
            for row in results:
                availableAgents.append( row[0] )
          
          
            self.render('templates/serverUpdates.html', agents = availableAgents)                    


    @tornado.gen.coroutine   
    def post(self, uri):

        uriFields = uri.split('/')
              
        # extract from json array the list of nodes
        # we need to send the updates to, then proceed
        if uri == '':        
            
            agents = tornado.escape.json_decode(self.request.body)

            if len(agents) == 0:
                self.write('No agents')
                return


            for a in agents:

                self.write('Sending updates {} <br>'.format( a ) )
                
                url = 'http://{}/updates'.format(a)
                updateBat = open('update.bat', 'r').read()

                try:
                    httpClient = tornado.httpclient.AsyncHTTPClient()
                    httpRequest = tornado.httpclient.HTTPRequest(url, method='POST', headers=None, body=base64.b64encode(updateBat), request_timeout=120 )
                    httpResponse = yield httpClient.fetch(httpRequest)
                except Exception as e:
                    pass

            
            
        else:
            self.write('Krap', uri)


class ServerResultsHandler(tornado.web.RequestHandler):


    
    def get(self, uri):
        uriFields = uri.split('/')
        
        # show list of available nodes
        if uri == '':

            # fetch the connected agents
            availableAgents = []
          
            results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
            for row in results:
                availableAgents.append( row[0] )
          
          
            self.render('templates/serverResults.html', agents = availableAgents)            
            

'''
Not a good design, handles: 
- ui to add a new agent (@GET)
- send a new server to an agent (@POST)
- handle agent pings towards the server (@POST)
'''
class ServerCommunicationHandler(tornado.web.RequestHandler):


    @tornado.gen.coroutine        
    def get(self, uri):

        uriFields = uri.split('/')

        # print the list of connected agents and let the user connect a new agent
        if uri == '':

            # fetch the connected agents
            availableAgents = []

            results = DB_CONNECTION.execute('SELECT * FROM AGENTS')
            for row in results:
                availableAgents.append( row[0] )


            self.render('templates/serverCommunication.html', agents = availableAgents)

        elif uriFields[0] == 'agents' and uriFields[2] == 'capabilities': 
            
            ip = uriFields[1]

            # query the agent for its fonts folders, fuzzers and results
            httpClient = tornado.httpclient.AsyncHTTPClient()
            httpRequest = tornado.httpclient.HTTPRequest('http://{}/communication/capabilities/'.format( ip) )
            httpResponse = yield httpClient.fetch(httpRequest)


            # response is a json object
            json = tornado.escape.json_decode(httpResponse.body )
            
            
            availableFontsFolder = []
            
            for f in json['fontFolders']:
                availableFontsFolder.append(f)


            availableFuzzers = []
            for f in json['fuzzers']:
                availableFuzzers.append(f)

               

            self.render('templates/serverCommunicationManageAgent.html', ip=ip, fontsFolder = availableFontsFolder,
                                                                         fuzzers = availableFuzzers)  

            

        else:
            self.write("GET {}".format(uri))


    @tornado.gen.coroutine        
    def post(self, uri):


        uriFields = uri.split('/')
        
        # this query is generated from the server itself
        #
        # e.g. http://localhost:81/communication/agents/127.0.0.1/asdf
        #      server contacts agent 127.0.0.1 with name 'asdf' telling
        #      that server is now its master
        if uriFields[0] == 'agents' and len(uriFields) == 3 and uriFields[2] != 'capabilities' \
                                                            and uriFields[2] != 'jobs': #FIXME: awful, change negative check

            # FIXME: nicer way to get localhost public ip
            try:
                serverIP = netifaces.ifaddresses(netifaces.interfaces()[1]).setdefault(netifaces.AF_INET)[0]['addr']
                netaddr.IPAddress(serverIP)
                
            except netaddr.core.AddrFormatError as e:
                self.write(e)
                return
        
            serverConf = {
                'ip': serverIP,
                'port': 81    # FIXME: fetch server port
                }
            serverConfJson = tornado.escape.json_encode(serverConf)
        

            httpClient = tornado.httpclient.AsyncHTTPClient()
            httpRequest = tornado.httpclient.HTTPRequest("http://{}/communication/servers/{}".format(uriFields[1],serverIP), method='POST', headers=None, body=serverConfJson)
            httpResponse = yield httpClient.fetch(httpRequest)

            # FIXME: check agent reply before db insertion
            self.write(httpResponse.body)

            
            # insert agent into AGENTS table
            try:
                query = "INSERT INTO agents VALUES ('{}', '80', '{}', '{}')".format(uriFields[1], time.ctime(), uriFields[2])
                res = DB_CONNECTION.execute(query)
            
                for i in  res:
                    print '\tres:',i

                res = DB_CONNECTION.commit()

                print 'Commit', res

            except sqlite3.IntegrityError as e:
                # FIXME: update time prolly
                print 'Agent already inserted', e
                
                

        # handle agent pings
        #
        # e.g http://localhost:81/communication/agents/127.0.0.1/active
        elif uriFields[0] == 'agents' and uriFields[2] == 'active': # FIXME: 'active' not rest at all
            #TODO
            pass

        # route font pull request towards client
        #
        # e.g. http://localhost:81/communication/fonts/fonts_8/192.168.1.1
        elif uriFields[0] == 'fonts' and len(uriFields) == 3:
            print "Routing pull request"
            
            httpClient = tornado.httpclient.AsyncHTTPClient()
            httpRequest = tornado.httpclient.HTTPRequest('http://{}/fonts/folder/{}'.format(uriFields[2], uriFields[1]))
            httpResponse = yield httpClient.fetch(httpRequest)

            self.write('Agent says: {}'.format(httpResponse.body))

        # agent management
        #
        # e.g. http://localhost:81/communications/agents/127.0.0.1/capabilities
        elif uriFields[0] == 'agents' and uriFields[2] == 'capabilities': 
            self.write('capabilities post')

        else :
            self.write('ServerCommunication post: {}'.format(uri))
    
        

        

def serverSetup():
    
    print '[*] Server setup..'

    connection = sqlite3.connect(SERVER_DB, detect_types=sqlite3.PARSE_DECLTYPES)


    print '[*]\tcreating table: AGENTS'
    connection.execute('''CREATE TABLE agents
                          (IP TEXT PRIMARY KEY NOT NULL,
                           PORT TEXT NOT NULL,
                           TIME_LAST_PING TEXT,
                           NAME TEXT);
''')

    connection.close()


def run():

    # connect to db
    global DB_CONNECTION
    DB_CONNECTION = sqlite3.connect(SERVER_DB, detect_types=sqlite3.PARSE_DECLTYPES)

    
    # start tornado
    settings = { "static_path": os.path.join( os.path.dirname(__file__), "static"),
                 }

    application = tornado.web.Application (
        debug = True,
        handlers = [ (r'/', ServerMainHandler),
                     (r'/dashboard/?(.*)', ServerDashboardHandler),
                     (r'/fonts/?(.*)',   ServerFontsHandler),
                     (r'/fuzzers/?(.*)', ServerFuzzersHandler),
                     (r'/results/?(.*)', ServerResultsHandler),
                     (r'/communication/?(.*)', ServerCommunicationHandler),
                     (r'/updates/?(.*)', ServerUpdatesHandler),
                     ],
        **settings )

    server = tornado.httpserver.HTTPServer(application)
    server.listen(81)
    tornado.ioloop.IOLoop.instance().start()      





if __name__ == '__main__':

    if len(sys.argv) == 2 and sys.argv[1] == 'setup':
        serverSetup()
    elif len(sys.argv) == 1:
        run()




# '''
# This handlers routes request to a suitable handler
# Probably useless
# '''
# class ServerBrokerHandler(tornado.web.RequestHandler):


#     def get(self, uri):
#         pass

#     #@tornado.gen.coroutine        
#     def post(self, uri):

#         if uri == 'communication/agent/new':

#             try:
#                 agentIp = self.get_argument("ip")
#                 agentName = self.get_argument("name")
                
#                 # validate ip
#                 netaddr.IPAddress(agentIp)

#             except tornado.web.MissingArgumentError as e:
#                 self.write('Not enough args', e)
#                 return
#             except netaddr.core.AddrFormatError as e:
#                 self.write(e)
#                 return
                
#             # dbg
#             self.write('Got {} {}'.format(agentIp, agentName))

#             # restify the query
#             uri = "http://localhost:81/communication/agents/{}/{}".format(agentIp, agentName)
            
#             # httpRequest = tornado.httpclient.HTTPRequest(uri, method='POST')
#             # httpClient = tornado.httpclient.AsyncHTTPClient()
#             # httpResponse = httpClient.fetch(httpRequest)

            
                
#         else:
#             self.write(uri)
