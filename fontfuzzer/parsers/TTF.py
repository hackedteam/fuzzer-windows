import os
import sys
import math
import mmap
import random
import string
import logging
import subprocess

from struct import *


def getLogger():
    # logging settings
    logger = logging.getLogger('TTF')
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger


LOGGER = getLogger()




"""
N.B *DirectoryOffset is supposed to TableOffset instead..
"""


class TTFont():

    REQUIRED_TABLES = [ 'cmap',  'head', 'hhea', 'hmtx' ,
                        'maxp', 'name', 'post', 'OS/2'  ]

    TTF_TABLES = ['cvt ', 'fpgm', 'glyf', 'loca', 'prep']


    POSTSCRIPT_TABLES = ['CFF ', 'VORG']


    BITMAP_TABLES = ['EBDT', 'EBLC', 'EBSC', ]


    OPTIONAL_TABLES = [ 'gasp', 'hdmx', 'kern', 'LTSH', 
                        'PCLT', 'VDMX', 'vhea', 'vmtx' ]


    def __init__(self, filename, simpleParsing = False):
        font_handle = open(filename,'rb')
        self.filename = filename
        self.fontOffsetTable = FontOffsetTable(font_handle)
        self.fontOffsetTableLength = font_handle.tell()
        self.simpleParsing = simpleParsing # when a fuzzed font is parsed it might raise exceptions
                                  # simple parsing tries to parse only necessary stuff


        # k: tag => v: FontTableDirectory entry
        self.fontTableDirectories = {}

        # read all the tables
        for i in range(0, int(self.fontOffsetTable.numTables)):
            table  = FontTableDirectory(font_handle, self.fontTableDirectories)
            self.fontTableDirectories[table.tag] = table

        self.fontTableDirectoriesLength = font_handle.tell() - self.fontOffsetTableLength

        # calculate checksum
        for t in sorted( self.fontTableDirectories.keys() ):


            # checksum for 'head' table is different
            if( self.fontTableDirectories[t].tag == 'head' ):
                self.fontTableDirectories[t].doHeadChecksum(font_handle)
            else:
                self.fontTableDirectories[t].doChecksum(font_handle)


        # parse required font tables (for both ttf and otf)

        LOGGER.debug('[*] >> Parsing required tables <<')

        # HEAD
        LOGGER.debug('[*] Parsing table head')
        font_handle.seek(self.fontTableDirectories['head'].offset)
        self.fontTableDirectories['head'].table = HeadTable(font_handle)

        # MAXP
        LOGGER.debug('[*] Parsing table maxp')
        font_handle.seek(self.fontTableDirectories['maxp'].offset)
        self.fontTableDirectories['maxp'].table = MaxpTable(font_handle)

        # CMAP
        LOGGER.debug('[*] Parsing table cmap')
        # FIXME: handle is set within constructor, change it
        self.fontTableDirectories['cmap'].table = CmapTable(font_handle, self.fontTableDirectories['cmap'])

        # HHEA
        LOGGER.debug('parsing table hhea')
        font_handle.seek(self.fontTableDirectories['hhea'].offset)
        self.fontTableDirectories['hhea'].table = HheaTable(font_handle, self.fontTableDirectories['hhea'])

        # HMTX
        LOGGER.debug('parsing table hmtx')
        font_handle.seek(self.fontTableDirectories['hmtx'].offset)
        numberOfHMetrics = self.fontTableDirectories['hhea'].table.numberOfHMetrics
        numGlyphs = self.fontTableDirectories['maxp'].table.numGlyphs
        self.fontTableDirectories['hmtx'].table = HmtxTable(font_handle, self.fontTableDirectories['hmtx'], numberOfHMetrics, numGlyphs )


        # POST
        LOGGER.debug('parsing table post')
        font_handle.seek(self.fontTableDirectories['post'].offset)
        self.fontTableDirectories['post'].table = PostTable(font_handle)	

        # either ttf (glyf) or otf (cff)
        if 'glyf' in self.fontTableDirectories and not self.simpleParsing:

            # LOCA (required by GLYF)
            isLong = self.fontTableDirectories['head'].table.indexToLocFormat

            numberOfGlyphs = self.fontTableDirectories['maxp'].table.numGlyphs + 1
            nor = self.fontTableDirectories['loca'].length / 4 if isLong else self.fontTableDirectories['loca'].length / 2

            if nor != numberOfGlyphs:
                LOGGER.info('weird number of Glyphs: {} vs {}'.format(nor, numberOfGlyphs))

            LOGGER.debug( '[D] \t Number of glyphs {}'.format(numberOfGlyphs) )

            LOGGER.debug( '[*] Parsing loca table' )
            font_handle.seek(self.fontTableDirectories['loca'].offset)
            self.fontTableDirectories['loca'].table = LocaTable(font_handle, isLong, numberOfGlyphs)



            # GLYF

            # glyph font table is a list of glyph structures
            LOGGER.debug( '[*] Parsing table glyf' )

            self.fontTableDirectories['glyf'].table = []

            # must set the handle offset before calling the constructor
            startOffset = self.fontTableDirectories['glyf'].offset 
            endOffset   = self.fontTableDirectories['glyf'].length + startOffset


            # loca table contains the offsets of the glyphs relative to the
            # beginning of glyphData table

            font_handle.seek(startOffset)

            offsets = self.fontTableDirectories['loca'].table.offsets
            if len(offsets) != self.fontTableDirectories['maxp'].table.numGlyphs + 1:
                LOGGER.warn('Weird number of glyph offsets: loca {} vs maxp {}'.format(len(offsets), self.fontTableDirectories['maxp'].table.numGlyphs + 1) )



            for i in range(0, self.fontTableDirectories['maxp'].table.numGlyphs + 1):

                currentOffset = offsets[i]
                font_handle.seek(startOffset + currentOffset)

                #print '[*]\t {}: reading table at {}'.format( i, font_handle.tell() )
                self.fontTableDirectories['glyf'].table.append( GlyphTable(font_handle) )





        elif 'CFF ' in self.fontTableDirectories:

            # CFF
            LOGGER.debug( '[*] Parsing table CFF' )

            font_handle.seek(self.fontTableDirectories['CFF '].offset)
            self.fontTableDirectories['CFF '].table = CFFTable(font_handle)

        else:
            if not simpleParsing:
                raise Exception('Can\'t find glyf nor CFF table')


        LOGGER.debug( '[*] >> Finished parsing required tables <<' )
        LOGGER.debug( '[*] >> Parsing optional tables <<' )

        # parse non required tables
        for t in sorted( self.fontTableDirectories.keys() ):

            # CVT 
            if t == 'cvt ':
                LOGGER.debug( '[*] Parsing table CVT ' )
                font_handle.seek(self.fontTableDirectories['cvt '].offset)
                self.fontTableDirectories['cvt '].table = CVTTable(font_handle, self.fontTableDirectories['cvt '].length / 2 )   


            # prep
            if t == 'prep':
                LOGGER.debug( '[*] Parsing table prep' )
                font_handle.seek(self.fontTableDirectories['prep'].offset)
                self.fontTableDirectories['prep'].table = PrepTable(font_handle, self.fontTableDirectories['prep'].length)   

            if t == 'EBDT':
                LOGGER.debug( '[*] Parsing table EBDT' )
                font_handle.seek(self.fontTableDirectories['EBDT'].offset)
                self.fontTableDirectories['EBDT'].table = EBDTTable(font_handle)   


            if t == 'EBLC':
                LOGGER.debug( '[*] Parsing table EBLC' )
                font_handle.seek(self.fontTableDirectories['EBLC'].offset)
                self.fontTableDirectories['EBLC'].table = EBLCTable(font_handle)   



            if t == 'EBSC':
                LOGGER.debug( '[*] Parsing table EBSC' )
                font_handle.seek(self.fontTableDirectories['EBSC'].offset)
                self.fontTableDirectories['EBSC'].table = EBSCTable(font_handle)   



            if t == 'fpgm':
                LOGGER.debug( '[*] Parsing table fpgm' )
                font_handle.seek(self.fontTableDirectories['fpgm'].offset)
                self.fontTableDirectories['fpgm'].table = FpgmTable(font_handle, self.fontTableDirectories['fpgm'].length)   

            if t == 'kern':
                LOGGER.debug('parsing table kern')
                font_handle.seek(self.fontTableDirectories['kern'].offset)
                self.fontTableDirectories['kern'].table = KernTable(font_handle)   

            if t == 'name':
                LOGGER.debug('parsing table name')
                font_handle.seek(self.fontTableDirectories['name'].offset)
                self.fontTableDirectories['name'].table = NameTable(font_handle)   


            if t == 'OS/2':

                # Some fonts have this table truncated

                LOGGER.debug('parsing table OS/2')
                font_handle.seek(self.fontTableDirectories['OS/2'].offset)

                try:
                    self.fontTableDirectories['OS/2'].table = OS2Table(font_handle)   
                except error as e:
                    LOGGER.error('\tOS/2 error: {}'.format( e ))



        LOGGER.debug( '[*] >> Finished parsing optional tables <<' )



    def dump(self):

        self.fontOffsetTable.dump()


        for i in sorted(self.fontTableDirectories.keys()):
            self.fontTableDirectories[i].dump()






    '''
    Rebuild the font with newTagTable as the new table
    for tag 'tag'
    '''
    def rebuildFont(self, tag, newTagTable, originalFontBuffer):


        assert len(originalFontBuffer) % 4 == 0, 'File must be 4 byte aligned'
        assert len(newTagTable) % 4 == 0, 'New table must be 4 byte aligned'


        newFont = []

        # only the tables that start after the one we're updating
        # need to be moved
        tagStartOffset = self.fontTableDirectories[tag].offset

        directories = self.fontTableDirectories.copy()
        directories.pop(tag)

        dirToRebase = {}
        for d in directories:
            if tagStartOffset < directories[d].offset:
                dirToRebase[d] =  directories[d] 


        dirToPlainCopy = list( set( self.fontTableDirectories.keys() ) - set( dirToRebase.keys() ) - set([tag]) )

        LOGGER.debug('rebuilding font, new table for: {}'.format( tag) ) 
        LOGGER.debug('rebuilding font, copying tables: {}'.format( ', '.join(dirToPlainCopy)  ) )
        LOGGER.debug('rebuilding font, rebasing tables: {}'.format( ', '.join(dirToRebase.keys() ) ) )


        # 1] copy font offset table
        newFont =  originalFontBuffer[:self.fontOffsetTableLength]

        # 2] copy font table directories, we'll fix checkSum, offset, length later
        newFont += originalFontBuffer[self.fontOffsetTableLength:self.fontTableDirectoriesLength + self.fontOffsetTableLength]

        assert len(newFont) %4 == 0, 'WTF -5'

        # 3] copy the tables that don't need to be rebased


        # copy the tables in order
        offsetLength = {}
        for d in dirToPlainCopy:

            offset = self.fontTableDirectories[d].offset
            tmpLength = self.fontTableDirectories[d].length


            if (tmpLength % 4) !=0:
                tmpLength = tmpLength + ( 4 - tmpLength  % 4)


            offsetLength[offset] = tmpLength





        keys = sorted(offsetLength.keys())

        for k in keys:
            newFont += originalFontBuffer[k:offsetLength[k] + k]
            #print k, Utils.doBufferChecksum(originalFontBuffer[k:offsetLength[k] + k])

        assert len(newFont) %4 == 0, 'WTF -4'



        # 4] copy the new table
        newFont  += ''.join(newTagTable)

        assert len(newFont) %4 == 0, 'WTF -3'


        # fix checksum and length in the font table directory for new table tag
        checksumOffsetWithinFontDirectoryTable = self.fontTableDirectories[tag].fontDirectoryOffsetWithinTheFile + 4
        lengthOffsetWithinFontDirectoryTable = self.fontTableDirectories[tag].fontDirectoryOffsetWithinTheFile + 12

        newChecksum = hex(Utils.doBufferChecksum(''.join(newTagTable)) ).replace('0x', '').replace('L', '')

        # dbg
        while len(newChecksum) < 8:
            newChecksum = '0' + newChecksum

        newChecksum = [ pack('>B', int(newChecksum[i:i+2],16) ) for i in range(0, len(newChecksum), 2) ]

        oldLength = len(newFont)

        assert len(newFont) %4 == 0, 'WTF -2'


        # update checksum
        newFont = list(newFont[:checksumOffsetWithinFontDirectoryTable]) + \
            newChecksum + \
            list(newFont[checksumOffsetWithinFontDirectoryTable+4:])

        newFont = ''.join(newFont)

        assert  oldLength == len(newFont)

        # update length
        newLength = pack('>L', len(newTagTable) ) 

        newTableOldLength = unpack('>L', originalFontBuffer[lengthOffsetWithinFontDirectoryTable:lengthOffsetWithinFontDirectoryTable+4])[0]
        lengthDelta = len(newTagTable) - newTableOldLength 

        LOGGER.debug('rebuilding font, length delta: {}'.format( lengthDelta ))

        assert len(newFont) %4 == 0, 'WTF -1'

        newFont = newFont[:lengthOffsetWithinFontDirectoryTable] + \
            newLength + \
            newFont[lengthOffsetWithinFontDirectoryTable+4:]

        assert  oldLength == len(newFont)

        assert len(newFont) %4 == 0, 'WTF 0'

        # 5] rebase the remaining tables in order
        offsetLength = {}
        for d in dirToRebase:
            offset = self.fontTableDirectories[d].offset
            length = self.fontTableDirectories[d].length


            if (length % 4) !=0:
                length = length + ( 4 - length  % 4)


            offsetLength[offset] = length


        keys = sorted(offsetLength)


        assert len(newFont) %4 == 0, 'WTF 1'

        # a] copy tables
        for k in keys:

            newFont += originalFontBuffer[k:offsetLength[k] + k]

        assert len(newFont) %4 == 0, 'WTF 2'

        # b] update offsets field within font table directory
        for d in dirToRebase:
            offsetOffsetWithinFontDirectoryTable = self.fontTableDirectories[d].fontDirectoryOffsetWithinTheFile + 8

            newLength = lengthDelta + unpack('>L', originalFontBuffer[offsetOffsetWithinFontDirectoryTable:offsetOffsetWithinFontDirectoryTable+4])[0]
            newLength = pack('>L', newLength)

            oldLength = len(newFont)

            newFont = newFont[:offsetOffsetWithinFontDirectoryTable] + \
                newLength + \
                newFont[offsetOffsetWithinFontDirectoryTable+4:]

            assert oldLength == len(newFont)


        # 6] update head checksum
        headFontDirectoryTableOffset = self.fontTableDirectories['head'].fontDirectoryOffsetWithinTheFile
        headChecksumOffsetWithinFontDirectoryTable = headFontDirectoryTableOffset - 4

        oldLength = len(newFont)
        newFont = Utils.doBufferHeadChecksum(newFont, headFontDirectoryTableOffset)

        assert oldLength == len(newFont)


        return newFont


