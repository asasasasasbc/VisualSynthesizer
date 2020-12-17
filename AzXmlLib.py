#######################################################################
# This is an un-executable library file I wrote to handle music XML format
# as notes, to separate tasks a little bit.
# Author: Alan Zhang
# [Exclusively for 112 term project]
# V1.1: Added generateMusicBasedOnAbsList function for .synnote file
# V1.01: Added illegal notes convertion, i.e. 3#, 4b,
# V1.00: Only support uncompressed xml format, UTF-8 coded musicxml file!
#######################################################################


# wav library is already too long, so I separated the code from Program.py
from AzWavLib import *

# FREQUENCY DEFINITION
# region
# frequency referred in https://en.wikipedia.org/wiki/Piano_key_frequencies
def getFreDictionary():
    ans = {
        '':100,

        "---1":32.70320,
        "---1#":34.64783,
        "---2b":34.64783,
        "---2":36.70810,
        "---2#":38.89087,
        "---3b":38.89087,
        "---3":41.20344,
        "---4":43.65353,
        "---4#":46.24930,
        "---5b":46.24930,
        "---5":48.99943,
        "---5#":51.91309,
        "---6b":51.91309,
        "---6":55.00000,
        "---6#":58.27047,
        "---7b":58.27047,
        "---7":61.73541,


        "--1":65.40639,
        "--1#":69.29566,
        "--2b":69.29566,
        "--2":73.41619,
        "--2#":77.78175,
        "--3b":77.78175,
        "--3":82.40689,
        "--4":87.30706,
        "--4#":92.49861,
        "--5b":92.49861,
        "--5":97.99886,
        "--5#":103.8262,
        "--6b":103.8262,
        "--6":110.0000,
        "--6#":116.5409,
        "--7b":116.5409,
        "--7":123.4708,


        "-1":130.8128,
        "-1#":138.5913,
        "-2b":138.5913,
        "-2":146.8324,
        "-2#":155.5635,
        "-3b":155.5635,
        "-3":164.8138,
        "-4":174.6141,
        "-4#":184.9972,
        "-5b":184.9972,
        "-5":195.9977,
        "-5#":207.6523,
        "-6b":207.6523,
        "-6":220.0000,
        "-6#":233.0819,
        "-7b":233.0819,
        "-7":246.9417,



        "1":261.6256,
        "1#":277.1826,
        "2b":277.1826,
        "2":293.6648,
        "2#":311.1270,
        "3b":311.1270,
        "3":329.6276,
        "4":349.2282,
        "4#":369.9944,
        "5b":369.9944,
        "5":391.9954,
        "5#":415.3047,
        "6b":415.3047,
        "6":440.0000,
        "6#":466.1638,
        "7b":466.1638,
        "7":493.8833,


        "+1":523.2511,
        "+1#":554.3653,
        "+2b":554.3653,
        "+2":587.3295,
        "+2#":622.2540,
        "+3b":622.2540,
        "+3":659.2551,
        "+4":698.4565,
        "+4#":739.9888,
        "+5b":739.9888,
        "+5":783.9909,
        "+5#":830.6094,
        "+6b":830.6094,
        "+6":880.0000,
        "+6#":932.3275,
        "+7b":932.3275,
        "+7":987.7666,

        "++1":1046.502,
        "++1#":1108.731,
        "++2b":1108.731,
        "++2":1174.659,
        "++2#":1244.508,
        "++3b":1244.508,
        "++3":1318.510,
        "++4":1396.913,
        "++4#":1479.978,
        "++5b":1479.978,
        "++5":1567.982,
        "++5#":1661.219,
        "++6b":1661.219,
        "++6":1760.000,
        "++6#":1864.655,
        "++7b":1864.655,
        "++7":1975.533,


        "+++1":2093.005,
        "+++1#":2217.461,
        "+++2b":2217.461,
        "+++2":2349.318,
        "+++2#":2489.016,
        "+++3b":2489.016,
        "+++3":2637.020,
        "+++4":2793.826,
        "+++4#":2959.955,
        "+++5b":2959.955,
        "+++5":3135.963,
        "+++5#":3322.438,
        "+++6b":3322.438,
        "+++6":3520.000,
        "+++6#":3729.310,
        "+++7b":3729.310,
        "+++7":3951.066,

        "++++1":4186.009,
    }
    return ans
