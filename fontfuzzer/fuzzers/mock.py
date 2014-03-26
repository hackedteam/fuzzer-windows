import os
import time
import hashlib
import threading

'''
For fuzzing framework
'''
class MockFuzzer(threading.Thread):
    
    def __init__(self, fontsFolder):
        threading.Thread.__init__(self)
        self.fontsFolder = fontsFolder
        self.stopMe = False

   
    def run(self):


        while not self.stopMe:

            print '[*] Mock fuzzer - hashes the content of {} folder'.format(self.fontsFolder)

            for i in os.listdir(os.path.join('fonts_extracted', self.fontsFolder)):
                time.sleep(1)
                m = hashlib.md5()
                m.update(open( os.path.join('fonts_extracted', self.fontsFolder, i), "rb").read())
                print '[*]\t {} : {}'.format(i, m.hexdigest())

    def stop(self):
        self.stopMe = True        
        
    
    def getDescription(self):
        return 'Mock fuzzer'


def getFuzzerInstance(folder):
    return MockFuzzer(folder)