# Start fuzzing methods


    '''
    bit flip the glyfs 
    return fileInMemory, isFontFuzzed, numberOfBytesChanged
    '''
    def fuzzGlyfsBitFlipping(self):
        LOGGER.debug('GlyfsBitFlipping')
        glyfsTable = self.fontTableDirectories['glyf'].table
        LOGGER.debug('\tnumber of glyf to fuzz: {}'.format(len( glyfsTable )))
        
        offsets = {}
        for t in glyfsTable:
            offsets[t.positionWithinFile] = t.positionWithinFile + t.length

        LOGGER.debug('\tnumber of regions actually fuzzed: {}'.format( len( offsets.keys()) ) )
        
        fileInMemory = open(self.filename, 'rb').read()
                
        oldsize = len(fileInMemory)
        numberOfChanges = 0
       
        for i in offsets:
            replacement, numwrites = Utils.fuzzBufferBitFlipping(fileInMemory[i:offsets[i]], fuzzFactor=20, maxWrites=100 )
            assert len(replacement) != i - offsets[i], 'buffer size changed'
            fileInMemory = fileInMemory[:i] + replacement + fileInMemory[offsets[i]:]
            numberOfChanges += numwrites
                                                      
        return fileInMemory, True, numberOfChanges

    '''
    benfuzzer harness
    '''
    def fuzzBenStyle(self, table, fuzzFactor):
        fileInMemory = open(self.filename, 'rb').read()

        # fuzz table table
        tableDirTable  = self.fontTableDirectories[table]
        tableOffset = tableDirTable.offset
        tableLength = tableDirTable.length

        newtableTable, numberOfChanges = Utils.fuzzBufferBenFuzz(fileInMemory[tableOffset:tableOffset+tableLength], fuzzFactor)

        # only to test rebuildFont
        #newtableTable = fileInMemory[tableOffset:tableOffset+tableLength]
        #while (len(newtableTable) % 4) != 0:
        #    newtableTable += chr(0x0)

        assert len(fileInMemory) % 4 == 0, 'Fuzz Ben style issues'
        assert len(newtableTable) % 4 == 0, 'Fuzz Ben style issues'

        newFont = self.rebuildFont(table, newtableTable, fileInMemory)
        
        return newFont, True, numberOfChanges

    '''
    Loop through each table, whether its content
    is fuzzed or not is probabilistic
    '''
    def fuzzFullTablesPayload(self):
        pass


    def fuzzDirectoriesRadamsa(self):

        # read the whole file
        fileInMemory = open(self.filename, 'rb').read()

        # fuzz directories content
        fileMod = fileInMemory
        for i in sorted(self.fontTableDirectories.keys()):
            table = self.fontTableDirectories[i]


            if table.tag == 'glyf':
                LOGGER.INFO( '[*] Fuzzing directory {}'.format(table.tag) )
                fileMod = table.fuzzDirectory(fileMod)

                # update checksum
                fileMod = table.doFileBufferChecksum(fileMod)
                fileMod = table.doFileBufferHeadChecksum(fileMod)




        # write fuzzed font disk
        fname = 'testcases//' + \
            os.path.basename(self.filename).split('.ttf')[0] + \
            '-' + \
            ''.join( random.choice(string.ascii_lowercase + string.digits) for x in range(8) ) + \
            '.ttf'



        open(fname, 'wb').write(fileMod)


    


    def fuzzFontBytecode(self):

        # read the whole file
        fileInMemory = open(self.filename, 'rb').read()

        # fuzz bytecode within certain tables
        fileMod = fileInMemory

        # this font may not contain the table we want to fuzz, return true if we changed something
        # within the font
        isFontFuzzed = False

        for i in sorted(self.fontTableDirectories.keys()):
            table = self.fontTableDirectories[i]


            # fuzz the bytcode within each glyf
            if table.tag == 'glyf':
                LOGGER.INFO( '[*] Fuzzing bytecode found in directory {}'.format(table.tag) )

                # fetch offset, fuzz that buffer then join the whole file back
                LOGGER.INFO( table.offset, '-', table.length + table.offset )
                buffer = fileInMemory[table.offset:table.length + table.offset]

                buffer, numberOfBytesChanged = Utils.fuzzBufferBitFlipping(buffer)
                isFontFuzzed = True

                fileMod = fileInMemory[0:table.offset] + buffer + fileInMemory[table.length + table.offset:]
                #print len(fileInMemory), 'vs', len(fileMod)

                # update checksum
                fileMod = table.doFileBufferChecksum(fileMod)
                fileMod = table.doFileBufferHeadChecksum(fileMod)





        # write fuzzed font disk
        #fname = 'testcases//' + \
        #         os.path.basename(self.filename).split('.otf')[0] + \
        #        '-' + \
        #        ''.join( random.choice(string.ascii_lowercase + string.digits) for x in range(8) ) + \
        #        '.otf3'

        #open(fname, 'wb').write(fileMod)

        return fileMod, isFontFuzzed, numberOfBytesChanged



    def fuzzCffTableBitFlipping(self):

        assert 'CFF ' in self.fontTableDirectories, '[E] No CFF table found'

        # 1] read file in memory
        fileInMemory = list(open(self.filename, 'rb').read())

        # 2] flip some bytes within cff table range
        start = self.fontTableDirectories['CFF '].offset
        end   = start + self.fontTableDirectories['CFF '].length

        print '[D] CFF range is {} <-> {}'.format(start, end)

        FuzzFactor = random.random() * random.random() * 500
        numwrites = random.randrange( math.ceil( (float(end-start) / FuzzFactor) ) ) +1

        print 'Changing {} bytes out of {}'.format(numwrites, end-start)

        # bit flip
        for j in range(numwrites):
            rbyte = random.randrange(256)
            rn = random.randrange(end-start)
            fileInMemory[start+rn] = "%c"%(rbyte);

        fileInMemory = ''.join(fileInMemory)


        # 3] checksum cff table and head
        fileInMemory = self.fontTableDirectories['CFF '].doFileBufferChecksum(fileInMemory)

        # pure crap
        fileInMemory = self.fontTableDirectories['CFF '].doFileBufferHeadChecksum(fileInMemory)

        # 4] write to disk
        #fname = 'testcases//' + \
        #        os.path.basename(self.filename).split('.otf')[0] + \
        #        '-' + \
        #        ''.join( random.choice(string.ascii_lowercase + string.digits) for x in range(8) ) + \
        #'.ttf'

        #open(fname, 'wb').write(fileInMemory)
        return fileInMemory


    def fuzzDirectoriesBitFlipping(self):
        fileInMemory = list(open(self.filename, 'rb').read())

        FuzzFactor = random.random() * random.random() * 500
        numwrites = random.randrange( math.ceil( (float(len(fileInMemory)) / FuzzFactor) ) ) +1

        print 'Changing {} bytes out of {}'.format(numwrites, len(fileInMemory))

        # bit flip
        for j in range(numwrites):
            rbyte = random.randrange(256)
            rn = random.randrange(len(fileInMemory))
            fileInMemory[rn] = "%c"%(rbyte);


        fileInMemory = ''.join(fileInMemory)

        # update checksums
        for i in sorted(self.fontTableDirectories.keys()):
            table = self.fontTableDirectories[i]

            fileInMemory = table.doFileBufferChecksum(fileInMemory)

        # table ?!
        fileInMemory = table.doFileBufferHeadChecksum(fileInMemory)


        # write file to disk
        fname = 'testcases//' + \
            os.path.basename(self.filename).split('.ttf')[0] + \
            '-' + \
            ''.join( random.choice(string.ascii_lowercase + string.digits) for x in range(8) ) + \
            '.ttf'

        open(fname, 'wb').write(fileInMemory)



