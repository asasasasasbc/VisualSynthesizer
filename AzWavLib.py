#######################################################################
# This is an un-executable library file I wrote to handle wav file format,
# to separate tasks a little bit.
# Author: Alan Zhang
# [Exclusively for 112 term project]
#######################################################################

import math
import numpy as np

# BASIC TOOLS SECTION: includes some basic int->binary, numpy manipulation
# region 
#Convert little endian binary lists to int
def litInt(bts):
    if(isinstance(bts, list)):
        bts = b''.join(bts)
    return int.from_bytes(bts, byteorder='little')

# convert little endian binary lists (2 complemented for negative) to int
def litBytesTo2CompleSignedInt(bts):
    if(isinstance(bts, list)):
        bts = b''.join(bts)
    return int.from_bytes(bts, byteorder='little', signed = True)

# convert traditional big endian binary lists to int
def bytes_to_int(bts, order = 'big'):
    if(isinstance(bts, list)):
        bts = b''.join(bts)
    return int.from_bytes(bts, byteorder=order)

# a general int to binary lists convertion function
def litByte(i,size = 4, signed = False):  
    return i.to_bytes(size, byteorder='little', signed = signed)

# used to merge np2 numpy array at np1's i-th position
# handles some edge cases like some part of np2 is out of np1's index
def npInsert(np1:np.ndarray, np2:np.ndarray, i:int):
    requiredL = i + len(np2)
    ans = np1
    if(len(np1) < requiredL):
        tail =  np.zeros(requiredL - len(np1), dtype = int)
        ans = np.append(np1,tail)
    ans[i:requiredL] += np2
    return ans

# endregion 
# END OF TOOLS SECTION

# START MYWAV CLASS DEFINITION
# region

# Alan Zhang's Wav (AzWav) class 
# Currently can only handle PCM16 (16bit) mono or stereo .wav file
# UPDATE LOG
# 20/12/9
# 1.1: Added numpy clipping method to avoid integer overflow when 
# writing the buffer
# 20/11/19
# 1.01: Fixed wav file's meta data cause noise issue.
# 1.0: I think it should be good enough!
# 20/11/15
# 0.9: Added numpy functions to boost handling speed!