# endregion
# END OF FREQUENCT DEFINITION

# handles providing the corresponding pitch's track (numpy array-like)
class sampleLibrary:
    sinWave: AzWav = AzWav() # a static attribute used to generate sin wav 
    # initialize!
    def __init__(self, wav:AzWav):
        if(wav == None):
            self.sample = wav
            self.sampleC5 = wav # for higher definition music
            self.sampleC6 = wav # for higher definition music
            self.trackDict = dict()
            self.freList = getFreDictionary()
            self.fadeTime = 0.2
        
            self.fadeLength = int(self.fadeTime * 
                              sampleLibrary.sinWave.sampleRate)
            self.fadeArray = np.linspace(1.0, 0.0, num=self.fadeLength)
            return

        self.sample : AzWav = wav
        self.trackDict = dict()
        self.freList = getFreDictionary()
        self.fadeTime = 1.5
        
        self.fadeLength = int(self.fadeTime * self.sample.sampleRate)
        self.fadeArray = np.linspace(1.0, 0.0, num=self.fadeLength)

    # prepare all pitched tracks
    def prepare(self):
        if(self.sample == None):
            return
        print('preparing the sample tracks for real time playback... May take some time')

        for pitch in self.freList:
            self.getTrack(pitch, 0.1,1)
        print('Preparation completed!')

    # set the sound tone
    def setSampleWav(self, wav: AzWav):
        self.sample = wav
        self.sampleC5 = wav
        self.sampleC6 = wav
        self.trackDict = dict()
    # set the sound fade out time
    def setFadeTime(n):
        self.fadeTime = n
    # get a certain pitched track
    def getTrack(self, pitch, duration, amp):
        k = pitch
        if(pitch not in self.freList):
            print('No such key found!:', pitch)
            return np.zeros(100)

        ansTrack = None
        if(self.sample == None):
            sinSampleRate = sampleLibrary.sinWave.sampleRate
            ansTrack = sampleLibrary.sinWave.sinWave(self.freList[pitch],
                        duration + self.fadeTime , amp = 1)
            # fade start array for sin wav
            # to avoid the noise...
            fadeStartLength = int(0.1 * sinSampleRate)
            fadeStartArray = np.linspace(0.0, 1, num=fadeStartLength)
            
            if(len(fadeStartArray) <= len(ansTrack)):
                np.multiply(ansTrack[0:len(fadeStartArray)], 
                        fadeStartArray[0:len(fadeStartArray)], 
                out=ansTrack[0:len(fadeStartArray)], casting='unsafe')
            else:
                np.multiply(ansTrack[0:len(ansTrack)], 
                        fadeStartArray[0:len(ansTrack)], 
                out=ansTrack[0:len(ansTrack)], casting='unsafe')



        # generate new track
        if(k not in self.trackDict and self.sample != None):
            
            #self.freList[pitch], amp = 1, duration = duration + 1.5,
            #            fadeEnd = 1.5)
            targetSample = self.sample
            if(self.sampleC5 == self.sample):
                track = targetSample.pitchedTrack(self.freList['1'],
                self.freList[pitch], amp = 1, duration = -1,
                    fade = False)

            elif(self.freList[pitch] < self.freList['+1']): 
                track = targetSample.pitchedTrack(self.freList['1'],
                self.freList[pitch], amp = 1, duration = -1,
                    fade = False)
            elif(self.freList[pitch] < self.freList['++1']): 
                targetSample = self.sampleC5
                track = targetSample.pitchedTrack(self.freList['+1'],
                self.freList[pitch], amp = 1, duration = -1,
                    fade = False)   
            else: 
                targetSample = self.sampleC6
                track = targetSample.pitchedTrack(self.freList['++1'],
                self.freList[pitch], amp = 1, duration = -1,
                    fade = False)          
            
            self.trackDict[k] = track

        fadeStart = 0
        if(self.sample != None):
            ansTrack = np.copy(self.trackDict[k])
            fadeStart = int(duration * self.sample.sampleRate)
        else:
            fadeStart = int(duration * sampleLibrary.sinWave.sampleRate)
        
        fadeArray = self.fadeArray
        
        if(fadeStart + self.fadeLength <= len(ansTrack)):
            #ansTrack[fadeStart:fadeStart + fadeLength] *= fadeArray
            np.multiply(ansTrack[fadeStart:fadeStart + self.fadeLength], fadeArray, 
            out=ansTrack[fadeStart:fadeStart + self.fadeLength], casting='unsafe')
            #ansTrack[fadeStart + self.fadeLength:] *= 0
            ansTrack = ansTrack[0:fadeStart + self.fadeLength]
        elif(fadeStart  >=  len(ansTrack)):
            pass
        else:
            fadeLength = len(ansTrack) - fadeStart
            #ansTrack[fadeStart:len(ansTrack)] *= fadeArray[0:fadeLength]
            np.multiply(ansTrack[fadeStart:fadeStart + fadeLength], 
                        fadeArray[0:fadeLength], 
            out=ansTrack[fadeStart:fadeStart + fadeLength], casting='unsafe')

        #ansTrack *= amp
        np.multiply(ansTrack, amp, 
            out=ansTrack, casting='unsafe')

        return ansTrack