# End fuzzing methods

"""
FIXED	32bit signed fixed-point number 16.16

"""

class FontOffsetTable():

    def __init__(self, handle):

        # sfnt stands for spline font
        self.SFNT_Version = handle.read(4)
        self.numTables = unpack(">H", handle.read(2) )[0]
        self.searchRange = handle.read(2)
        self.entrySelector = handle.read(2)
        self.rangeShift = handle.read(2)

    def dump(self):

        print 'FontOffsetTable:'
        print '\tSFNT_Version\t {}'.format( unpack(">i", self.SFNT_Version )[0] )
        print '\tnumTables\t {}'.format(  self.numTables )
        print '\tsearchRange\t {}'.format( unpack(">H", self.searchRange)[0] )
        print '\tentrySelector\t {}'.format( unpack(">H", self.entrySelector)[0] )
        print '\trangeShift\t {}'.format( unpack(">H", self.rangeShift)[0] )


# TODO: redesign this class
class FontTableDirectory():

    def __init__(self, handle, fontTableDirectories):

        self.fontDirectoryOffsetWithinTheFile = handle.tell()

        self.tag = handle.read(4)
        self.checksum = unpack('>L', handle.read(4))[0]
        self.offset = unpack('>L', handle.read(4) )[0]
        self.length = unpack('>L', handle.read(4) )[0]

        # the FontTable object this directory element points to
        self.table = None

        # awful abstraction
        self.fontTableDirectories = fontTableDirectories

    """
    fuzzDirectory changes the payload of the directory, keeping the
    same offset and length, but updating the checksum
    """
    def fuzzDirectory(self, fileInMemory):

        assert self.table != None, '[E] No table for this directory'

        # a] write the table to file, then fuzz it
        file_name = 'tmp_table'
        t = open(file_name, 'wb')

        data = fileInMemory[self.offset:self.offset+self.length]

        assert len(data) == self.length, "Couldn't read enough bytes"

        t.write(data)

        t.close()

        output = subprocess.check_output(['radamsa-0.3.exe', file_name])[:len(data)]

        # pad with 0xf atm
        while len(output) < len(data):
            output += pack('>b', 0xf)


        final_data = fileInMemory[0:self.offset] + output + fileInMemory[self.offset+self.length:]

        assert len(final_data) == len(fileInMemory)

        return final_data 


    def doChecksum(self, handle):
        total_data = 0

        handle.seek(self.offset)

        # round length
        checksumLength = (self.length + 3 ) & ~3

        #print 'Reading for {} bytes rather than {}'.format(checksumLength, self.length)

        table = handle.read(checksumLength)
        #print 'Read {} bytes from table {}'.format(len(table), self.tag)

        for i in range(0, len(table), 4):
            data = unpack('>I', table[i:i+4] ) [0]
            total_data += data

        final_data = 0xffffffff & total_data

        if final_data != self.checksum:
            LOGGER.debug( '\n\tChecksum error, calculated: {} - read: {}'.format(final_data, self.checksum) )

        LOGGER.debug( '[*]\t checksum: {}'.format(final_data) )

        return final_data


    def doFileBufferChecksum(self, fileInMemory):
        total_data = 0

        # round length
        checksumLength = (self.length + 3 ) & ~3

        table = fileInMemory[self.offset:self.offset+checksumLength]

        for i in range(0, len(table), 4):
            data = unpack('>I', table[i:i+4] ) [0]
            total_data += data

        new_checksum = 0xffffffff & total_data

        print '[*]\t New checksum {}'.format(new_checksum)

        # update the buffer
        newFileInMemory = fileInMemory[0:self.fontDirectoryOffsetWithinTheFile + 4] +  pack('>L', new_checksum) + \
            fileInMemory[self.fontDirectoryOffsetWithinTheFile + 8:]

        assert len(newFileInMemory) == len(fileInMemory)

        return newFileInMemory




    # TODO: wrong class for this function 
    def doFileBufferHeadChecksum(self, fileInMemory):

        # these var names are actually inverted..
        headDirectoryOffsetWithinTheFile = self.fontTableDirectories['head'].fontDirectoryOffsetWithinTheFile
        headTableOffset = self.fontTableDirectories['head'].offset

        LOGGER.debug( '[D] Head headDirectoryOffsetWithinTheFile {} - headTableOffset {}'.format(headDirectoryOffsetWithinTheFile, headTableOffset) )

        total_data = 0

        # round length
        checksumLength = (self.fontTableDirectories['head'].length + 3 ) & ~3

        # set checkSumAdjustement to 0 in the read buffer
        fileInMemory = fileInMemory[:headTableOffset + 8] + pack('>I', 0 ) + \
            fileInMemory[headTableOffset  + 12:]

        table = fileInMemory[headTableOffset:headTableOffset+checksumLength]

        LOGGER.debug( '[D] table size {}'.format(len(table)) )

        for i in range(0, len(table), 4):
            if i == 8:    # actually useless
                data = 0  # set checkSumAdjustement to 0 in the read buffer
                checkSumAdjustement = unpack('>I', table[i:i+4] ) [0]
            else:
                data = unpack('>I', table[i:i+4] ) [0]

            total_data += data

        headTableChecksum = 0xffffffff & total_data

        # head table checksum done, update checksum field in memory
        newFileInMemory = fileInMemory[0:headDirectoryOffsetWithinTheFile + 4] +  pack('>L', headTableChecksum) + \
            fileInMemory[headDirectoryOffsetWithinTheFile + 8:]

        LOGGER.debug( '[D] head table checksum {} @ {}'.format(headTableChecksum, headDirectoryOffsetWithinTheFile + 4) )

        # now, calculate entire font checksum
        total_data = 0

        # calculate new checkSumAdjustement value
        for i in range(0, len(newFileInMemory), 4):
            data = unpack('>I', newFileInMemory[i:i+4])[0]
            total_data += data

        newCheckSumAdjustement = total_data & 0xffffffff 
        newCheckSumAdjustement = (0xb1b0afba - newCheckSumAdjustement ) & 0xffffffff 

        LOGGER.debug( '[D] head newCheckSumAdjustement {}'.format(newCheckSumAdjustement) )


        # update
        newFileInMemory = newFileInMemory[:headTableOffset + 8] + pack('>I',newCheckSumAdjustement ) + \
            newFileInMemory[headTableOffset  + 12:]


        LOGGER.debug( '[D] updating newCheckSumAdjustement {} @ {}'.format(newCheckSumAdjustement, headTableOffset + 8 ) )


        return newFileInMemory




    def doHeadChecksum(self, handle):
        """
        To calculate the checkSum for the 'head' table which itself includes the checkSumAdjustment entry for the entire font, do the following:

        1] Set the checkSumAdjustment to 0.
        2] Calculate the checksum for all the tables including the 'head' table and enter that value into the table directory.
        3] Calculate the checksum for the entire font.
        4] Subtract that value from the hex value B1B0AFBA.
        5] Store the result in checkSumAdjustment.

        The checkSum for the head table which includes the checkSumAdjustment entry for the entire font is now incorrect.
        That is not a problem. Do not change it. An application attempting to verify that the 'head' table has not changed 
        should calculate the checkSum for that table by not including the checkSumAdjustment value, and compare the result 
        with the entry in the table directory. 
        """

        assert self.tag == 'head', 'Trying to calculate the head checksum for a non-head table'

        total_data = 0

        handle.seek(self.offset)

        # round length
        checksumLength = (self.length + 3 ) & ~3


        table = handle.read(checksumLength)


        for i in range(0, len(table), 4):
            if i == 8:
                data = 0
                checkSumAdjustement = unpack('>I', table[i:i+4] ) [0]
            else:
                data = unpack('>I', table[i:i+4] ) [0]

            total_data += data

        final_data = 0xffffffff & total_data

        if final_data != self.checksum:
            LOGGER.debug( 'checksum error, calculated: {} - read: {}'.format(final_data, self.checksum) )

        # head table checksum done
        LOGGER.debug( '[*]\t checksum: {}'.format(final_data) )



        # now, calculate entire font checksum
        handle.seek(0,2)
        end_of_file = handle.tell()

        handle.seek(0)

        total_data = 0
        font = handle.read(end_of_file)

        # set checkSumAdjustement to 0 in the read buffer
        font = font[:self.offset + 8] + pack('>I', 0) + font[self.offset + 12:]


        #print 'Read {} bytes for checkSumAdjustement'.format(len(font))

        for i in range(0, len(font), 4):
            data = unpack('>I', font[i:i+4] ) [0]
            total_data += data

        final_data =  total_data & 0xffffffff 

        final_data =  (0xb1b0afba - final_data) & 0xffffffff 

        if final_data != checkSumAdjustement:
            LOGGER.debug( 'checkSumAdjustement error, calculated {} - read: {}'.format(final_data, checkSumAdjustement ) )


        return final_data


    def dump(self, index=''):

        print 'FontTableDirectory {}'.format(index)
        print '\ttag\t {}'.format(self.tag)
        print '\tchecksum {}'.format(self.checksum)
        print '\toffset\t {}'.format(self.offset)
        print '\tlength\t {}'.format(self.length)