# I learned WAV specification from http://soundfile.sapp.org/doc/WaveFormat/
class AzWav:
    # define my library version
    version = '1.1'

    # Wav data structure definition
    # region
    '''
    # HEADER
    chunkId: list = [b'R', b'I', b'F', b'F']
    chunkSize: int = 36 #4 + (8 + subChunk1Size) + (8 + subChunk2Size)
    wavFormat: list = [b'W', b'A', b'V', b'E']
    # SUB CHUNK 1 part
    subChunk1ID: list = [b'f', b'm', b't', b'\x20']   
    subChunk1Size: int = 16 # 16 for PCM
    audioFormat: int = 1
    numChannels: int = 1 
    sampleRate: int = 44100
    byteRate: int = 44100 * 1 * 2#SampleRate * NumChannels * BitsPerSample/8
    blockAlign: int = 2#NumChannels * BitsPerSample/8
    # The number of bytes for one sample including all channels
    bitsPerSample: int = 16
    # SUB CHUNK 2 part
    subChunk2ID: list = [b'd', b'a', b't', b'a']
    subChunk2Size:int = 0#NumSamples * NumChannels * BitsPerSample/8
    data:list = []
    primaryTrack:list = []
    secondaryTrack:list = []
    soundTime: float = 0
    '''
    # endregion

    # initialize the class..
    def __init__(self):
        print(f'New AzWav object v{AzWav.version} initialized')
        self.chunkId = [b'R', b'I', b'F', b'F']
        self.chunkSize= 36 #4 + (8 + subChunk1Size) + (8 + subChunk2Size)
        self.wavFormat= [b'W', b'A', b'V', b'E']
        # SUB CHUNK 1 part
        self.subChunk1ID= [b'f', b'm', b't', b'\x20']   
        self.subChunk1Size= 16 # 16 for PCM
        self.audioFormat= 1
        self.numChannels= 1 
        self.sampleRate= 44100
        self.byteRate= 44100 * 1 * 2#SampleRate * NumChannels * BitsPerSample/8
        self.blockAlign= 2#NumChannels * BitsPerSample/8
        # The number of bytes for one sample including all channels
        self.bitsPerSample= 16
        # SUB CHUNK 2 part
        self.subChunk2ID= [b'd', b'a', b't', b'a']
        self.subChunk2Size = 0#NumSamples * NumChannels * BitsPerSample/8
        self.data = []
        self.primaryTrack = []
        self.secondaryTrack = []
        self.soundTime = 0
        self.buffer:np.ndarray = np.zeros(0,dtype = int)

    # print the wav file info for debugging purpose.
    def printInfo(self):
        print('Chunk id:', str(self.chunkId))
        print('Chunk size' + str(self.chunkSize))
        print('Format raw data:' + str(self.wavFormat))
        print('subChunk1ID:' + str(self.subChunk1ID))
        print('subChunk1Size:' , self.subChunk1Size)

        print('audioFormat:' , self.audioFormat)
        print('numChannels:' , self.numChannels)
        print('sampleRate:' , self.sampleRate, 'samples/second')
        print('byteRate:' , self.byteRate , 'bytes/second')
        print('blockAlign:' , self.blockAlign, 'bytes per block') # 
        # block align = [2 * numChannels ]in 16bit situation
        print('bitsPerSample:' , self.bitsPerSample)

        print('subChunk2ID:' + str(self.subChunk2ID))
        print('subChunk2Size:' , self.subChunk2Size, 'byte')
        print('Data[original file] length:' , len(self.data))

    # read the wav file according to the path.
    def read(self, path):
        byteArray = []
        with open(path, "rb") as f:
            byte = f.read(1)
            while byte != b"":
                # Read all bytes to array.
                byteArray.append(byte)  
                byte = f.read(1)
        self.chunkId = byteArray[0:4]
        
        # littlie endian chunk size to big endian for understanding
        self.chunkSize = bytes_to_int(byteArray[4:8],'little')   
        
        # larget endian
        self.wavFormat =  byteArray[8:12]
        
        
        # big endian chunk ID
        self.subChunk1ID = byteArray[12:16]
        # little endian chunk 1 size
        self.subChunk1Size= bytes_to_int(byteArray[16:20],'little')   
        # little endian audio format [2 byte]
        self.audioFormat =  litInt(byteArray[20:22])
        # little endian num channels
        self.numChannels = litInt(byteArray[22:24])
        # little endian sample rate
        self.sampleRate = litInt(byteArray[24:28])
        # little endian byte rate
        self.byteRate = litInt(byteArray[28:32])
        # little endian block align
        self.blockAlign = litInt(byteArray[32:34])
        # little endian bits per sample
        self.bitsPerSample = litInt(byteArray[34:36])

        # big endian chunk ID
        self.subChunk2ID = byteArray[36:40]
        self.subChunk2Size = litInt(byteArray[40:44])
        self.data = byteArray[44:]

        if(len(self.data) != (self.subChunk2Size)):
            print('This wav file contains some meta data.')
            self.data = self.data[0:self.subChunk2Size]
        

        self.soundTime = len(self.data) / self.byteRate
        print('Total music time:' , self.soundTime)

        print('Currently only 16bits per sample is allowed!')
        if(self.bitsPerSample != 16):
            print('Not 16bits per sample! Incompatible!')
            return

        # generate self defined track data
        self.primaryTrack = [] # primary track is for mono / stereo left channel!
        self.secondaryTrack = [] # secondary track is for stereo right channel!
        # since only 1 channel and 16bit, one block is 2 byte.
        # we directly decode that as a signed int.
        for i in range(0,len(self.data),self.blockAlign):
            val = litBytesTo2CompleSignedInt(self.data[i:i+2])
            self.primaryTrack.append(val)
        if(self.numChannels > 1):
            for i in range(0,len(self.data),self.blockAlign):
                val = litBytesTo2CompleSignedInt(self.data[i+2:i+4])
                self.secondaryTrack.append(val)
        print('Load success!')


    # write buffer area instread of primary/secondary track.
    # calculate all the header info and write to the file.
    def writeBuffer(self, path):
        # CALCULATE SECTION
        self.byteRate = self.sampleRate * self.numChannels * \
                        self.bitsPerSample // 8
        self.blockAlign = self.numChannels * self.bitsPerSample // 8
        self.buffer = np.clip(self.buffer,-32768, 32767)#(-32768<=val <=32767)
        samples = len(self.buffer)
        self.subChunk1Size = 16 # for PCM
        self.subChunk2Size = samples * self.numChannels * \
                             self.bitsPerSample // 8
        self.chunckSize = 4 + 8 + self.subChunk1Size + 8 + self.subChunk2Size

        print('Start writing...')


        binarys = b''
        bArray = []
        
        # header
        bArray.extend(self.chunkId)#4 byte
        bArray.extend([litByte(self.chunckSize)])#4 byte little endian
        bArray.extend(self.wavFormat)
        # sub chunk 1
        bArray.extend(self.subChunk1ID)
        bArray.extend([litByte(self.subChunk1Size)])#4 byte little endian
        bArray.extend([litByte(self.audioFormat, size = 2)])
        bArray.extend([litByte(self.numChannels, size = 2)])
        bArray.extend([litByte(self.sampleRate, size = 4)])
        bArray.extend([litByte(self.byteRate, size = 4)])
        bArray.extend([litByte(self.blockAlign, size = 2)])
        bArray.extend([litByte(self.bitsPerSample, size = 2)])
        # sub chunk 2
        bArray.extend(self.subChunk2ID)
        bArray.extend([litByte(self.subChunk2Size, size = 4)])

        # calculate data from primary track and secondary track!
        if(self.numChannels == 1):
            for val in self.buffer:
                #For 16bit signed int, (-32768<=val <=32767)
                val = int(val)
                #if(val > 32767):
                #    val = 32767
                #elif(val < -32768):
                #    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))
        elif(self.numChannels == 2):
            for i in range(len(self.buffer)):
                val =int(self.buffer[i])
                #if(val > 32767):
                #    val = 32767
                #else:
                #    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))

                val =int(self.buffer[i])
                #if(val > 32767):
                #    val = 32767
                #elif(val < -32768):
                #    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))

        binarys = binarys.join(bArray)
        print('binary length:', len(binarys))
        f = open(path,'wb')
        f.write(binarys)
        f.close()
        print('Write success!')

    # calculate all the header info and write tracks to the file.
    def write(self, path):
        # CALCULATE SECTION
        self.byteRate = self.sampleRate * self.numChannels * \
                        self.bitsPerSample // 8
        self.blockAlign = self.numChannels * self.bitsPerSample // 8
        samples = len(self.primaryTrack)
        self.subChunk1Size = 16 # for PCM
        self.subChunk2Size = samples * self.numChannels * \
                             self.bitsPerSample // 8
        self.chunckSize = 4 + 8 + self.subChunk1Size + 8 + self.subChunk2Size

        print('Start writing...')


        binarys = b''
        bArray = []
        
        # header
        bArray.extend(self.chunkId)#4 byte
        bArray.extend([litByte(self.chunckSize)])#4 byte little endian
        bArray.extend(self.wavFormat)
        # sub chunk 1
        bArray.extend(self.subChunk1ID)
        bArray.extend([litByte(self.subChunk1Size)])#4 byte little endian
        bArray.extend([litByte(self.audioFormat, size = 2)])
        bArray.extend([litByte(self.numChannels, size = 2)])
        bArray.extend([litByte(self.sampleRate, size = 4)])
        bArray.extend([litByte(self.byteRate, size = 4)])
        bArray.extend([litByte(self.blockAlign, size = 2)])
        bArray.extend([litByte(self.bitsPerSample, size = 2)])
        # sub chunk 2
        bArray.extend(self.subChunk2ID)
        bArray.extend([litByte(self.subChunk2Size, size = 4)])

        # calculate data from primary track and secondary track!
        if(self.numChannels == 1):
            for val in self.primaryTrack:
                if(val > 32767):
                    val = 32767
                elif(val < -32768):
                    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))
        elif(self.numChannels == 2):
            for i in range(len(self.primaryTrack)):
                val = self.primaryTrack[i]
                if(val > 32767):
                    val = 32767
                else:
                    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))

                val = self.secondaryTrack[i]
                if(val > 32767):
                    val = 32767
                elif(val < -32768):
                    val = -32768
                bArray.append(litByte(val,size = 2, signed = True))

        binarys = binarys.join(bArray)
        print('binary length:', len(binarys))
        f = open(path,'wb')
        f.write(binarys)
        f.close()
        print('Write success!')


    # useful tool set to reverse the sound!
    def reverse(self):
        self.primaryTrack.reverse()
        self.secondaryTrack.reverse()


    # return the faded track
    def fadeTrack(self, ansTrack, fadeStart, fadeDuration):
        # to avoid the noise...
        fadeStartLength = int(fadeStart * self.sampleRate)
        fadeLength = int(fadeDuration * self.sampleRate)
        fadeArray = np.linspace(1, 0, num=fadeStartLength)
        
        
        if(fadeStartLength + fadeLength <= len(ansTrack)):
            #ansTrack[fadeStart:fadeStart + fadeLength] *= fadeArray
            np.multiply(ansTrack[fadeStartLength:fadeStartLength + fadeLength], fadeArray, 
            out=ansTrack[fadeStartLength:fadeStartLength + fadeLength], casting='unsafe')
            ansTrack[fadeStartLength + fadeLength:] *= 0
        elif(fadeStart  >=  len(ansTrack)):
            pass
        else:
            fadeLength = len(ansTrack) - fadeStart
            #ansTrack[fadeStart:len(ansTrack)] *= fadeArray[0:fadeLength]
            np.multiply(ansTrack[fadeStart:fadeStart + fadeLength], 
                        fadeArray[0:fadeLength], 
            out=ansTrack[fadeStart:fadeStart + fadeLength], casting='unsafe')

        return ansTrack


    # sound pitch, return the track nparray<int> with pitched sound.
    # currently fade does not work. Find fade function in AzXMLLib.
    def pitchedTrack(self, baseFreq, toFreq, amp = 0.5, fade = True, 
                     duration = -1, fadeEnd = 0.1, targetSampleRate = 44100):
        
        def listLerp(track, index):
            if(index < 0 ):
                return 0
            elif(len(track) - 1 >= 0 and 
                index >= len(track) - 1): # last sample is discarded.
                return track[len(track) - 1]
            first = math.floor(index)
            second = math.ceil(index)
            fractor = index - first
            return (track[first] * (1 - fractor) + track[second] * fractor)

        sampleCount = int(duration * self.sampleRate)
        if(sampleCount < 0):
            sampleCount = max(len(self.primaryTrack) - 1, 0)
        if(sampleCount == 0):
            return np.zeros(1, dtype = np.int16)

        
        ratio = toFreq / baseFreq
        # in the case sample rate is differnet
        if(self.sampleRate != targetSampleRate):
            ratio *= (self.sampleRate / targetSampleRate)

        ansTrack = np.zeros(sampleCount, dtype = float)
        trackIndex = 0
        sampleIndex = 0.0
        # new way using np.interp
        xp = np.arange(0, len(self.primaryTrack))
        fp = np.array(self.primaryTrack)
        x = np.arange(0, len(self.primaryTrack), step = ratio)

        pitched = np.interp(x, xp, fp)
        pitched = np.clip(pitched,-32768, 32767)#(-32768<=val <=32767)
        if(len(ansTrack) >= len(pitched)):
            ansTrack[0:len(pitched)]+=pitched
        else:
            ansTrack = pitched[0:len(ansTrack)]
        ansTrack *= amp


        return ansTrack.astype(np.int16)

    # generate sin wav at certain frequency! return track with int np array!
    # use wav settings because needs basic frequnecy
    # Caution! PCM16 only allow -32768 to 32767 int range.
    def sinWave(self, frequency, duration, amp = 0.5, 
                fade = True, boost = True):
        maxAmp = 32766 # to avoid reaching to high sound!
        samples = int(self.sampleRate * duration)
        sampleArr = np.arange(0,samples, dtype = float) / self.sampleRate
        sampleArr *= (2 * math.pi * frequency)
        sampleArr = np.sin(sampleArr) * maxAmp * amp
        sampleArr = np.clip(sampleArr,-32768, 32767)#(-32768<=val <=32767)
        return sampleArr.astype(np.int16)

        # Old codes that uses lists to do the same thing!
        ans = []
        time  = 0
        for i in range(samples):
            time = i / self.sampleRate
            val = int(maxAmp * amp * math.sin(time * (2 * math.pi * frequency)))
            if(fade == True):
                if(time < 0.1):
                    val = int(val * (time / 0.1))
                remainTime = duration - time
                if(remainTime < 0.1):
                    val = int(val * (remainTime / 0.1))
            ans.append(val)
        return np.array(ans)

    
    # Insert track segments into the both tracks list.
    # It is quite slow though. Better use bufferArea and bufferInsert instead.
    # Which uses numpy and it is 5 times more fast. (But need to allocate the
    # fixed memroy area for buffer Area. That's how numpy works....)
    def insert(self, sampleStart, trackSeg):
        if(len(self.primaryTrack) < sampleStart + len(trackSeg)):
            extendSize = sampleStart + len(trackSeg) - len(self.primaryTrack)
            self.primaryTrack += [0] * extendSize
        for i in range(len(trackSeg)):
            #if(i + sampleStart >= len(self.primaryTrack)):
            #    print(f'Error! i = {i}, i + sampleStart = {i + sampleStart}, \
            #            primaryTrack = {self.primaryTrack}')
            self.primaryTrack[i + sampleStart] += trackSeg[i]

        if(self.numChannels > 1):
            if(len(self.secondaryTrack) < sampleStart + len(trackSeg)):
                extendSize = sampleStart + len(trackSeg) - \
                             len(self.secondaryTrack)
                self.secondaryTrack += [0] * extendSize
            for i in range(len(trackSeg)):
                self.secondaryTrack[i + sampleStart] += trackSeg[i]

    # Create a buffer area for much, much faster track insert!
    # Although buffer area can extend by itself, you should better initialize
    # it with a reasonable large size (1unit = 1 sample per track)
    def bufferArea(self, bufferSamples):
        self.buffer = np.zeros(bufferSamples,dtype = int)
    
    # Insert the track seg into the buffer. GONNA GO FAST
    # Faster than default insert method
    def bufferInsert(self, sampleStart, trackSeg):
        if(isinstance(trackSeg, np.ndarray)):
            try:
                self.buffer = npInsert(self.buffer, 
                          trackSeg, max(sampleStart,0)) # avoid <0 situation
            except:
                print('Error happend!')
                print('Sample start is:', sampleStart)
                print('trackSeg shape:', len(trackSeg))
                print('Buffer shape:', len(self.buffer))
        else:
            self.buffer = npInsert(self.buffer, 
                      np.array(trackSeg,dtype=int),  max(sampleStart,0))

    # calculate buffer to the track list type.
    def bufferToList(self):
        return self.buffer.tolist()

    # convert the primrary track to the numpyarray
    # so that it can be played via pyaudio
    def toNpArray(self):
        return np.array(self.primaryTrack,dtype=int)

# endregion



# MISCELLANOUS REGION
# print the error message. 
if (__name__ == '__main__'):
    print('Error! This is just a library file!')
    print('You should not directly run my library file.')
    print('Please run ProgramGUI.py instead!')