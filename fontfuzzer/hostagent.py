#!/usr/bin/env python

import os
import imp
import sys
import time
import Queue
import base64
import shutil
import sqlite3
import tarfile
import datetime
import cStringIO
import threading
import subprocess


import tornado.gen
import tornado.web
import tornado.ioloop
import tornado.escape
import tornado.httpclient
import tornado.httpserver


# no time for desing patterns
JOBS_MANAGER = None

# db filename
SERVER_DB = 'server.db'
DB_CONNECTION = None

#mocks
SERVER_IP = ''
SERVER_PORT = ''

def getServerIP():
    return SERVER_IP

def getServerPort():
    return SERVER_PORT

def setServerIP(ip):
    SERVER_IP = ip

def setServerPort(port):
    SERVER_PORT = port

# db filename
AGENT_DB = 'agent1.db'

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        pass


class DashboardHandler(tornado.web.RequestHandler):
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*");    
    
    def get(self, uri):
                
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('Cache-Control', 'no-cache')    
        
        # N.B there should be a deadlock condition, check jobsLock vs queue
        #     should be safe with one job per node        
        
        # pick the last testcase the last job queue
        #print 'acquire lock'
        JOBS_MANAGER.jobsLock.acquire()
        jobs = JOBS_MANAGER.getFuzzingJobs()
         
        if len(jobs) == 0:
            
            json = {
                'timeNow'   : str(datetime.datetime.now()).split('.')[0],
                'fontName'  : 'No jobs running',
            }                
            
            response = u'data: ' + tornado.escape.json_encode(json) + u'\n\n'
        else:
            queue = jobs[len(jobs) -1][3]
            message = queue.get().split('@@@')
            
            # create js obj len(message) == 7
            # time now - font name - fuzzer name - bytes changed - chars rendered - chars not rendered - ctime - render time
            print '[AA]', message[0]
            json = {
                'timeNow'       : message[0].split('.')[0],
                'fontName'      : message[1],
                'fuzzerName'    : message[2],
                'bytesChanged'  : message[3],
                'charsRendered' : message[4],
                'charsNotRendered' : message[5],
                'creationTime'  : message[6].split('.')[0],
                'renderTime'    : message[7].split('.')[0],
            }
            
            response = u'data: ' + tornado.escape.json_encode(json) + u'\n\n'

        JOBS_MANAGER.jobsLock.release()
        
        #print '[M] ->', response
        #print 'release lock'
        
        self.write(response)
        self.flush()
        

'''
Handle font related messages:
- request from server to pull fonts
- pull fonts from server
'''
class FontsHandler(tornado.web.RequestHandler):
    
    @tornado.gen.coroutine   
    def get(self, uri):
        uriFields = uri.split('/')

        
        # pull fonts from server
        # 
        # e.g. http://localhost/fonts/folder/fontFolder
        if uriFields[0] == 'folder' and len(uriFields) == 2:
            fontFolder =  uriFields[1] 
            
            # fetch master server, FIXME: atm nobody checks that there's only one master
            query = "SELECT * FROM server WHERE MASTER == 1"
            res = DB_CONNECTION.execute(query)
            
            server = res.fetchone() 
            ip = server[0]
            port = server[1]

            # now pull the files
            self.write("pulling fonts {}".format(uriFields[1]))
            
            httpClient = tornado.httpclient.AsyncHTTPClient()
            httpRequest = tornado.httpclient.HTTPRequest('http://{}:{}/fonts/folder/{}'.format(ip,port,fontFolder))
            
            httpResponse = yield httpClient.fetch(httpRequest)
            
            # body is a tar.bz2 containing the font folder
            archive = cStringIO.StringIO( httpResponse.body )
            
            print 'Received size {}'.format( len(archive.getvalue() ) )
            
            tar = tarfile.open(fileobj=archive, mode='r:bz2')
            
            tar.extractall(path='fonts_extracted')
            
            tar.close()
            
        
        else:
            self.write("GET /fonts {}".format(uriFields) )


    @tornado.gen.coroutine        
    def post(self, uri):
        print self.request
        print '---'
        print uri


        