"""
Superclass for all the tables
"""
class FontTable():
    pass



class CFFTable(FontTable):

    def __init__(self, handle):

        # 1 header
        self.headerMajor    = unpack('>B', handle.read(1))[0]
        self.headerMinor    = unpack('>B', handle.read(1))[0]
        self.headerHdrSize  = unpack('>B', handle.read(1))[0]

        # The offSize field specifies the size of all offsets(0) relative to the
        # start of CFF data
        self.headerOffSize  = unpack('>B', handle.read(1))[0]


        '''
        This contains the PostScript language names (FontName or
        CIDFontName) of all the fonts in the FontSet

        For compatibility with client software, such as PostScript
        interpreters and Acrobat , font names should be no longer
        than 127 characters and should not contain any of the following
        ASCII characters: [, ], (, ), {, }, <, >, /, %, null (NUL), space, tab,
        carriage return, line feed, form feed. It is recommended that
        font names be restricted to the printable ASCII subset, codes 33
        through 126. Adobe Type Manager  software imposes a further restriction on the font
        name length of 63 characters
        '''

        # 2
        self.name = self.Index(handle)

        for n in self.name.data:
            print '[D] \tPS name: {}'.format(n)

        '''
        top-level DICTs of all the fonts in the FontSet
        stored in an INDEX structure.

        Objects contained within this INDEX correspond to those 
        in the Name INDEX in both order and number. Each object 
        is a DICT structure that corresponds to
        the top-level dictionary of a PostScript font.
        A font is identified by an entry in the Name INDEX and its data
        is accessed via the corresponding Top DICT
        '''

        # 3
        self.topDictIndex = self.Index(handle)


        # 4
        self.stringIndex = self.Index(handle)

        for n in self.stringIndex.data:
            print '[D] \tString name: {}'.format(n)


        # 5 Global Subr INDEX


    class Dict():


        def __init__(self, handle):
            pass


    class Index():

        def __init__(self, handle):

            self.count          = unpack('>H', handle.read(2))[0]
            #print 'Count {}'.format(self.count)

            self.offSize        = unpack('>B', handle.read(1))[0]
            #print 'offSize {}'.format(self.offSize)

            self.offsetArray = []

            for i in range(0, self.count + 1):

                if self.offSize == 1:
                    self.offsetArray.append( unpack('>B', handle.read(1))[0])

                elif self.offSize == 2:
                    self.offsetArray.append( unpack('>H', handle.read(2))[0])         

                elif self.offSize == 3:
                    raise Exception('TODO: unpack 3 bytes')

                elif self.offSize == 4:
                    self.offsetArray.append( unpack('>I', handle.read(4))[0])

                else:
                    raise Exception('Invalid offSize')

            # Offsets in the offset array are relative to the byte that precedes
            # the object data
            self.startOffset    = handle.tell() - 1

            # read elements
            self.data = []

            for i in range(0, self.count):

                # seek to the correct offset, i.e. start of index struct + offsetArray[i]
                handle.seek(self.startOffset + self.offsetArray[i])
                size = self.offsetArray[i+1] - self.offsetArray[i]

                self.data.append( handle.read(size) )

            # seek handle to the end of the index
            first = handle.tell()
            handle.seek( self.offsetArray[len(self.offsetArray)-1] + self.startOffset )
            assert handle.tell() == first, 'offsets screwed'




class FpgmTable(FontTable):

    def __init__(self, handle, numberOfInstructions):
        self.instructions = []
        for i in range(0, numberOfInstructions):
            self.instructions.append( unpack('>B', handle.read(1))[0])





"""
Collection of bitmap data, according
to info of EBLC table
"""
class EBDTTable(FontTable):

    def __init__(self, handle):
        self.version = unpack('>l', handle.read(4))[0]
        assert self.version == 0x20000, '[E] Wrong version for EBDT table: {}'.format(self.version)


"""
Embedded bitmap locators
"""
class EBLCTable(FontTable):

    def __init__(self, handle):
        self.version    = unpack('>l', handle.read(4))[0]
        assert self.version == 0x20000, '[E] Wrong version for EBLC table: {}'.format(self.version)
        self.numSizes   = unpack('>L', handle.read(4))[0]

        self.bitmapSizeTables = []


    class BitmapSizeTable():

        def __init__(self, handle):
            self.indexSubTableArrayOffset = unpack('>L', handle.read(4))[0]
            self.indexTablesSize          = unpack('>L', handle.read(4))[0]
            self.numberOfIndexSubTables   = unpack('>L', handle.read(4))[0]
            self.colorRef                 = unpack('>L', handle.read(4))[0]

            self.hori                     = SbitLineMetrics(handle)
            self.vert                     = SbitLineMetrics(handle)

            self.startGlyphIndex          = unpack('>W', handle.read(2))[0]
            self.endGlyphIndex            = unpack('>W', handle.read(2))[0]

            self.ppemX                    = unpack('>B', handle.read(1))[0]
            self.ppemY                    = unpack('>B', handle.read(1))[0]
            self.bitDepth                 = unpack('>B', handle.read(1))[0]
            self.flags                    = unpack('>B', handle.read(1))[0]




class EBSCTable(FontTable):


    def __init__(self):
        self.version    = unpack('>l', handle.read(4))[0]
        assert self.version == 0x20000, '[E] Wrong version for EBLC table: {}'.format(self.version)
        self.numSizes   = unpack('>L', handle.read(4))[0]

        self.bitmapScaleTable = []
        for i in range(0, self.numSizes):
            self.bitmapScaleTable.append( BitmapScaleTable(handle) )


    class BitmapScaleTable():

        def __init__(self, handle):
            self.hori           = SbitLineMetrics(handle)
            self.vert           = SbitLineMetrics(handle)

            self.ppemX          = unpack(handle.read('>B', handle.read(1) ) )[0]         
            self.ppemY          = unpack(handle.read('>B', handle.read(1) ) )[0]
            self.substitutePpemX          = unpack(handle.read('>B', handle.read(1) ) )[0]
            self.substitutePpemY          = unpack(handle.read('>B', handle.read(1) ) )[0]




class SbitLineMetrics():

    def __init__(self):
        self.ascender = unpack('>b', handle.read(1))[0]
        self.descender = unpack('>b', handle.read(1))[0]
        self.widthMax = unpack('>B', handle.read(1))[0]

        self.caretSlopeNumerator = unpack('>b', handle.read(1))[0]
        self.caretSlopeDenominator = unpack('>b', handle.read(1))[0]

        self.caretOffset = unpack('>b', handle.read(1))[0]
        self.minOriginSB = unpack('>b', handle.read(1))[0]
        self.minAdvancedSB = unpack('>b', handle.read(1))[0]
        self.maxBeforeBL = unpack('>b', handle.read(1))[0]
        self.minAfterBL = unpack('>b', handle.read(1))[0]
        self.pad1 = unpack('>b', handle.read(1))[0]
        self.pad2 = unpack('>b', handle.read(1))[0]


"""
provides a mechanism for describing embedded bitmaps
which are created by scaling other embedded bitmaps

"""



"""
Index to Location
"""
class LocaTable(FontTable):

    """
    Offsets are relative to the beginning of the glyphData.
    In order to compute the length of the last glyph element, 
    there is an extra entry after the last valid index.

    Index zero is the missing character
    """
    def __init__(self, handle, isLong, numberOfRecords):

        # 0 for short offsets, 1 for long
        self.isLong = isLong

        self.offsets = []

        if self.isLong:
            for i in range(0, numberOfRecords):
                self.offsets.append( unpack('>L', handle.read(4) ) [0] )
        else:
            for i in range(0, numberOfRecords):
                self.offsets.append( unpack('>H', handle.read(2) ) [0] * 2 )



    def fuzz(self):
        # WTF: screw indexes
        pass


"""
List of values that can be referenced by instructions
"""
class CVTTable(FontTable):

    def __init__(self, handle, numberOfElements):

        self.values = []
        for i in range(0, numberOfElements):
            self.values.append( unpack('>h', handle.read(2) ) )




"""
Set of TrueType instructions that will be executed 
whenever the font or point size or transformation matrix 
change and before each glyph is interpreted
"""
class PrepTable(FontTable):

    def __init__(self, handle, numberOfInstructions):
        self.instructions = []

        for i in range(0, numberOfInstructions):
            self.instructions.append(unpack('>B', handle.read(1)))


    def fuzz(self):
        pass