# convert to simple note
#i.e. convert 'C4#' to '1#'
# convert 'D4#' to '2#'
def convertNote(n):
    ans = ''
    if(len(n) < 2):
        return ''
    tail = n [2:]
    l = n[0]
    d = int(n[1]) # 4,5,6
    if(l == 'A'):
        l = 'H'
    if(l == 'B'):
        l = 'I'
    lInt = ord(l) - ord('C') # v to -1, c to 0,d to 1
    
    # c4 to 0    d4 to 1
    finalInt = lInt + 7 * (d -4) 
    while(len(tail) > 1):
        if(tail[0] == '#'):
            finalInt += 1
        elif(tail[0] == 'b'):
            finalInt -= 1
        tail = tail[2:]
    
    #print('Final int:', finalInt)
    #C4:0    D4:1    D5:2
    # -1->7  0->1 ...6->7 7->+1
    step = ((finalInt)% 7 ) + 1
    if((step == 7 or step == 3) and '#' in tail):
        print('Illegal note found:' + (str(step) + tail))
        octave = (finalInt - step + 1) // 7


        tail = ''
        finalInt += 1
        step = ((finalInt)% 7 ) + 1
        print('Converted to legal note')
    if((step == 1 or step == 4) and 'b' in tail):
        print('Illegal note found:' + (str(step) + tail))

        tail = ''
        finalInt -= 1
        step = ((finalInt)% 7 ) + 1
        print('Converted to legal note')


    octave = (finalInt - step + 1) // 7
    if(octave > 0):
        ans = ('+' * abs(octave)) + ans
    elif(octave < 0):
        ans = ('-' * abs(octave)) + ans
    ans = ans + str(step) + tail



    

    #print(n,'Convert to',ans)
    return ans 




