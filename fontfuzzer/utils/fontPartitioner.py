#!/usr/bin/env python

import os
import sys
import shutil


def moveFiles(srcFolderName, numberOfFonts, dstFolderName):

    print '[*] Trying to move {} fonts from {} to {}'.format( numberOfFonts, srcFolderName, dstFolderName)

    j = 0

    for f in os.listdir(srcFolderName):
        shutil.move( os.path.join(srcFolderName, f), os.path.join(dstFolderName, f) )
        
        if j == numberOfFonts:
            break
        
        j += 1



    print '[*] Moved {} fonts'.format(j)

    


if __name__ == '__main__':


    if len(sys.argv) != 5:
        print '[*] Usage ./{} sourceFolder numberOfFiles folderRootName numberOfFolders'.format(sys.argv[0])
        print '    Creates numberOfFolders folders, each containing numberOfFiles'
        exit(1)
    
    
    srcFolderName = sys.argv[1]
    numberOfFonts = int(sys.argv[2])
    dstFolderRoot = sys.argv[3]

    numberOfDirectories = int(sys.argv[4])


    for i in range(0, numberOfDirectories):
        
        dstFolderName = dstFolderRoot + '_' + str(i)
        os.mkdir(dstFolderRoot + '_' + str(i))
        moveFiles(srcFolderName, numberOfFonts, dstFolderName )