class MaxpTable(FontTable):

    def __init__(self, handle):

        self.tableVersionNumber = unpack('>l', handle.read(4) )[0]
        self.numGlyphs          = unpack('>H', handle.read(2) )[0]
        self.maxPoints          = unpack('>H', handle.read(2) )[0]
        self.maxContours        = unpack('>H', handle.read(2) )[0]
        self.maxCompositePoints = unpack('>H', handle.read(2) )[0]
        self.maxCompositeContours = unpack('>H', handle.read(2) )[0]
        self.maxZones           = unpack('>H', handle.read(2) )[0]
        self.maxTwilightPoints  = unpack('>H', handle.read(2) )[0]
        self.maxStorage         = unpack('>H', handle.read(2) )[0]
        self.maxFunctionDefs    = unpack('>H', handle.read(2) )[0]
        self.maxInstructionDefs = unpack('>H', handle.read(2) )[0]
        self.maxStackElements   = unpack('>H', handle.read(2) )[0]
        self.maxSizeOfInstructions = unpack('>H', handle.read(2) )[0]
        self.maxComponentElements  = unpack('>H', handle.read(2) )[0]
        self.maxComponentDepth     = unpack('>H', handle.read(2) )[0]


    def fuzze(self):
        #WTF: fuzz all the values
        pass

class HeadTable(FontTable):

    def __init__(self, handle):

        self.tableVersionNumber = unpack('>l', handle.read(4) )[0]
        self.fontRevision       = unpack('>l', handle.read(4) )[0]
        self.checkSumAdjustement= unpack('>L', handle.read(4) )[0]
        self.magicNumber        = unpack('>L', handle.read(4) )[0]
        self.flags              = unpack('>H', handle.read(2) )[0]
        self.unitsPerEm         = unpack('>H', handle.read(2) )[0]
        self.created            = unpack('>Q', handle.read(8) )[0]
        self.modified           = unpack('>Q', handle.read(8) )[0]
        self.xMin               = unpack('>h', handle.read(2) )[0]
        self.yMin               = unpack('>h', handle.read(2) )[0]
        self.xMax               = unpack('>h', handle.read(2) )[0]
        self.yMax               = unpack('>h', handle.read(2) )[0]
        self.macStyle           = unpack('>H', handle.read(2) )[0]
        self.lowestRecPPEM      = unpack('>H', handle.read(2) )[0]
        self.fontDirectionHint  = unpack('>h', handle.read(2) )[0]
        self.indexToLocFormat   = unpack('>h', handle.read(2) )[0]
        self.glyphDataFormat    = unpack('>h', handle.read(2) )[0]

    def fuzz(self):
        pass
        # WTF:
        # screw flags value
        # unitsPerEm range is 16-16384



"""
caller must set the handle offset before
"""
class GlyphTable(FontTable):

    def __init__(self, handle):


        self.positionWithinFile = handle.tell()
        
        # FOLLOWING CODE when called on fuzzed samples (i.e. native_glyf.shortNameMine) gives
        # exceptions obviously
        self.header = self.GlyphTableHeader(handle)


        # if a glyph has zero contours, it need not have any glyph data
        # should happen only with the last 'fake' glyph
        if self.header.numberOfCountours == 0: 
            #print '[*] \t\t last'
            self.glyph = None
        elif self.header.numberOfCountours < 0:
            #print '[*] \t\t composite'
            self.glyph = self.CompositeGlyph(handle, self.header)
        else:
            #print '[*] \t\t simple'
            self.glyph = self.SimpleGlyph(handle, self.header)


        self.length = handle.tell() - self.positionWithinFile

    """
    Fuzz bytecode of the glyph table, return a buffer with the fuzzed table
    """
    def fuzzBytecode(self, fileInMemory):

        print '[DD] Start fuzz GLYPH'

        if self.glyph.bytecodeStartFileOffset is None or self.glyph.bytecodeEndFileOffset is None:
            #print '[D] \t Found no bytecode'
            return fileInMemory


        # find bytecode offset within font file
        startOffset = self.glyph.bytecodeStartFileOffset
        endOffset = self.glyph.bytecodeEndFileOffset


        print '[D] \t fuzzing between offsets {} and {}'.format(startOffset, endOffset)



        data = fileInMemory[startOffset:endOffset]
        assert len(data) == endOffset - startOffset, "Couldn't read enough bytes"


        radamsa = False
        if radamsa:
            # write the table to file, then fuzz it
            file_name = 'tmp_table'
            t = open(file_name, 'wb')
            t.write(data)
            t.close()
            output = subprocess.check_output(['radamsa-0.3.exe', file_name])[:len(data)]


            # pad with 0xf atm
            while len(output) < len(data):
                output += pack('>b', 0xf)

        else:

            output = []
            l = len(data)
            i = 0

            byteCopied = 0
            byteRandom = 0

            while i < l:

                if (random.randrange(256) % 3) == 0 and bool(random.getrandbits(1)) :

                    # copy a random chunk of bytes from existing buffer into randomized one
                    t = random.randrange(l-i)
                    for j in range(0, t):
                        output.append( data[i+j] )

                    i+=t
                    byteCopied += t

                else:
                    e = pack('>B', random.randrange(256) )
                    output.append( e  )

                    i+=1
                    byteRandom += 1

            assert len(data) == byteRandom + byteCopied
            print '[D] \t bytecode size {} - random {} copied {}'.format(len(data), byteRandom, byteCopied)

            assert len(data) == len(output), 'data: {} output: {}'.format(len(data), len(output))
            output = ''.join(output)






        final_data = fileInMemory[0:startOffset] + output + fileInMemory[endOffset:]

        assert len(final_data) == len(fileInMemory)

        print '[DD] Return fuzz glyph'

        return final_data




    class GlyphTableHeader():

        def __init__(self, handle):

            # if negative -> composite glyph
            # if >=0      -> single glyph
            self.numberOfCountours      = unpack('>h', handle.read(2) )[0]
            
            LOGGER.debug('\tnumber of countour: {}'.format(self.numberOfCountours))

            # glyph's bounding box
            self.xMin                   = unpack('>h', handle.read(2) )[0]
            self.yMin                   = unpack('>h', handle.read(2) )[0]
            self.xMax                   = unpack('>h', handle.read(2) )[0]
            self.yMax                   = unpack('>h', handle.read(2) )[0]
            
            LOGGER.debug('\tglyph box: ({},{}) ({},{})'.format(self.xMin, self.yMin, self.xMax, self.yMax))
                                                               


    class CompositeGlyph():


        # a composite glyph is apparently composed by
        # some components and instructions
        def __init__(self, handle, header):

            self.bytecodeStartFileOffset = None
            self.bytecodeEndFileOffset   = None 


            self.components = []
            while True:
                component = self.CompositeGlyphComponent(handle)
                
                self.components.append( component )

                if not component.moreComponents():
                    # Following the last component are
                    # instructions for the composite
                    # character

                    if component.weHaveInstructions():
                        self.numInstr = unpack('>H', handle.read(2) )[0]

                        LOGGER.debug('[D]\tnumber of instruction {}'.format(self.numInstr))

                        if self.numInstr > 0:
                            self.bytecodeStartFileOffset = handle.tell()

                        self.instr = []
                        try:
                            for i in range(0, self.numInstr):
                                self.instr.append( unpack('>b', handle.read(1) ) [0] )

                        except Exception as e:
                            LOGGER.error( '[E]\tProbably read a wrong instruction number: {}'.format(e) )
                            print handle.tell()

                        if self.numInstr > 0:
                            self.bytecodeEndFileOffset = handle.tell()


                        break




        class CompositeGlyphComponent():

            def __init__(self, handle):
                self.flags          = unpack( '>H', handle.read(2) )[0]

                # index of the first contour
                self.glyphIndex     = unpack( '>H', handle.read(2) )[0]

                # data varies according to flags, see page 69
                if self.arg1And2AreWords():
                    self.argument1  = unpack('>h', handle.read(2) )[0]
                    self.argument2  = unpack('>h', handle.read(2) )[0]
                else:
                    # ( arg1 << 8 ) | arg2
                    self.arg1and2   = unpack('>H', handle.read(2) )[0] 

                if self.weHaveAScale():
                    self.scale      = unpack('>h', handle.read(2) )[0]

                elif self.weHaveAnXAndYScale():
                    self.xscale      = unpack('>h', handle.read(2) )[0]
                    self.yscale      = unpack('>h', handle.read(2) )[0]

                elif self.weHaveATwoByTwo():
                    self.xscale      = unpack('>h', handle.read(2) )[0]
                    self.scale01     = unpack('>h', handle.read(2) )[0]
                    self.scale10     = unpack('>h', handle.read(2) )[0]
                    self.yscale      = unpack('>h', handle.read(2) )[0]


            """
            If this is set, the arguments are words;
            otherwise, they are bytes
            """
            def arg1And2AreWords(self):
                return (self.flags & 1) != 0 


            """
            If this is set, the arguments are xy
            values; otherwise, they are points
            """
            def argsAreXYValues(self):
                return (self.flags & 2) != 0 

            """
            For the xy values if the preceding is
            true
            """
            def roundXYToGrid(self):
                return (self.flags & 4) != 0 

            """
            This indicates that there is a simple
            scale for the component. Otherwise,
            scale = 1.0
            """
            def weHaveAScale(self):
                return (self.flags & 8) != 0  


            """
            Indicates at least one more glyph after
            this one
            """
            def moreComponents(self):
                return (self.flags & 32) != 0  

            """
            The x direction will use a different
            scale from the y direction
            """
            def weHaveAnXAndYScale(self):
                return (self.flags & 64) != 0  


            """
            There is a 2 by 2 transformation that
            will be used to scale the component
            """
            def weHaveATwoByTwo(self):
                return (self.flags & 128) != 0 


            """
            Following the last component are
            instructions for the composite character
            """
            def weHaveInstructions(self):
                return (self.flags & 256) != 0

            """
            If set, this forces the aw and lsb (and rsb)
            for the composite to be equal to those from this original glyph. This
            works for hinted and unhinted characters
            """
            def useMyMetrics(self):
                return (self.flags & 512) != 0




    class SimpleGlyph():

        def __init__(self, handle, header):
            self.endPtsOfCountour = []
            for i in range(0, header.numberOfCountours):
                self.endPtsOfCountour.append( unpack('>H', handle.read(2))[0] )
            #    LOGGER.debug('\tend of countours: {}'.format(self.endPtsOfCountour[-1]) )

            

            # total number of bytes for instructions
            self.instructionLength = unpack('>H', handle.read(2))[0]

            self.bytecodeStartFileOffset = None
            self.bytecodeEndFileOffset   = None 

            if self.instructionLength > 0:
                self.bytecodeStartFileOffset = handle.tell()


            self.instructions = []

            for i in range(0, self.instructionLength):
                self.instructions.append( unpack('>B', handle.read(1) ) [0] )


            if len(self.instructions) > 0:
                self.bytecodeEndFileOffset = handle.tell()
                LOGGER.debug('\tnumber of instructions: {}'.format(len(self.instructions)))    
            

            # array of flags for each coordinate in outline
            self.glyphFlags = []
            initialNumberOfFlag = self.endPtsOfCountour[-1] + 1
            
            i = 0
            while i < initialNumberOfFlag:
                flags = GlyphTable.GlyphFlags(handle)

                # If set, the next byte specifies the number of additional
                # times this set of flags is to be repeated. In this way,
                # the number of flags listed can be smaller than the
                # number of points in a character.
                if flags.isRepeatSet():
                    LOGGER.debug('\trepeat {}'.format( flags.numberOfRepetition) )
                    i += flags.numberOfRepetition
                    
                self.glyphFlags.append( flags )
            
            #LOGGER.debug('\tnumber of coordinates: {} '.format(len(self.glyphFlags)))

           

            self.xCoordinates = []
            for i in range(0, len(self.glyphFlags) ):

                if self.glyphFlags[i].isXshortVectorSet():
                    self.xCoordinates.append( unpack('>B', handle.read(1)) [0] )
                else:
                    self.xCoordinates.append( unpack('>h', handle.read(2)) [0] )
                    
            self.yCoordinates = []
            for i in range(0, len(self.glyphFlags) ):

                if self.glyphFlags[i].isYshortVectorSet():
                    self.yCoordinates.append( unpack('>B', handle.read(1)) [0] )
                else:
                    self.yCoordinates.append( unpack('>h', handle.read(2)) [0] )



            #for i in range(0, len(self.glyphFlags) ):
            #    LOGGER.debug('\tcoords delta: ({}, {})'.format(self.xCoordinates[i], self.yCoordinates[i]))


    class GlyphFlags():

        def __init__(self, handle):

            self.flagAsByte = unpack('>B', handle.read(1) )[0]

            # if repeat is set the next byte is the number of repetition
            if self.isRepeatSet() == 1:
                self.numberOfRepetition = unpack('>B', handle.read(1) )[0]

        def numberOfRepetition(self):
            return self.numberOfRepetition

        

        def isOnCurveSet(self):
            return (self.flagAsByte & 1) != 0 


        """
        if set read 1 byte, else 2 bytes
        """
        def isXshortVectorSet(self):
            return (self.flagAsByte & 2) != 0

        """
        if set read 1 byte, else 2 bytes
        """
        def isYshortVectorSet(self):
            return (self.flagAsByte & 4) != 0

        """
        If set, the next byte specifies the number of additional
        times this set of flags is to be repeated. In this way,
        the number of flags listed can be smaller than the
        number of points in a character.
        """
        def isRepeatSet(self):
            return (self.flagAsByte & 8) != 0


        def isPositiveXshortVectorSet(self):
            return (self.flagAsByte & 16) != 0

        def isPositiveYshortVectorSet(self):
            return (self.flagAsByte & 32) != 0