# generate music based on xmlPath or synnote path and write to path.
def generateBaseOnXml(path, xmlPath, noteTime = 0.8, 
                      sampleList = [], globalAmpList = [], useSamLibrary = None,
                      calculateNoteTime = False, outNoteList = None):
    freList = getFreDictionary()
    audioInfo = dict()
    notes = []
    if(xmlPath.endswith('.synnote')):
        notes = parseSynnote(xmlPath,staff = 0, audioInfo = audioInfo)
    else:
        notes = parseMusicXML(xmlPath,staff = 0, audioInfo = audioInfo)
    #notes2 = parseMusicXML(xmlPath,staff = 2)

    noteList = dict()

    if(calculateNoteTime == True):
        if('bpm' in audioInfo):
            bpm = audioInfo['bpm']
            noteTime = 60 / bpm
            print('Note time calculated, BPM = ', bpm)
    
    if('staffs' not in audioInfo):
        audioInfo['staffs'] = [0]
        print('No staff marker found.')

    maxDuration = 1
    if('staffs' in audioInfo):
        staffList = audioInfo['staffs']
        print(staffList)
        for staffIndex in staffList:
            print('Parsing staff', staffIndex)
            result = parseMusicXML(xmlPath,staff = staffIndex,
                                   audioInfo = audioInfo)
            noteList[staffIndex] = result
            #print(result)
            duration = calculateDuration(noteList[staffIndex],noteTime)
            maxDuration = max(duration, maxDuration)
            print('Staff',staffIndex,' loaded, duration:',duration)
            amp = 0.5
            if(staffIndex < len(globalAmpList)):
                amp = globalAmpList[staffIndex]
            if(outNoteList != None):
                outNoteList += calculateAbsTime(noteList[staffIndex],noteTime, 
                                                staffIndex, amp)
   

    if(outNoteList != None):
        print('Outputed as note lists')
        return None
    wav = AzWav()
    
    wav.bufferArea(int(maxDuration * wav.sampleRate))
    for tmpNotesIndex in noteList:
        tmpNotes = noteList[tmpNotesIndex]
        print(f'Staff {tmpNotesIndex} note count: {len(tmpNotes)}')
        #print(f'Staff {tmpNotesIndex} note: {(tmpNotes)}')
        duration = calculateDuration(tmpNotes,noteTime)
        
        # noteTime is per metre (time)
        cTime = 0
        sample = None
        sampleLib =  sampleLibrary(None)
        globalAmp = 0.5
        if(tmpNotesIndex < len(globalAmpList)):
            globalAmp = globalAmpList[tmpNotesIndex]

        if(useSamLibrary != None):
            sampleLib = useSamLibrary
            sample = sampleLib.sample

        elif(tmpNotesIndex < len(sampleList)):
            sample = sampleList[tmpNotesIndex]
            if(sample != None):
                sampleLib = sampleLibrary(sample)

        for note in tmpNotes:
            n = note[0]
            if(n not in freList):
                print('note not found:', n)
                n = ''
            metre = note[1]
            # offset situation
            if(len(note) > 2): # chord situation
                cTime += noteTime * note[2]
            amp = globalAmp
            if(n == ''):
                amp = 0
            elif(sample == None):
                #track = wav.sinWave(freList[n],noteTime * metre, amp = amp)
                track = sampleLib.getTrack(n, noteTime * metre, amp)
                wav.bufferInsert(int(cTime * wav.sampleRate), track)
            else: # sample style music situation!
                track = sampleLib.getTrack(n, noteTime * metre, amp)
                wav.bufferInsert(int(cTime * wav.sampleRate), track)
            cTime += noteTime * metre

    wav.writeBuffer(path)
    wav.printInfo()
    return wav


# return the notes list based on self defined notes txt file
def parseNotesList(path):
    f = open(path, "r", encoding='utf-8')
    lines = f.readlines()
    ans = []
    for line in lines:
        tokens = line.split(',')
        note = ['',0]
        if(len(tokens) >= 2):
            note[0] = tokens[0]
            note[1] = float(tokens[1])
            if(len(tokens) >= 3):
                note.append(float(tokens[1]))
            ans.append(note)
    return ans

# calculate the duration (in second) of the give notes list:
def calculateDuration(nList, noteTime):
    cTime = 0 
    for note in nList:
        metre = note[1]
        if(len(note) > 2): # chord situation
            cTime += noteTime * note[2]
        cTime += noteTime * metre
    return cTime


# calculate the absolute time (in second) of the give notes list:
# output format: [['1', timeStart, timeDuration, staff, amp]   ....]
def calculateAbsTime(nList, noteTime, staff, amp):
    ans = []
    cTime = 0 
    for note in nList:
        metre = note[1]
        if(len(note) > 2): # chord situation
            cTime += noteTime * note[2]
        startTime = cTime
        durTime =  noteTime * metre
        if(note[0] != ''):
            ans.append([note[0], startTime, durTime, staff, amp])
        cTime += durTime
    return ans