'''
Handle fuzzer updates
'''
class FuzzersHandler(tornado.web.RequestHandler):
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*");


    def get(self, uri):
         
        uriFields = uri.split('/')
        
        print 'GET FuzzersHandler', uriFields

    @tornado.gen.coroutine        
    def post(self, uri):
        uriFields = uri.split('/')
        
        # handle fuzzer fetch/update requests
        #
        # e.g. http://localhost/fuzzers/native.py
        if len(uriFields) == 1:

            # fetch 'fuzzerName' from master server
            fuzzerName = uriFields[0]
            
            # fetch master server, FIXME: atm nobody checks that there's only one master
            query = "SELECT * FROM server WHERE MASTER == 1"
            res = DB_CONNECTION.execute(query)
            
            server = res.fetchone() 
            serverIp = server[0]
            serverPort = server[1]
            

            httpClient = tornado.httpclient.AsyncHTTPClient()
            httpRequest = tornado.httpclient.HTTPRequest('http://{}:{}/fuzzers/{}'.format(serverIp, serverPort, fuzzerName))
            httpResponse = yield httpClient.fetch(httpRequest)

            # response is a text file (python script)
            fuzzer = httpResponse.body
            
            # write fuzzer to disk, overwrite in case
            with open('fuzzers_downloaded/{}'.format(fuzzerName), 'w') as f:
                f.write(fuzzer)
            

            # register the fuzzer into the db
            query = "INSERT INTO fuzzers VALUES ( '{}', '{}')".format(fuzzerName.split('.')[0], 1)

            try:
                res = DB_CONNECTION.execute(query)
            
                for i in res:
                    print i
            
                res = DB_CONNECTION.commit()
                
                print 'Commit', res

            except sqlite3.IntegrityError as e:
                print 'Fuzzer already inserted', e
                res = DB_CONNECTION.commit()
            


            # ack the client interface
            self.write("Fetched {} from {} size {} bytes<br>".format(fuzzerName, server, len(httpResponse.body))) 
            

        else:            
            print 'POST FuzzersHandler', uriFields
        

class UpdatesHandler(tornado.web.RequestHandler):
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*");



    # Return the version
    #
    # e.g.
    def get(self, uri):
        self.write( 'Core version number: 08/10/13' )
    
    # Parse the update package 
    #
    # e.g. http://172.20.30.31/updates/
    def post(self, uri):
        
        uriField = uri.split('/')
        
        print 'Got a update post', uri
        
        if uri == '':
            
            # stop running jobs before updates
            
            print 'Terminate jobs'
            jobsId = JOBS_MANAGER.getFuzzingJobs().keys()
            for j in jobsId:
                print '\t job', j
                JOBS_MANAGER.stopFuzzingJob(j)
                
            
            updateBat = base64.b64decode(self.request.body)
           
            home = os.getcwd()
            os.chdir('..')
            open('update.bat', 'w').write(updateBat)
            
            self.write('restarting host agent')
            self.finish()
            
            os.chdir(home)
            print 'finished update procedure'
            subprocess.Popen('update.bat')
            sys.exit(0)
            
            
        else:
            self.write('updates POST {}'.format(uri))                      



class ResultsHandler(tornado.web.RequestHandler):
    
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",  "*");
        #self.set_header("Access-Control-Allow-Methods", "DELETE, OPTIONS");
        
    
    def get(self, uri):
        
        uriFields = uri.split('/')
         
        if uri == '':
            
            # retrieve a summary of available results
            availableResults = []
            res = DB_CONNECTION.execute("SELECT fileName, fuzzer, bytesChanged, charsRendered, charsNotRendered, renderTime  FROM results ORDER BY fileName")
            
            for row in res:
                r = list(row)
                r[5] = str(r[5]).split('.')[0]
                availableResults.append(r)
            
            jsonizeMe = tornado.escape.json_encode( { 
                'results' : availableResults
            } )
            
            
            self.set_header('Content-Type', 'application/json')
            self.write(jsonizeMe)

        # request results after a given date
        # 
        # e.g. http://172.20.30.31/results/2013-09-04
        elif len(uriFields) == 1 and len( uriFields[0].split('-') ) == 3:
            
            date = uriFields[0].split('-')
            try:
                startFrom = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
                
                res = DB_CONNECTION.execute("SELECT fileName, fuzzer, bytesChanged, charsRendered, charsNotRendered, renderTime  FROM results WHERE renderTime >= ? ORDER BY fileName", (startFrom,) )
                
                availableResults = []
                for row in res:
                    r = list(row)
                    r[5] = str(r[5]).split('.')[0]
                    availableResults.append(r)
                
                jsonizeMe = tornado.escape.json_encode( { 
                    'results' : availableResults
                } )
                
                
                self.set_header('Content-Type', 'application/json')
                self.write(jsonizeMe)
            except ValueError as e:
                
                print '[E] ResultHandler', e
                self.set_header('Content-Type', 'application/json')
                self.write( tornado.escape.json_encode( { 'results' : 'Wrong Parameters' } ) )

            
        else:
            self.write('result GET {}'.format(uri))