'''
This table defines the mapping of character codes to the glyph index values
used in the font. It may contain more than one subtable, in order to support
more than one character encoding scheme


Character codes that do not correspond to any glyph 
in the font should be mapped to glyph index 0 (missing character)

'''
class CmapTable(FontTable):

    def __init__(self, handle, fontTableDirectory):

        handle.seek(fontTableDirectory.offset)

        self.cmapOffsetWithinFile = handle.tell()
        self.table = fontTableDirectory

        self.header = self.CmapTableHeader(handle)
        self.subTables = []

        LOGGER.debug('\tcmap: table version number {}'.format(self.header.tableVersionNumber))
        LOGGER.debug('\tcmap: number of encoding tables {}'.format(self.header.numberOfEncodingTables))

        for i in range(self.header.numberOfEncodingTables):
            #position = handle.tell()
            self.subTables.append( self.CmapSubTable(handle, self.cmapOffsetWithinFile ) )
            #handle.seek(position + 8)

    class CmapTableHeader():

        def __init__(self, handle):

            self.tableVersionNumber     = unpack('>H', handle.read(2) )[0]
            self.numberOfEncodingTables = unpack('>H', handle.read(2) )[0]

        def getContent(self):
            return pack('>H', self.tableVersionNumber) + pack('>H', self.numberOfEncodingTables)



    class CmapSubTable():

        def __init__(self, handle, cmapOffsetWithinFile):

            self.startOfTableOffset = handle.tell()
            self.cmapOffsetWithinFile = cmapOffsetWithinFile

            self.platformId = unpack('>H', handle.read(2) )[0]
            self.platformSpecificEncoding = unpack('>H', handle.read(2) )[0]
            self.byteOffset = unpack('>L', handle.read(4) )[0] # this offset is from startOfTableOffset


            # Format subtables might point to the same data

            # read at byteOffset to understand which Format is used
            savedHandle =  handle.tell()
            handle.seek( self.cmapOffsetWithinFile + self.byteOffset)
            fmt = unpack('>H', handle.read(2) )[0]
            LOGGER.debug('\tcmap: format {}'.format(fmt) )

            handle.seek( handle.tell() - 2)
            if fmt == 0:
                formatTable = self.Format0(handle)
            elif fmt == 4:
                formatTable = self.Format4(handle)
            elif fmt == 6:
                formatTable = self.Format6(handle)
            else:
                LOGGER.debug('\tcmap: Format table not parsed')
                raise Exception('Unknown format table')

            self.formatTable = formatTable

            handle.seek(savedHandle)






        def getContent(self):
            return pack('>H', self.platformId) + \
                   pack('>H', self.platformSpecificEncoding) + \
                   pack('>H', self.byteOffset)



        """
        a subtable can either be:
        - format 0
        - format 2
        - format 4
        """

        class Format0():

            def __init__(self, handle):
                self.offsetWithinFile = handle.tell()
                self.fmt = unpack('>H', handle.read(2) )[0]
                self.length = unpack('>H', handle.read(2) )[0]
                self.version = unpack('>H', handle.read(2) )[0]

                self.glyphIdArray = []
                for i in range(0, 256):
                    self.glyphIdArray.append( unpack('>B', handle.read(1))[0] )


        class Format4():

            def __init__(self, handle):

                self.offsetWithinFile = handle.tell()
                self.fmt = unpack('>H', handle.read(2) )[0]
                self.length = unpack('>H', handle.read(2) )[0]
                self.version = unpack('>H', handle.read(2) )[0]

                # 2 x segCount
                self.segCountX2 = unpack('>H', handle.read(2) )[0]

                self.searchRange = unpack('>H', handle.read(2) )[0]
                self.entrySelector = unpack('>H', handle.read(2) )[0]
                self.rangeShift = unpack('>H', handle.read(2) )[0]

                # WTF: end USHORT for *Count is 0xffff
                self.endCount = []
                for i in range(0, self.segCountX2 / 2 ):
                    self.endCount.append(unpack('>H', handle.read(2) )[0])

                # WTF: set to 0
                self.reservedPad = unpack('>H', handle.read(2) )[0]

                self.startCount = []
                for i in range(0, self.segCountX2 / 2 ):
                    self.startCount.append(unpack('>H', handle.read(2) )[0])

                self.idDelta = []
                for i in range(0, self.segCountX2 / 2 ):
                    self.idDelta.append(unpack('>H', handle.read(2) )[0])

                self.idRangeOffset = []
                for i in range(0, self.segCountX2 / 2 ):
                    self.idRangeOffset.append(unpack('>H', handle.read(2) )[0])

                self.glyphIdArray = []
                for i in range(0, (self.length - (handle.tell() - self.offsetWithinFile ) ) /2 ):
                    self.glyphIdArray.append (unpack('>H', handle.read(2) )[0])


        class Format6():

            def __init__(self, handle):
                self.offsetWithinFile = handle.tell()
                self.fmt = unpack('>H', handle.read(2) )[0]
                self.length = unpack('>H', handle.read(2) )[0]
                self.version = unpack('>H', handle.read(2) )[0]
                self.firstCode = unpack('>H', handle.read(2) )[0]
                self.entryCount = unpack('>H', handle.read(2) )[0]


                self.glyphIdArray = []
                for i in range(0, self.entryCount):
                    self.glyphIdArray.append( unpack('>H', handle.read(2))[0] )            


    # FIXME: Format stuff
    def getContent(self):
        data = self.header.getContent()

        for t in self.subTables:
            data += t.getContent()

        #print len(data), self.table.length

        assert len(data) == self.table.length, '[E] Length of content data != table length'

        return data


    def fuzz():
        pass

class HmtxTable(FontTable):


    def __init__(self, handle, fontTableDirectory, numberOfHMetrics, numGlyphs):

        self.hMetrics = []
        for i in range(0, numberOfHMetrics):
            self.hMetrics.append( self.LongHorMetric(handle) )


        self.leftSideBearing = []
        for i in range(0, numGlyphs - numberOfHMetrics):
            self.leftSideBearing.append( unpack('>h', handle.read(2))[0] )


    class LongHorMetric():

        def __init__(self, handle):
            self.advanceWidth = unpack('>H', handle.read(2))[0]
            self.lsb = unpack('>h', handle.read(2))[0]