# generate music based on note list
def generateMusicBasedOnList(path, notes,  noteTime = 0.8, globalAmp = 0.1,
                             sample: AzWav = None):
    print(notes)
    freList = getFreDictionary()
    cTime = 0
    wav = AzWav()
    for note in notes:
        n = note[0]
        if(n not in freList):
             n = ''
        metre = note[1]
        # offset situation
        if(len(note) > 2): # chord situation
            cTime += noteTime * note[2]
        amp = globalAmp
        amp = globalAmp
        if(n == ''):
            amp = 0
            track = [0] * int(noteTime * metre * wav.sampleRate)
            wav.insert(int(cTime * wav.sampleRate), track)
        elif(sample == None):
            track = wav.sinWave(freList[n],noteTime * metre, amp = amp)
            wav.insert(int(cTime * wav.sampleRate), track)
        else: # sample style music situation!
            track = sample.pitchedTrack(261.6256,
                freList[n], amp = amp, duration = noteTime * metre + 1.5,
                        fadeEnd = 1.5)
            wav.insert(int(cTime * wav.sampleRate), track)
        #wav.primaryTrack += wav.sinWave(freList[n],noteTime * metre, amp = amp)
        cTime += noteTime * metre
    wav.write(path)
    wav.printInfo()



# generate music based on absolute time note list
def generateMusicBasedOnAbsList(path, notes, useSamLibrary: sampleLibrary = None, 
                                globalAmp = -1):
    freList = getFreDictionary()
    cTime = 0
    if(notes == None or len(notes) < 1):
        return
    maxDuration = 0
    for note in notes:
        cTime = note[1]
        dur = note[2]
        if(cTime + dur > maxDuration):
            maxDuration = cTime + dur
    
    wav = AzWav()
    wav.bufferArea(int(maxDuration * wav.sampleRate))
    if(useSamLibrary == None):
        useSamLibrary = sampleLibrary(None)
    sampleLib = useSamLibrary
    for note in notes:
        n = note[0]
        if(n not in freList):
            n = ''
            continue
        cTime = note[1]
        dur = note[2]
        noteStaff = note[3]
        amp = note[4]
        if(globalAmp >= 0):
            amp = globalAmp
        track = sampleLib.getTrack(n, dur, amp)
        wav.bufferInsert(int(cTime * wav.sampleRate), track)
        
    wav.writeBuffer(path)
    wav.printInfo()
    return wav