'''
Not a good design, handles: 
- receive new servers
- notify server of agent aliveness 
- receive new fuzzing jobs
'''
class CommunicationHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",  "*");
        self.set_header("Access-Control-Allow-Methods", "DELETE, OPTIONS");

    def options(self,uri):
        pass

    
    @tornado.gen.coroutine   
    def delete(self, uri):


        uriFields = uri.split('/')
 
        # handle stop running jobs
        # 
        # e.g http://127.0.0.1/communication/jobs/12       
        if uriFields[0] == 'jobs' and len(uriFields) == 2:
            
            # fetch job id
            jobId = uriFields[1]
            
            #results = DB_CONNECTION.execute('SELECT * FROM jobs WHERE jobId == {}'.format(jobId))
            message = JOBS_MANAGER.stopFuzzingJob(jobId)
            self.write(message);
            

        else:
            print "DELETE ", uri


    @tornado.gen.coroutine       
    def get(self, uri):

        uriFields = uri.split('/')
        
        # server queries agent capabilities
        #
        # e.g. http://localhost/communication/capabilities
        if uriFields[0] == 'capabilities':
            
            # retrieve available fonts folders
            fontsFolder = os.path.join(os.path.dirname(__file__), 'fonts_extracted')

            availableFontsFolder = []

            for folder in os.listdir(fontsFolder):
                folder = os.path.join( fontsFolder, folder)
                if os.path.isdir( folder ):
                    availableFontsFolder.append( os.path.basename(folder))

                    

            # retrieve available fuzzers
            availableFuzzers = []
            query = "SELECT * FROM fuzzers"
            res = DB_CONNECTION.execute(query)
            
  
            for row in res:
                availableFuzzers.append(row[0])
            

            
            # send results back to server as a json object
            jsonizeMe = tornado.escape.json_encode( { 
                    'fontFolders' : availableFontsFolder,
                    'fuzzers' : availableFuzzers,
            } )

            self.set_header('Content-Type', 'application/json')
            self.write(jsonizeMe)

        # return the list of running jobs
        # 
        # e.g.
        elif uriFields[0] == 'jobs' and uriFields[1] == 'list':

            #{ 'id' : 1, 'fuzzer' : 'mock', 'folder' : 'asdf' },
            json = []
            jobs = JOBS_MANAGER.getFuzzingJobs()
            for j in jobs:
                json.append( { 'id' : j,
                               'fuzzer' : jobs[j][0],
                               'folder' : jobs[j][1] } ) 

            self.write(tornado.escape.json_encode(json) )

            
        else:
            self.write('GET {} - {}'.format( uri, uriFields) )



    @tornado.gen.coroutine        
    def post(self, uri):

        uriFields = uri.split('/')

        # add new server
        # 
        # e.g http://127.0.0.1/communication/servers/127.0.0.1
        if uriFields[0] == 'servers':
            self.set_header('Content-Type', 'text/plain')
       
            json = tornado.escape.json_decode(self.request.body)

            self.write('Server {}:{} added'.format(json['ip'], json['port']))
            
            try:
                query = "INSERT INTO server VALUES ('{}', '{}', 1 )".format( json['ip'], json['port'] )
                print query
                res = DB_CONNECTION.execute(query)

                for i in res:
                    print i
            
                res = DB_CONNECTION.commit()

                print 'Commit', res

            except sqlite3.IntegrityError as e:
                print 'Server already inserted', e
                DB_CONNECTION.commit()

        # start a fuzzing job
        #
        # e.g. 
        elif uriFields[0] == 'jobs' and len(uriFields) == 3:

            
            selectedFuzzer = uriFields[1]
            selectedFolder = uriFields[2]
            
            self.write("Starting job with fuzzer {} on folder {}".format(selectedFuzzer, selectedFolder))

            JOBS_MANAGER.startFuzzingJob(selectedFuzzer, selectedFolder)


        else:
            self.write('Communication post: {}'.format(uri))