class HheaTable(FontTable):


    def __init__(self, handle, fontTableDirectory):

        self.tableVersionNumber = unpack('>l', handle.read(4) )[0]
        self.ascender = unpack('>h', handle.read(2) )[0]
        self.descender = unpack('>h', handle.read(2) )[0]
        self.lineGap = unpack('>h', handle.read(2) )[0]
        self.advanceWidthMax = unpack('>H', handle.read(2) )[0]
        self.minLeftSideBearing = unpack('>h', handle.read(2) )[0]
        self.minRightSideBearing = unpack('>h', handle.read(2) )[0]
        self.xMaxExtent = unpack('>h', handle.read(2) )[0]
        self.caretSlopeRise = unpack('>h', handle.read(2) )[0]
        self.caretSlopeRun = unpack('>h', handle.read(2) )[0]
        self.reserved0 = unpack('>h', handle.read(2) )[0]
        self.reserved1 = unpack('>h', handle.read(2) )[0]
        self.reserved2 = unpack('>h', handle.read(2) )[0]
        self.reserved3 = unpack('>h', handle.read(2) )[0]
        self.reserved4 = unpack('>h', handle.read(2) )[0]
        self.metricDataFormat = unpack('>h', handle.read(2) )[0]
        self.numberOfHMetrics = unpack('>H', handle.read(2) )[0]



    def fuzz(self):
        #WTF: screw numberOfHMetrics
        pass


class KernTable(FontTable):

    def __init__(self, handle):

        self.version = unpack('>H', handle.read(2) )[0]
        self.nTables = unpack('>H', handle.read(2) )[0]

        self.subTables = []

        for i in range(0, self.nTables):

            fmt = unpack('>H', handle.read(2) )[0]
            handle.seek(handle.tell() - 2)

            LOGGER.debug('\tkern: subtable {}'.format(fmt))
            if fmt == 0:
                self.subTables.append(self.Format0(handle))
            elif fmt == 2:
                LOGGER.warn('\tkern: format2 subtable parser not completed')
                self.subTables.append(self.Format2(handle))                
            else:
                LOGGER.error('\tkern: unknown subtable {}'.format(fmt))
                raise Exception('kern: unknown subtable {}'.format(fmt))


    class Format0():

        def __init__(self, handle):
            self.offsetWithinFile = handle.tell()

            self.version = unpack('>H', handle.read(2) )[0]
            self.length = unpack('>H', handle.read(2) )[0]
            self.coverage = unpack('>H', handle.read(2) )[0]

            self.nPairs = unpack('>H', handle.read(2) )[0]
            self.searchRange = unpack('>H', handle.read(2) )[0]
            self.entrySelector = unpack('>H', handle.read(2) )[0]
            self.rangeShift = unpack('>H', handle.read(2) )[0]

            self.kerningPairs = []
            for i in range(0, self.nPairs):
                self.kerningPairs.append( self.KerningPair(handle) )


        class KerningPair():

            def __init__(self, handle):
                self.left = unpack('>H', handle.read(2) )[0]
                self.right = unpack('>H', handle.read(2) )[0]
                self.value = unpack('>h', handle.read(2) )[0]


    class Format2():


        def __init__(self, handle):
            self.offsetWithinFile = handle.tell()

            self.version = unpack('>H', handle.read(2) )[0]
            self.length = unpack('>H', handle.read(2) )[0]
            self.coverage = unpack('>H', handle.read(2) )[0]

            self.rowWitdh = unpack('>H', handle.read(2) )[0]
            self.leftClassTable = unpack('>H', handle.read(2) )[0]
            self.rightClassTable = unpack('>H', handle.read(2) )[0]
            self.array = unpack('>H', handle.read(2) )[0]


        class ClassTable():

            def __init__(self, handle):

                self.firstGlyph = unpack('>H', handle.read(2) )[0]
                self.nGlyphs = unpack('>H', handle.read(2) )[0]

    def fuzz(self):
        # WTF: fuzz format0 values
        pass


class NameTable(FontTable):

    def __init__(self, handle):

        self.offsetWithinFile = handle.tell()

        self.formatSelector = unpack('>H', handle.read(2) )[0]
        self.numberOfNameRecords = unpack('>H', handle.read(2) )[0]
        self.offsetToStartOfStringStorage = unpack('>H', handle.read(2) )[0]

        self.nameRecords = []
        for i in range(0, self.numberOfNameRecords):
            self.nameRecords.append( self.NameRecord( handle ) )


    class NameRecord():

        def __init__(self, handle):

            self.platformId = unpack('>H', handle.read(2) )[0]
            self.encodingId = unpack('>H', handle.read(2) )[0]
            self.languageId = unpack('>H', handle.read(2) )[0]
            self.nameId = unpack('>H', handle.read(2) )[0]
            self.stringLength = unpack('>H', handle.read(2) )[0]
            self.stringOffsetFromStartOfStorage = unpack('>H', handle.read(2) )[0]



    def fuzz(self):
        # fuzz offsets
        pass



class OS2Table(FontTable):

    def __init__(self, handle):

        self.version = unpack('>H', handle.read(2) )[0]
        self.xAvgCharWidth = unpack('>h', handle.read(2) )[0]
        self.usWeightClass = unpack('>H', handle.read(2) )[0]
        self.usWidthClass = unpack('>H', handle.read(2) )[0]
        self.fsType = unpack('>h', handle.read(2) )[0]
        self.ySubscriptXSize = unpack('>h', handle.read(2) )[0]
        self.ySubscriptYSize = unpack('>h', handle.read(2) )[0]
        self.ySubscriptXOffset = unpack('>h', handle.read(2) )[0]
        self.ySubscriptYOffset = unpack('>h', handle.read(2) )[0]
        self.ySuperscriptXSize = unpack('>h', handle.read(2) )[0]
        self.ySuperscriptYSize = unpack('>h', handle.read(2) )[0]
        self.ySuperscriptXOffset = unpack('>h', handle.read(2) )[0]
        self.ySuperscriptYOffset = unpack('>h', handle.read(2) )[0]
        self.yStrikeoutSize = unpack('>h', handle.read(2) )[0]
        self.yStrikeoutPosition = unpack('>h', handle.read(2) )[0]
        self.sFamilyClass = unpack('>h', handle.read(2) )[0]
        self.panose = unpack('>BBBBBBBBBB', handle.read(10) )
        self.ulUnicodeRange1  = unpack('>L', handle.read(4) )[0]
        self.ulUnicodeRange2  = unpack('>L', handle.read(4) )[0]
        self.ulUnicodeRange3  = unpack('>L', handle.read(4) )[0]
        self.ulUnicodeRange4  = unpack('>L', handle.read(4) )[0]

        self.achVendID = ''.join(unpack('>cccc', handle.read(4) ) )
        LOGGER.debug( self.achVendID  )
        self.fsSelection = unpack('>H', handle.read(2) )[0]
        self.usFirstCharIndex = unpack('>H', handle.read(2) )[0]
        self.usLastCharIndex = unpack('>H', handle.read(2) )[0]
        self.sTypoAscender = unpack('>H', handle.read(2) )[0]
        self.sTypoDescender = unpack('>H', handle.read(2) )[0]
        self.sTypoLineGap = unpack('>H', handle.read(2) )[0]
        self.usWinAscent = unpack('>H', handle.read(2) )[0]
        self.usWinDescent = unpack('>H', handle.read(2) )[0]

        # commented, some fonts don't follow the spec..
        #self.ulCodePageRange1 = unpack('>L', handle.read(4) )[0]
        #self.ulCodePageRange2 = unpack('>L', handle.read(4) )[0]


    def fuzz(self):
        # WTF: fuzz the whole table
        pass

class PostTable(FontTable):

    def __init__(self, handle):

        self.formatType = unpack('>l', handle.read(4) )[0]
        self.italicAngle = unpack('>l', handle.read(4) )[0]
        self.underlinePosition = unpack('>h', handle.read(2) )[0]
        self.underlineThickness = unpack('>h', handle.read(2) )[0]
        self.isFixedPitch = unpack('L', handle.read(4) )[0]
        self.minMemType42 = unpack('L', handle.read(4) )[0]
        self.maxMemType42 = unpack('L', handle.read(4) )[0]
        self.minMemType1 = unpack('L', handle.read(4) )[0]
        self.maxMemType1 = unpack('L', handle.read(4) )[0]


        # If the format is 1.0 or 3.0, the table ends here.
        if self.formatType != 0x10000 and self.formatType != 0x30000:

            if self.formatType == 0x20000:
                self.format2 = self.Format2(handle)

            else:
                LOGGER.error('\tpost: unknown table format {}'.format(self.formatType) )

    class Format2():

        def __init__(self, handle):

            self.numGlyphs = unpack('>H', handle.read(2) )[0]

            # glyph name array maps the glyphs in this font to name index
            # 
            # If the name index is between 258 and
            # 32767, then subtract 258 and use that to index into the list of Pascal strings at
            # the end of the table.

            self.glyphNameIndex = []
            for i in range(0, self.numGlyphs):
                self.glyphNameIndex.append( unpack('>H', handle.read(2) )[0] )


            self.postName = []
            for i in self.glyphNameIndex:

                if i >= 258:

                    # read a p-string
                    self.postName.append( PostTable.Pstring(handle) )

    class Pstring():

        def __init__(self, handle):


            self.length = unpack('>B', handle.read(1) ) [0]

            self.string = []
            for i in range(0, self.length):
                self.string.append( unpack('>c', handle.read(1) ) [0] )

            self.string = ''.join(self.string)



    def fuzz(self):
        # WTF:
        # - numGlyphs should be the same as maxp table
        # - truncate the string table
        pass


class VdmxTable(FontTable):


    def __init__(self, handle):
        self.version = unpack('>H', handle.read(2) )[0]
        self.numRecs = unpack('>H', handle.read(2) )[0]
        self.numRatios = unpack('>H', handle.read(2) )[0]


        self.ratRange = []
        for i in range(0, self.numRatios):
            self.ratRange.append( self.Ratios(handle) )


        self.offset = []
        for i in range(0, self.numRatios):
            self.offset.append( unpack('>H', handle.read(2) ) [0] )


            # TODO: VDMX groups 

    class Ratios():

        def __init__(self, handle):

            self.bCharSet = unpack('>B', handle.read(1) )[0]
            self.xRatio = unpack('>B', handle.read(1) )[0]
            self.yStartRatio = unpack('>B', handle.read(1) )[0]
            self.yEndRatio = unpack('>B', handle.read(1) )[0]