# return a list with [('1',metre,minusTimeInMetre)]
# voice range from 1,2.... to 8
def parseMusicXML(path, staff = -1, audioInfo = dict()):
    f = open(path, "r", encoding='utf-8')
    lines = f.readlines()
    tmpNote = ['',0]
    ans = []
    prevDuration = 0
    alt = ''
    tmpStaff = 0
    tmpVoice = 0
    measureNum = -1
    mesaureStart = 0
    mesaureRealStart = 0
    measureBeatsRaw = 4
    measureBeats = 4
    measureBeatDuration = 1 # assume 1/4 note is 1 
    currentBeat = 0
    prevNoteVoice = 0
    division = 4
    staffs = []
    print('target staff:',staff)
    for line in lines:
        line = line.strip()
        if('<note' in line):
            tmpNote = ['',0]
            tmpStaff = 0
            tmpVoice = 0
            alt = ''
        elif('<chord/>' in line):
            tmpNote.append(-1 * prevDuration)
        elif('<beats>' in line):
            line = line.replace('<beats>','')
            line = line.replace('</beats>','')
            measureBeatsRaw = int(line)
            measureBeats = measureBeatsRaw * measureBeatDuration
        elif('<beat-type>' in line):
            line = line.replace('<beat-type>','')
            line = line.replace('</beat-type>','')
            measureBeatDuration = 4 / int(line)
            measureBeats = measureBeatsRaw * measureBeatDuration
        elif('<step>' in line):
            line = line.replace('<step>','')
            line = line.replace('</step>','')
            tmpNote[0] +=line
        elif('<per-minute>' in line):
            line = line.replace('<per-minute>','')
            line = line.replace('</per-minute>','')
            if(len(line) > 0 ):
                if('bpm' not in audioInfo):
                    audioInfo['bpm'] = int(line)
        elif('<sound tempo="' in line):
            line = line.replace('<sound tempo="','')
            line = line.replace('"/>','')
            if('bpm' not in audioInfo):
                audioInfo['bpm'] = float(line)
        elif('<octave>' in line):
            line = line.replace('<octave>','')
            line = line.replace('</octave>','')
            tmpNote[0] +=line   
        elif('<staff>' in line):
            line = line.replace('<staff>','')
            line = line.replace('</staff>','')
            tmpStaff =int(line)   
            if(tmpStaff not in staffs):
                staffs.append(tmpStaff)
                audioInfo['staffs'] = staffs
        elif('<voice>' in line):
            line = line.replace('<voice>','')
            line = line.replace('</voice>','')
            tmpVoice =int(line)   
        elif('<divisions>' in line):
            line = line.replace('<divisions>','')
            line = line.replace('</divisions>','')
            division =int(line) 
        elif('<duration>' in line):
            line = line.replace('<duration>','')
            line = line.replace('</duration>','')
            tmpNote[1] =1 *float(line) / division  
            prevDuration =1 * float(line)  / division
        elif('<alter>' in line):
            line = line.replace('<alter>','')
            line = line.replace('</alter>','')
            #tmpNote[0] ='a'+line +'_' + tmpNote[0] 
            #print('Added alter info:', line)
            if(int(line) > 0):
                alt = '#' * int(line)
            elif(int(line) < 0):
                alt = 'b' * abs(int(line))
        elif('</note>' in line):
            tmpNote[0] += alt
            # close note and write
            tmpNote[0] = convertNote(tmpNote[0])
            if( staff >= 0 and tmpStaff != staff and 
                not (tmpStaff == 0)  ):
                tmpNote = ['',0]
            else:
                #print("Note:",tmpNote[0],"\tDur:",tmpNote[1])
                currentBeat += tmpNote[1]
                if(len(tmpNote) > 2):
                    currentBeat += tmpNote[2]
                '''
                if(prevNoteVoice != 0 and prevNoteVoice != tmpVoice):
                    if(currentBeat < mesaureStart):
                        ans.append(tmpNote['',mesaureStart -currentBeat ])
                        currentBeat = mesaureStart
                    elif(currentBeat > mesaureStart):
                        if(len(tmpNote) > 2):
                            tmpNote[2] -= currentBeat - mesaureStart
                        else:
                            tmpNote.append(-1 * (currentBeat - mesaureStart))
                        currentBeat = mesaureStart
                '''
                # out of measure problem!
                if(currentBeat > mesaureStart + measureBeats):
                    if(len(tmpNote) > 2):
                        tmpNote[2] -= measureBeats
                    else:
                        tmpNote.append(-1 * (measureBeats))
                    currentBeat -= measureBeats
                ans.append(tmpNote[:])
                prevNoteVoice = tmpVoice
                
            #step part   
        elif('</measure>' in line): # one measure ends
            if(mesaureStart != 0):
                # step in first beat
                mesaureStart += measureBeats
                if(currentBeat < mesaureStart):
                    ans.append(['',mesaureStart -currentBeat ])
                    currentBeat = mesaureStart
                elif(currentBeat > mesaureStart):
                    ans.append(['',0,mesaureStart -currentBeat ])
                    currentBeat = mesaureStart
            else:
                mesaureStart += measureBeats
                 # move currentBeat to mesaureStart instead
                if(currentBeat < mesaureStart):
                    #ans.append(['',mesaureStart -currentBeat ])
                    mesaureRealStart = currentBeat
                    mesaureStart = currentBeat
                elif(currentBeat > mesaureStart):
                    ans.append(['',0,mesaureStart -currentBeat ])
                    currentBeat = mesaureStart
        elif('</part>' in line): # one measure ends
            pass
            mesaureStart = 0
            if(currentBeat < mesaureStart):
                ans.append(['',mesaureStart -currentBeat ])
                currentBeat = mesaureStart
            elif(currentBeat > mesaureStart):
                ans.append(['',0,mesaureStart -currentBeat ])
                currentBeat = mesaureStart
                

    return ans
    #print(ans)
    #print('End')


# MISCELLANOUS REGION
# print the error message. 
if (__name__ == '__main__'):
    print('Error! This is just a library file!')
    print('You should not directly run my library file.')
    print('Please run ProgramGUI.py instead!')