class FuzzingJobsManager():

    def __init__(self, dbConnection, path='fuzzers_downloaded'):
        self.fuzzersPath = path
        self.jobsId = 0
        self.runningJobs = {}
        self.dbConnection = dbConnection
        self.jobsLock = threading.Lock()
      

    def getFuzzingJobs(self):
        return self.runningJobs
             
    '''
    Return an instance of 'moduleName' 
    '''
    def loadFuzzerModule(self, moduleName):
        
        # weird windows behaviour, use chdir
        home = os.getcwd()
        os.chdir(self.fuzzersPath)
        sys.path.append(os.getcwd())
        
        print os.getcwd(), ' - ', moduleName

        fp, pathname, description = imp.find_module( moduleName) 
        
        try:
            return imp.load_module( moduleName, fp, pathname, description)
        finally:

            # restore old wd
            os.chdir(home)

            if fp:
                fp.close()



    def addJob(self, fuzzerDescription, folder, fuzzer, queue):
        print 'addJob acquire'
        self.jobsLock.acquire()
        self.runningJobs[self.jobsId] = [fuzzerDescription, folder, fuzzer, queue]
        self.jobsId += 1
        self.jobsLock.release()
        print 'addJob release'

    def removeJob(self, jobId):
        print 'removeJob acquire'        
        self.jobsLock.acquire()
        self.runningJobs.pop(int(jobId))
        self.jobsLock.release()
        print 'removeJob release'


    def startFuzzingJob(self, fuzzer, folder):
        
        fuzzerModule = self.loadFuzzerModule(fuzzer)
        queue = Queue.Queue(maxsize=1)
        fuzzer = fuzzerModule.getFuzzerInstance(folder, queue)
        self.addJob(fuzzer.getDescription(), folder, fuzzer, queue)
        fuzzer.start()
        


    def stopFuzzingJob(self, jobId):

        try:
            jobId = int(jobId)
        except ValueError:
            return 'Wrong job number'

        if not jobId in self.runningJobs.keys() :
            return 'Wrong job number'
        else:
            self.runningJobs[jobId][2].stop()
            self.runningJobs[jobId][2].join()
            self.removeJob(jobId)
            return 'Job stopped'
            
        


def run():
    
    # connect to db
    global DB_CONNECTION
    DB_CONNECTION = sqlite3.connect(AGENT_DB, check_same_thread = False, timeout=1, detect_types=sqlite3.PARSE_DECLTYPES)

    # start fuzzing jobs manager
    global JOBS_MANAGER
    JOBS_MANAGER = FuzzingJobsManager(DB_CONNECTION)

    settings = {"static_path": os.path.join( os.path.dirname(__file__), "static"),}

    application = tornado.web.Application (
        #debug = True,
        handlers = [ (r'/', MainHandler),
                     (r'/dashboard/?(.*)', DashboardHandler),
                     (r'/fonts/?(.*)', FontsHandler),
                     (r'/fuzzers/?(.*)', FuzzersHandler),
                     (r'/results/?(.*)', ResultsHandler),
                     (r'/communication/?(.*)', CommunicationHandler),
                     (r'/updates/?(.*)', UpdatesHandler),
                     ],
        **settings )

    server = tornado.httpserver.HTTPServer(application)
    server.listen(80)
    tornado.ioloop.IOLoop.instance().start()      


def  agentSetup():
    
    # create database
    connection = sqlite3.connect(AGENT_DB, detect_types=sqlite3.PARSE_DECLTYPES)

    # server configuration                                                    
    connection.execute( '''CREATE TABLE server
                           (IP TEXT PRIMARY KEY NOT NULL,
                            PORT TEXT NOT NULL,
                            MASTER INT NOT NULL);
''')
    # fuzzers deployed
    connection.execute( '''CREATE TABLE fuzzers
                           (name TEXT PRIMARY KEY NOT NULL,
                            active INT NOT NULL); 
''')  # might need to add a path field
                                                    
    # jobs running
    connection.execute( '''CREATE TABLE jobs
                           ( jobId INTEGER PRIMARY KEY AUTOINCREMENT ,
                             fuzzer TEXT NOT NULL,
                             folder TEXT NOT NULL,
                             running INT NOT NULL) ;
''')


    # fuzzer results
    connection.execute('''CREATE TABLE results
                          ( md5 TEXT PRIMARY KEY,
                            bytesChanged INTEGER,
                            charsRendered INTEGER,
                            charsNotRendered INTEGER,
                            fuzzer TEXT,
                            fileName TEXT,
                            createTime TIMESTAMP,
                            renderTime TIMESTAMP ) ;
    ''')

    connection.close()


    # create directories for fonts and fuzzers downloaded
    try:
        os.mkdir('fonts_extracted')
        os.mkdir('fuzzers_downloaded')
    except OSError as e:
        print '[D]\t', e


if __name__ == '__main__':


    if len(sys.argv) == 2 and sys.argv[1] == 'setup':
        agentSetup()
    elif len(sys.argv) == 1:
        run()