class Utils():

    '''
    returns new buffer
    '''
    @staticmethod
    def doBufferHeadChecksum(fileInMemory, headDirectoryOffset):


        assert len(fileInMemory) % 4 == 0, 'File must be 4 byte aligned'

        # these var names are actually inverted..
        headDirectoryOffsetWithinTheFile = headDirectoryOffset 
        headTableOffset = unpack('>L', fileInMemory[headDirectoryOffset + 8: headDirectoryOffset + 12 ])[0]

        LOGGER.debug( '[D] Head headDirectoryOffsetWithinTheFile {} - headTableOffset {}'.format(headDirectoryOffsetWithinTheFile, headTableOffset) )

        total_data = 0

        # round length
        checksumLength = ( unpack('>L', fileInMemory[headDirectoryOffset + 12:headDirectoryOffset + 16])[0] + 3 ) & ~3

        # set checkSumAdjustement to 0 in the read buffer
        fileInMemory = fileInMemory[:headTableOffset + 8] + pack('>I', 0 ) + \
            fileInMemory[headTableOffset  + 12:]

        table = fileInMemory[headTableOffset:headTableOffset+checksumLength]

        LOGGER.debug( '[D] table size {}'.format(len(table)) )

        for i in range(0, len(table), 4):
            if i == 8:    # actually useless
                data = 0  # set checkSumAdjustement to 0 in the read buffer
                checkSumAdjustement = unpack('>I', table[i:i+4] ) [0]
            else:
                data = unpack('>I', table[i:i+4] ) [0]

            total_data += data

        headTableChecksum = 0xffffffff & total_data


        # head table checksum done, update checksum field in memory
        newFileInMemory = fileInMemory[0:headDirectoryOffsetWithinTheFile + 4] +  pack('>L', headTableChecksum) + \
            fileInMemory[headDirectoryOffsetWithinTheFile + 8:]

        LOGGER.debug( '[D] head table checksum {} @ {}'.format(headTableChecksum, headDirectoryOffsetWithinTheFile + 4) )

        # now, calculate entire font checksum
        total_data = 0

        #print len(newFileInMemory) % 4 

        # calculate new checkSumAdjustement value
        for i in range(0, len(newFileInMemory), 4):
            data = unpack('>I', newFileInMemory[i:i+4])[0]
            total_data += data

        newCheckSumAdjustement = total_data & 0xffffffff 
        newCheckSumAdjustement = (0xb1b0afba - newCheckSumAdjustement ) & 0xffffffff 

        LOGGER.debug( '[D] head newCheckSumAdjustement {}'.format(newCheckSumAdjustement) )


        # update
        newFileInMemory = newFileInMemory[:headTableOffset + 8] + pack('>I',newCheckSumAdjustement ) + \
            newFileInMemory[headTableOffset  + 12:]


        LOGGER.debug( '[D] updating newCheckSumAdjustement {} @ {}'.format(newCheckSumAdjustement, headTableOffset + 8 ) )


        return newFileInMemory    


    '''
    Compute ttf checksum for a buffer, i.e. a font table


    '''
    @staticmethod
    def doBufferChecksum(buf):
        total_data = 0

        # pad with 0s
        mod = len(buf) % 4
        while mod > 0:
            buf += chr(0x0)
            mod -= 1

        # round length
        checksumLength = (len(buf) + 3 ) & ~3

        #print len(buf), checksumLength

        for i in range(0, checksumLength, 4):
            data = unpack('>I', buf[i:i+4] ) [0]
            total_data += data

        final_data = 0xffffffff & total_data

        LOGGER.debug( '\n\tcalculated checksum: {}'.format(final_data) )


        return final_data




    '''
    aka millerfuzz:

    "As a note, in the CSW slides, the length divisor is a
    variable called 'fuzzfactor' - I just guessed at 10"

    numwrites = random.randrange( math.ceil((float(len(buf)) / FuzzFactor)))+1
    for j in range(numwrites):
      rbyte = random.randrange(256)rn = random.randrange(len(buf))
      buf[rn] = "%c"%(rbyte)
      numwrites = random.randrange(math.ceil((float(len(buf)) / FuzzFactor)))+1

      for j in range(numwrites):
        rbyte = random.randrange(256)rn = random.randrange(len(buf))
	buf[rn] = "%c"%(rbyte);

    '''
    @staticmethod
    def fuzzBufferBitFlipping(buf, maxWrites, fuzzFactor=10):
        fileInMemory = list(buf)



        #fuzzFactor = 0
        #while fuzzFactor < 1:
        #    fuzzFactor = random.random() * random.random() * 500
        #fuzzFactor = 10 

        numwrites = random.randrange( math.ceil( (float(len(fileInMemory) ) / fuzzFactor) ) )  + 1

        if numwrites > maxWrites:
            numwrites = random.randrange(maxWrites)
        

        #print 'ff',  len(buf)/fuzzFactor, 'writes', numwrites

        LOGGER.debug('BitFlipper: changing {} / {} bytes '.format(numwrites, len(fileInMemory)) )

        # bit flip
        for j in range(numwrites):
            rbyte = random.randrange(256)
            rn = random.randrange(len(fileInMemory))
            fileInMemory[rn] = "%c"%(rbyte);


        fileInMemory = ''.join(fileInMemory)


        return fileInMemory, numwrites

    '''
    N.B
    - this fuzzer returns buffer with different size wrt the original
    - changed the frequencies of mutations/junk insertions
    - align to 4


    a] mutations: it takes successive chunks and mutates them:
    - increments a bit
    - decrements a bit
    - tries some binary corner cases also allowing for endian

    b] insertions/deletion: every so often (in this case, every 128th of the file) it 
    also inserts a bunch of junk. The junk is a mix of:
    - raw random
    - ascii
    - some wacked unicode
    - some terminators and special chars


    '''
    @staticmethod
    def fuzzBufferBenFuzz(buf, fuzzFactor2):
        buf = list(buf)


        # a] mutations

        fuzzFactor = 0
        while fuzzFactor < 1:
            fuzzFactor = random.random() * random.random() * 10	
            
        m = math.ceil( (float( len(buf) ) / fuzzFactor ) / fuzzFactor2 )
        numberOfMutations = random.randrange( m )	

        LOGGER.info('BenFuzz: mutations {}/{} - buffer size {}'.format(numberOfMutations, int(m), len(buf) ) )


        # how many
        for i in range(numberOfMutations):

            # where
            position = random.randrange(len(buf) )

            mutationType = random.randrange(5)

            # 1] increment
            if mutationType == 1:
                try:
                    buf[position] = '%c' % ( ord(buf[position]) + int('0b1', 2) )
                except OverflowError as e:
                    buf[position] = '%c' % 0x0

            # 2] decrement
            elif mutationType == 2:
                try:
                    buf[position] = '%c' % ( ord(buf[position]) - int('0b1', 2) )
                except OverflowError as e:
                    buf[position] = '%c' % 0xf

            elif mutationType == 3:
                buf[position] = '%c' % ( ord(buf[position]) | 0x8 )

            elif mutationType == 4:
                buf[position] = '%c' % ( ord(buf[position]) ^ 0xf )



        # b] insertions
        
        fuzzFactor = 10
        while fuzzFactor < 1:
            fuzzFactor = random.random() * random.random() * 10	


        m = math.ceil( (float( len(buf) ) / fuzzFactor ) / (fuzzFactor2 / 2)  )
        numberOfJunkInsertion = random.randrange( m )

        LOGGER.info('BenFuzz: junk insertions {}/{} - buffer size {}'.format(numberOfJunkInsertion, int(m), len(buf) ) )



        # how many
        for i in range(numberOfJunkInsertion):

            # where 
            position = random.randrange( len(buf) )

            insertionType = random.randrange( 5 )

            # 1] insert raw random
            if insertionType == 1:
                buf = buf[:position] + list('%c' % random.randrange(256) ) + buf[position:]

            # 2] insert ascii
            elif insertionType == 2:
                buf = buf[:position] + list('%c' % ord(random.choice(string.ascii_letters))) + buf[position:]

            # 3] remove a byte
            elif insertionType == 3:
                buf = buf[:position - 1] + buf[position:]

            # 4] insert null
            elif insertionType == 4:
                buf = buf[:position] + list('%c' % 0x0) + buf[position:]



        # pad with 0s

        while len(buf) % 4 != 0:
            buf += chr(0x0)

        assert len(buf) % 4 == 0, 'WTF {}'.format(len(buf))

        return buf, numberOfMutations + numberOfJunkInsertion	


if __name__ == '__main__':


    if len(sys.argv) == 2:
        LOGGER.debug('[*] arsing {}'.format(sys.argv[1]))
        
        f = TTFont(sys.argv[1])
        #table = random.choice(list(set(f.fontTableDirectories.keys()) - set(TTFont.REQUIRED_TABLES) ))    
        #fuzzFactor =  f.fontTableDirectories[table].length / 50
        
        #if fuzzFactor < 2:
        #    fuzzFactor = 2
        
        #LOGGER.info('[*]\t{}'.format( table ))
        #font = f.fuzzBenStyle(table, fuzzFactor)
        #font = f.fuzzBenStyle('glyf', 80)
        
        #font = f.fuzzGlyfsBitFlipping()
        #open('test/testCase', 'wb').write(font[0])
        name = f.fontTableDirectories['name'].table
        f = open( sys.argv[1],'rb')
        
        for i in name.nameRecords:
            
            if i.platformId != 3:
                continue
            
            offset = name.offsetWithinFile + name.offsetToStartOfStringStorage + i.stringOffsetFromStartOfStorage
            f.seek(offset)
            item = unpack('>{}s'.format(i.stringLength), f.read(i.stringLength))[0]
            
            # unicode
            if i.encodingId == 1:
                item = unicode(item, 'utf-16-be').encode('utf-8')

            print i.nameId,  item, i.stringLength

        

    if len(sys.argv) == 3:
        LOGGER.debug('Parsing {}'.format(sys.argv[1]))
        for i in os.listdir(sys.argv[2]):
            print '% {}'.format(i)
            try:
                TTFont(i)
            except:
                continue
