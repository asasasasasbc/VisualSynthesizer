#######################################################################
# This is the main file of the Visual Synthesizer 
# Visual synth Verion: TP3
# Author: Alan Zhang
# [Exclusively wrote for 112 term project]
#######################################################################


# module manager for easier importing simpleaudio!
import module_manager
# avoid finding the module I wrote!
module_manager.ignore_module('AzWavLib')
module_manager.ignore_module('AzXmlLib')
module_manager.review()

import sys
import time




# Background image:
# bg.jpg came from https://www.goodfreephotos.com/astrophotography/starry-milky-way-galaxy.jpg.php

from cmu_112_graphics import *

import zipfile # bult-in zip file function
import random
import json # used to save the configuration easily.

# import my own wav file library!
# wav library is already too long, so I separated the code from Program.py
from AzWavLib import *
from AzXmlLib import *

# External module from https://pypi.org/project/simpleaudio/
# pip install simpleaudio
import simpleaudio as sa

# basic image handling.
import PIL
from PIL import Image, ImageFilter

from tkinter import messagebox, simpledialog, filedialog, colorchooser 

# from 112 course note get rgb string for tkinter
def rgbString(r, g, b):
    # Don't worry about the :02x part, but for the curious,
    # it says to use hex (base 16) with two digits.
    return f'#{r:02x}{g:02x}{b:02x}'

# get rgb string from list L
def rgbList(L):
    # Don't worry about the :02x part, but for the curious,
    # it says to use hex (base 16) with two digits.
    r,g,b = L[0],L[1],L[2]
    return f'#{r:02x}{g:02x}{b:02x}'

# read the custom defined synnote file.
def readSynnoteFile(app, path):
    f = open(path, "r", encoding='utf-8')
    lines = f.readlines()
    globalAmp = 0.1
    globalStaff = 1
    globalMetre = 1 # time scale per time unit.
    absNotes = []
    currentTime = 0
    prevTime = 0
    for line in lines:
        notePitch = ''
        noteStart = 0
        noteDur = 1
        noteAmp = globalAmp
        noteStaff = globalStaff
        if('#' in line[0:1]): # comment section
            continue
        elif(line.strip() == ''):
            continue
        elif('AMP:' in line):
            line = line.replace('AMP:','')
            line = line.strip()
            noteAmp = float(line)
        elif('METRE:' in line):
            line = line.replace('METRE:','')
            line = line.strip()
            globalMetre = float(line)
        elif('STAFF:' in line):
            line = line.replace('STAFF:','')
            line = line.strip()
            noteStaff = int(line)
        else:
            words = line.split(',')
            if(len(words) >= 4):
                noteStaff = int(words[3].strip())
            if(len(words) >= 5):
                noteAmp = int(words[4].strip())
            if(len(words) >= 3):
                notePitch = words[0].strip()
                noteStart = currentTime
                noteDur = 1
                
                if(words[1].strip().isdigit()):
                    noteStart = float(words[1].strip()) * globalMetre
                elif('chord' in words[1].strip()):
                    noteStart = prevTime
                
                noteDur = float(words[2].strip()) * globalMetre
                
                n = [notePitch,noteStart,noteDur,noteStaff,noteAmp]
                absNotes.append(n)
                prevTime = noteStart
                currentTime = noteStart + noteDur

    app.absNotesList = sorted(absNotes,key=lambda l:l[1])
    clearRenderedTrack(app) # clear prerendered sound.
    app.musicDuration = absNotes[-1][1] + absNotes[-1][2]
    app.inMusicTime = 0
    app.i = 0 
    pauseMusic(app, False)
    app.startTime = time.time()        
        
# save the config.ini file
def saveConfig(app):
    app.config.exportJsonFile('config.ini')

# reset all settings to default
def resetConfig(app):
    app.config = Config()
    app.config.applyRenderScale(app.renderScale)
    # initlize required data.
    r,g,b = app.config.textColor
    app.textColorStr = rgbString(r,g,b)
    refreshBg(app)
    

# refresh the background picture
def refreshBg(app):
    # initliaze the background picture
    app.bgPicNp = None
    app.bgImg = None
    if(app.config.bgPicture):
        if(os.path.exists(app.config.bgPath)):
            app.bgImg = Image.open(app.config.bgPath)
            tmpImg = app.bgImg.resize((app.width, app.height), Image.NEAREST)
            app.bgPicNp = np.array(tmpImg.getdata(), dtype=np.uint8).reshape(tmpImg.height, tmpImg.width, 3)

# pop a window to read a new config.ini file
def readNewConfig(app):
    pauseMusic(app, True)
    types = (('Config file','*.ini'),('all files','*.*'))
    iniPath = filedialog.askopenfilename(initialdir=os.getcwd(),defaultextension=".ini",
              title='Select the skin configuration file: ',filetypes =types)
    if(not os.path.exists(iniPath)):
        return
    app.config.loadJsonFile(iniPath)
    app.config.applyRenderScale(app.renderScale)

    # initlize required data.
    r,g,b = app.config.textColor
    app.textColorStr = rgbString(r,g,b)

    # initliaze the background picture
    refreshBg(app)

    messagebox.showinfo('OK', 'New configuration file loaded.')


# clear all the rendered music that is playing:
def clearRenderedTrack(app):
    if(app.saObj != None):
        app.saObj.stop()
        app.saObj = None
    app.renderedTrack = None 
    pass
# read new music XML file
def readNewFile(app):
    pauseMusic(app, True)
    path = 'dummy.wav'
    xmlPath = 'xml/zuGuo.xml'
    app.pressedKeys = dict()
    #clear the tmp file first:
    for fileName in os.listdir(os.path.curdir):
        if fileName == "tmp":
            for fileNameTmp in os.listdir(os.path.curdir + '/' + fileName):
                os.remove(os.path.curdir + '/tmp/' + fileNameTmp)
    
    types = (('Music XML file','*.xml'),('Music XML file','*.musicxml'),
               ('Music XML file','*.mxl'),
               ('Custom defined music note','*.synnote'), ('all files','*.*'))
    
    xmlPath = filedialog.askopenfilename(initialdir=os.getcwd(),defaultextension=".xml",
              title='Select music xml file you want to play: ',filetypes =types)
    print(xmlPath)
    # if the music mxl(zipped ver) is a compressed file:
    if(xmlPath.endswith('.mxl')):
        app.fileName = os.path.split(xmlPath)[1]
        archive = zipfile.ZipFile(xmlPath, "r")
        targetXML = ""
        for fileName in archive.namelist():
            if(fileName.endswith("xml") and (not fileName.startswith("META-INF/"))):
                targetXML = fileName
        print(archive.namelist())
        print(targetXML)
        if(targetXML == ""):
            xmlPath = ''
        else:
            archive.extract(targetXML,path="tmp")
            xmlPath = "tmp/" + targetXML

    elif(xmlPath == ''):
        app.absNotesList = []
        app.inMusicTime = 0
        app.musicDuration = 0.001
        app.i = 0 
        
        app.xmlPath = ''
        app.mode = 'home'
        app.fileName = ''
        clearRenderedTrack(app) # clear prerendered sound.
        pauseMusic(app, True)
        return
    elif(xmlPath.endswith('.synnote')):
        app.fileName = os.path.split(xmlPath)[1]
        app.absNotesList = []
        app.inMusicTime = 0
        app.musicDuration = 0.001
        app.i = 0 
        app.xmlPath = xmlPath
        readSynnoteFile(app, xmlPath)
        app.mode = 'music'
        clearRenderedTrack(app) # clear prerendered sound.
        pauseMusic(app, False)
        return
    else:
        app.fileName = os.path.split(xmlPath)[1]

    app.xmlPath = xmlPath
    

    absNotes = []
    generateBaseOnXml(path, xmlPath, noteTime = 1, 
                      sampleList = [None, None, None],
                      globalAmpList = [app.globalAmp] * 3,
                      calculateNoteTime = True,
                      outNoteList = absNotes,
                      )
    app.absNotesList = sorted(absNotes,key=lambda l:l[1])
    app.musicDuration = absNotes[-1][1] + absNotes[-1][2]
    app.inMusicTime = 0
    app.i = 0 
    pauseMusic(app, False)
    app.startTime = time.time()
    clearRenderedTrack(app) # clear prerendered sound.
    app.mode = 'music'

# export rendered wav file
def exportWavFile(app):
    if(app.xmlPath == ''):
        messagebox.showinfo('OK', 'Nothing to save!')
        return
    pauseMusic(app, True)
    types = (("Wav sound files", "*.wav"),("All Files", "*.*") )
    filePath = filedialog.asksaveasfilename(initialdir=os.getcwd(),initialfile = app.fileName + '.wav',defaultextension=".wav", title='Export high precision wav file:',filetypes =types)
    if(filePath == '' or filePath == None):
        return
    if(app.xmlPath.endswith('.synnote')):
        app.renderedTrack = generateMusicBasedOnAbsList(filePath, 
                            app.absNotesList, app.samLib, app.globalAmp)
        messagebox.showinfo('OK', 'Wav file saved.')
        return
    print('File path:', filePath)
    print('XML file path:', app.xmlPath)
    app.renderedTrack = generateBaseOnXml(filePath, app.xmlPath, noteTime = 1, 
                      sampleList = [None]*10,
                      globalAmpList = [app.globalAmp] * 10,
                      calculateNoteTime = True,
                      outNoteList = None,
                      useSamLibrary = app.samLib
                      )


    messagebox.showinfo('OK', 'Wav file saved.')

# read the sin wave intrument
def readSinSample(app):
    pauseMusic(app, True)
    app.samLib = sampleLibrary(None)
    app.globalAmp = 0.125
    app.maxAmp = app.globalAmp  * 2
    clearRenderedTrack(app) # clear prerendered sound.
    messagebox.showinfo('OK', 'Sin tone loaded.')

# read custom defined .wav file as intrument sound
def readNewSample(app):
    pauseMusic(app, True)
    messagebox.showwarning('OK', 'Caution! Using non-default instrument may cause some lag issue.')
    types = (('Wav sound files','*.wav'),('all files','*.*'))
    path = filedialog.askopenfilename(initialdir=os.getcwd(), title='Select instrument C4 .wav file you want to use: ',filetypes =types )
    if(path == ''):
        return

    else:
        wavFile = AzWav()
        wavFile.read(path)
        app.samLib.setSampleWav(wavFile)
        msgBox = messagebox.askquestion ('Additional info','Do you want add C5 .wav file for this intrument?',icon = 'warning')
        if(msgBox == 'yes'):
            path = filedialog.askopenfilename(initialdir=os.getcwd(), title='Select instrument C5 .wav file you want to use: ',filetypes =types )
            if(path != ''):
                wavFileC5 = AzWav()
                wavFileC5.read(path)
                app.samLib.sampleC5 = wavFileC5
                msgBox = messagebox.askquestion ('Additional info','Do you want add C6 .wav file for this intrument?',icon = 'warning')
                if(msgBox == 'yes'):
                    path = filedialog.askopenfilename(initialdir=os.getcwd(), title='Select instrument C6 .wav file you want to use: ',filetypes =types )
                    if(path != ''):
                        wavFileC6 = AzWav()
                        wavFileC6.read(path)
                        app.samLib.sampleC6 = wavFileC6
        
        app.samLib.prepare()
        app.globalAmp = 0.5
        app.maxAmp = app.globalAmp  * 2
        clearRenderedTrack(app) # clear prerendered sound.
        messagebox.showinfo('OK', 'New intrument .wav loaded.')
    pauseMusic(app, True)

# read the grand piano instrument sound
def readGrandPiano(app):
    pauseMusic(app, True)
    messagebox.showwarning('OK', 'It may take a few seconds to load this tone.')
    path = 'sample/GrandPianoC4.wav'
    wavFile = AzWav()
    wavFile.read(path)
    app.samLib.setSampleWav(wavFile)
    path = 'sample/GrandPianoC5.wav'
    wavFileC5 = AzWav()
    wavFileC5.read(path)
    app.samLib.sampleC5 = wavFileC5
    path = 'sample/GrandPianoC6.wav'
    wavFileC6 = AzWav()
    wavFileC6.read(path)
    app.samLib.sampleC6 = wavFileC6
    app.samLib.prepare()
    app.globalAmp = 0.5
    app.maxAmp = app.globalAmp  * 2
    clearRenderedTrack(app) # clear prerendered sound.
    messagebox.showinfo('OK', 'Grand piano instrument loaded.')

# used to define some basic 2d particle effect
class Particle(object):
    # contructor, define basic position, velocity value
    def __init__(self, x, y, vx, vy, color, duration):
        self.x : float = x
        self.y : float = y
        self.vx : float = vx
        self.vy : float = vy
        self.timeStart : float = time.time() 
        self.timeEnd : float = time.time() + duration
        self.color = color
        self.prevTime = time.time()
    # update particle position and draw on the numpy data.
    def update(self, data, glowMask, glowDis, glowRatio):
        deltaTime = time.time() - self.prevTime
        self.prevTime = time.time()
        self.x += self.vx * deltaTime
        self.y += self.vy * deltaTime
        r,g,b = self.color
        lifeSpan = (time.time() - self.timeStart) / (self.timeEnd - self.timeStart)

        applyGlowMask(data,int(self.x), int(self.y), r, g, b, glowMask,glowDis, glowRatio * (1 - lifeSpan))
    # check if particle expired or not
    def expired(self):
        return  time.time()  > self.timeEnd


# used to define some visual configuration of the program.
class Config(object):
    # constructor
    def __init__(self):
        # maximum not counts on the screen.
        self.noteMaxCount = 75
        # default note color = note: cyan
        self.noteColor = (156,217,229)
        # default note black key color: light blue
        self.noteBlackColor = (75,174,191)
        
        # UI text color
        self.textColor = (255,255,255)
        self.textColor2 = (255,255,255) 

        # show key board or not
        self.showKeyboard = True

        # white keyboard key color
        self.keyBorder = True
        self.whiteKeyColor = (255,255,255)
        # black keyboard key color 
        self.blackKeyColor = (10,10,10)
        # white keyboard key pressed color
        self.whiteKeyPressedColor = (156,217,229)
        # black keyboard key pressed color 
        self.blackKeyPressedColor = (75,174,191)


        # define note color have a fade effect or not.
        self.noteFade = False
        self.noteFadeRatio = 0.316
        # define if note has border or not.
        self.noteBorder = False

        # check whether note fade in or not
        self.noteFadeIn = True

        # note key glow or not (time consuming!)
        self.noteGlow = True
        self.noteGlowDis = 15 
        self.noteGlowRate = -0.2

        # pressed key glow or not.
        self.pressedGlow = True
        self.pressedGlowDis = 20 
        self.pressedGlowRate = 1
        self.pressedGlowTime = 0.3

        # keyboard color fade or not.
        self.whiteKeyFade = True
        self.whiteKeyFadeRate = -0.1

        self.blackKeyFade = True
        self.blackKeyFadeRate = -1


        # SUPER TIME CONSUMING GORGEOUS PARTICLE SYSTEM
        self.particleSystem = True
        self.particleLimit = 5 # maximum 10 particles
        self.particleColor = 255,255,255
        self.particleRadius = 10 
        self.particleGlowRate = 0.25
        self.particleDur = 1
        self.particleVy = 10 
        self.particleVx = 20 

        # back ground color.
        self.bgColor = (56,84,99)
        # if set to true, it will load bg.png file.
        self.bgPicture = True
        self.bgPath = 'bg.jpg'
    # apply the render scale (pixelize effect)
    def applyRenderScale(self, renderScale):
        self.noteGlowDis = 15 // renderScale
        self.pressedGlowDis = 20 // renderScale
        self.particleRadius = 10  // renderScale
        self.particleVy = 10 // renderScale
        self.particleVx = 20 // renderScale
    # load a config.ini file
    def loadJson(self, dict):
        if(type(dict) == type('')):
            dict = json.loads(dict)
        for key,val in dict.items():
            setattr(self, key, val)
    # load a config.ini file
    def loadJsonFile(self, path):
        fp = open(path,'r')
        dict = json.load(fp)
        for key,val in dict.items():
            setattr(self, key, val)
        fp.close()
        return
    # export a config.ini file
    def exportJson(self):
        return json.dumps(self.__dict__, sort_keys=False, indent=2)
    # export the config.ini file
    def exportJsonFile(self, path):
        fp = open(path, 'w')
        json.dump(self.__dict__, fp, sort_keys=False, indent=2)
        fp.close()
        return



# initialize the model
def appStarted(app):
    app.absNotesList =  [['1',0,1,1,0.1],['1#',1,1,1,0.1],['3',2,1,1,0.1]            ]
    app.i = 0 # next note to play index.
    app.readOnStart = False

    app.mouseX = 0
    app.mouseY = 0

    app.version = 'Version TP3'

    app.mode = 'home' # home or music or instrument or setting or about
    app.startTime = time.time()
    app.timerDelay = 1000 // 40

    app.renderScale = 1 #it will boost the speed of rendering image.
    
    app.fileName = ''
    app.hideUI = False

    app.renderedTrack: AzWav = None
    # app's simple audio object for playing rendered sound
    app.saObj = None
    app.config : Config = Config()
    
    # if config file exists, load config file:
    configPath = 'config.ini'
    if(os.path.exists(configPath)):
        app.config.loadJsonFile(configPath)
    else:
        app.config.exportJsonFile(configPath)
    app.config.applyRenderScale(app.renderScale)

    # initlize required data.
    r,g,b = app.config.textColor
    app.textColorStr = rgbString(r,g,b)

    app.btnColorStr = rgbString(149,209,207)
    app.btnHoverColorStr = rgbString(47,139,178)
    app.btnH = 23
    app.btnFont = 'Arial 12'

    # initliaze the background picture
    app.bgPicNp = None
    app.bgImg = None
    if(app.config.bgPicture):
        if(os.path.exists(app.config.bgPath)):
            app.bgImg = Image.open(app.config.bgPath)
            tmpImg = app.bgImg.resize((app.width, app.height), Image.NEAREST)
            app.bgPicNp = np.array(tmpImg.getdata(), dtype=np.uint8).reshape(tmpImg.height, tmpImg.width, 3)

    app.titleImg = Image.open('title.png').resize((app.width, app.height), Image.ANTIALIAS)
    app.musicImg = Image.open('music.png').resize((app.width, app.height), Image.ANTIALIAS)
    # initialize the np array to avoid memory leak issue (meybe?)
    iw,ih = app.width, app.height
    app.imgNp : np.ndarray = np.ones((ih//app.renderScale + 200, iw//app.renderScale + 200, 3), dtype=np.uint8)

    app.renderBeforeDuration = 0.2 # render notes 0.2s before.
    app.renderAfterDuration = 7
    app.paused = True
    app.timerFiredTime = 0
    app.inMusicTime = 0
    app.globalAmp = 0.125
    app.maxAmp = app.globalAmp  * 2
    app.img =  None




    # default glow mask for pressed keys
    app.glowMask = createGlowMask(0, 0,app.config.pressedGlowDis)
    app.particleMask =  createGlowMask(0, 0,app.config.particleRadius, power = 0.5)
    app.particles = []

    app.pressedKeys = dict()

    app.xmlPath = ''

    app.cx = (app.width / 2) / app.renderScale
    app.cy = (app.height * 0.75) / app.renderScale
    app.notesCount = 56
    app.noteKeyWidth = (app.width  / app.notesCount) / app.renderScale
    app.noteKeyHeight = (app.height / app.renderScale * 0.25) - 3 #100
    app.noteHeight = 50 / app.renderScale # 50 pixels per second

    app.samLib = sampleLibrary(None)

    app.absNotesList = []
    app.inMusicTime = 0
    app.musicDuration = 0.001
    app.i = 0 
    pauseMusic(app, True)
    app.xmlPath = ''

    app.working = False # check if timer fired triggered or not.

    if(app.readOnStart == True):
        readNewFile(app)


# timer fired event
def timerFired(app):
    if(app.working == True):
        print('Timer fired overlapped!!! Error!!!')
        return
    app.working = True
    iw,ih = app.width, app.height

    data = app.imgNp
    data.fill(1)
    if(type(app.bgPicNp) == type(None)):

        data[:,:,0].fill(app.config.bgColor[0]) # get white page.
        data[:,:,1].fill(app.config.bgColor[1])
        data[:,:,2].fill(app.config.bgColor[2])
    else:
        tmpW = len(app.bgPicNp[0])
        tmpH = len(app.bgPicNp)
        data[100:100+tmpH,100:100+tmpW] = app.bgPicNp[:tmpH,:tmpW]
    # draw the notes in numpy array.
    if(app.mode == 'music'):
        drawNotesNp(app, data)
        drawKeyBoardNp(app, data)
        drawParticlesNp(app,data)
    else:
        drawKeyBoardNp(app, data, pressEffect = False)
    app.img = Image.fromarray(data[100:-100,100:-100])

    app.timerFiredTime = time.time()
    if(app.paused):
        app.startTime =  app.timerFiredTime - app.inMusicTime
        app.working = False
        return
    else:# respond to timer events
        app.inMusicTime = app.timerFiredTime -   app.startTime 
        if(app.inMusicTime >= app.musicDuration + 1):
            app.inMusicTime =  app.musicDuration + 1
            pauseMusic(app, True)
            app.working = False
            return

    frequency = 44100
    channels = 1
    bytesPerSample = 2
    # play the sound here!
    ct = app.timerFiredTime
    absNotes = app.absNotesList 
    startTime = app.startTime

    

    if(ct - app.startTime < app.musicDuration):
        ct = time.time()
        while(app.i < len(absNotes) and absNotes[app.i][1] < ct - startTime):
            pitch = absNotes[app.i][0]
            dur = absNotes[app.i][2]
            amp = absNotes[app.i][4]
            # use global amp to override the note's value.
            amp = app.globalAmp
            if(pitch == '' or dur < 0.001):
                app.i += 1
                continue
            # if we used rendered track, then don't need real time play back!
            if(app.renderedTrack == None):
                audio = app.samLib.getTrack(pitch,dur,amp).astype(np.int16)
                try:
                    play_obj = sa.play_buffer(audio, channels, bytesPerSample,frequency)
                except:
                    print("Too many notes played at same time! This note is dropped!")
            pitchIndex = pitchToIndex(pitch)
            endTime  = absNotes[app.i][1] + dur
            app.pressedKeys[pitchIndex] = (endTime,dur)
            if(app.config.particleSystem):
                vy = -app.config.particleVy
                vx = (1 - random.random() * 2) * app.config.particleVx
                noteId, noteBlack = pitchToIndex(pitch)
                noteWidth = app.noteKeyWidth
                leftX = app.cx + noteId * noteWidth 
                rightX = leftX + noteWidth 
                
                if(noteBlack > 0):
                    leftX += noteWidth * 0.75 
                    rightX = leftX + noteWidth * 0.5
                elif(noteBlack < 0):
                    leftX -= noteWidth * 0.25 
                    rightX = leftX + noteWidth * 0.5
                center = (leftX + rightX) / 2
                p = Particle(center + 100,app.cy + 100,vx,vy,app.config.particleColor, app.config.particleDur)
                if(len(app.particles) < app.config.particleLimit):
                    app.particles.append(p)
            app.i+=1

    app.working = False

# play or pause the music
def pauseMusic(app, val):
    if(app.paused != val):
        if(app.renderedTrack != None):
            if(val == True and app.saObj != None):
                app.saObj.stop()
            elif(val == False):
                wav:AzWav = app.renderedTrack
                channels = 1
                bytesPerSample = 2
                frequency = wav.sampleRate
                start = max(int(app.inMusicTime  * frequency),0)
                audio = wav.buffer[start:].astype(np.int16)    
                if(len(audio > 0)):
                    try:
                        play_obj = sa.play_buffer(audio, channels, bytesPerSample,frequency)
                        app.saObj = play_obj
                    except:
                        print("Too many notes played at same time! This note is dropped!")
        if(val == False):       
            JumpToSecondInPause(app, app.inMusicTime)
        app.paused = val
        

# return normal color if mouse in within the (x0,y0,x1,y1) rectangle
# otherwise return hoverColor.
def getBtnColor(app, x0,y0,x1,y1, normalColor, hoverColor):
    if(x0 <= app.mouseX < x1 and y0 <= app.mouseY < y1):
        return hoverColor
    return normalColor

# return True if mouse if mouse in within the (x0,y0,x1,y1) rectangle
# otherwise return False
def inArea(mouseX, mouseY, x0, y0,x1,y1):
    return (x0 <= mouseX < x1 and y0 <= mouseY < y1)

# event triggered when mouse is cliked in home page
def homeClicked(app, mouseX, mouseY):
    cx, cy = app.cx, app.cy - 120
    btnH = app.btnH
    x0,x1 =  cx - 150, cx + 150

    btnY = cy + 1 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # load music xml
        pauseMusic(app, True)
        readNewFile(app)

    btnY = cy + 2 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # instrument settings
        pauseMusic(app, True)
        app.mode = 'instrument'

    btnY = cy + 3 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # settings
        pauseMusic(app, True)
        app.mode = 'setting'

    btnY = cy + 4 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # about
        pauseMusic(app, True)
        app.mode = 'about'
# hone page's redraw all function
def homeRedrawAll(app, canvas):
    cx, cy = app.cx, app.cy - 120
    btnH = app.btnH
    font = app.btnFont
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr

    canvas.create_image(0,0,anchor = 'nw', pilImage=app.titleImg, 
                        state="normal")

    btnY = cy + 1 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
            text = f'[Load MusicXML File]', font = font)
    
    btnY = cy + 2 * btnH
    filColor = getBtnColor(app,cx - 150,btnY,  cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
            text = f'[Playback Instruments]', font = font)
    
    btnY = cy + 3 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
            text = f'[Settings]', font = font)
    
    btnY = cy + 4 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
            text = f'[About]', font = font)

    
    pass
# event triggered when mouse is cliked in music page
def musicClicked(app, mouseX, mouseY):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr
    
    btnY = 10
    y0, y1 =  btnY, btnY + btnH

    cx = app.width / 8 + 50
    x0,x1 =  cx - 50, cx + 50

    if(mouseY > app.height * 0.25 or app.hideUI):
        app.hideUI = not app.hideUI
        return

    cx =0.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # load new
        pauseMusic(app, True)
        readNewFile(app)
    #text = 'Load', font = font)

    cx =1.2* app.width / 8 + 10
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # export
        exportWavFile(app)
    #text = 'Export', font = font)

    cx =2.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # instrument
        pauseMusic(app, True)
        app.mode = 'instrumentFromMusic'
    #text = 'Instrument', font = font)

    cx =3.2* app.width / 8 + 20
    x0,x1 =  cx-40, cx + 40
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # <<
        JumpToSecond(app, app.inMusicTime - 5)
    #text = '<<', font = font)

    cx =4.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # pause/play
        pauseMusic(app, not app.paused)
        #app.paused = not app.paused
    #text = 'Play/Pause', font = font)

    cx =5.2* app.width / 8 + 20
    x0,x1 =  cx-40, cx + 40
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # >>
        JumpToSecond(app, app.inMusicTime + 5)
    #text = '>>', font = font)

    cx =6.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # replay
        app.startTime =  time.time() 
        app.inMusicTime = 0
        app.i = 0
        app.pressedKeys = dict()
        
    #text = 'Replay', font = font)

    cx =7.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # load music xml
        pauseMusic(app, True)
        app.mode = 'home'
    #text = 'Home', font = font)
# music page's redraw all function
def musicRedrawAll(app, canvas):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr

    if(app.hideUI):
        return

    # Draw the background transition
    canvas.create_image(0,0,anchor = 'nw', pilImage=app.musicImg, 
                        state="normal")
    # Draw the name.
    displayName = app.fileName
    if(app.renderedTrack != None):
        displayName = '[Rendered] ' + app.fileName
    canvas.create_text(20, 45, anchor = 'nw',fill =  textColor,
            text = displayName)
    # Draw the time length
    canvas.create_text(app.width - 20, 45, anchor = 'ne',fill =  textColor,
            text = f'{int(min(app.inMusicTime,app.musicDuration))} / {int(app.musicDuration )}s')
    # Draw the progress bar
    x0,x1 = 20, app.width - 20
    y0,y1 = 38,40
    canvas.create_rectangle(x0,y0,x1,y1, fill = 'grey', width = 0)

    pct = min(app.inMusicTime,app.musicDuration) / (app.musicDuration )
    pct = max(0, pct)
    canvas.create_rectangle(x0,y0,x0 + (x1 - x0) * pct,y1, fill = 'white', width = 0)

    cx =0.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Load', font = font)

    cx =1.2* app.width / 8 + 10
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Export', font = font)

    cx =2.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Instrument', font = font)

    cx =3.2* app.width / 8 + 20
    x0,x1 =  cx-40, cx + 40
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = '<<', font = font)

    cx =4.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Play/Pause', font = font)

    cx =5.2* app.width / 8 + 20
    x0,x1 =  cx-40, cx + 40
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = '>>', font = font)

    cx =6.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Replay', font = font)

    cx =7.2* app.width / 8 + 20
    x0,x1 =  cx-50, cx + 50
    y0,y1 = 10, 10 + btnH
    fillColor = getBtnColor(app, x0, y0, x1, y1, normalColor, hoverColor)
    canvas.create_text(cx, y0, anchor = 'n', fill =  fillColor,
    text = 'Home', font = font)

# event triggered when mouse is cliked in instrument page
def instrumentClicked(app, mouseX, mouseY):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr
    x0,x1 =  cx - 150, cx + 150

    btnY = cy + 4 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # sinwave
        pauseMusic(app, True)
        readSinSample(app)
    
    btnY = cy + 5 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # grand piano
        pauseMusic(app, True)
        readGrandPiano(app)

    btnY = cy + 6 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # custom sound
        pauseMusic(app, True)
        readNewSample(app)

    btnY = cy + 9 * btnH
    y0, y1 =  btnY, btnY + btnH
    vx0 = cx - 100
    vx1 = cx + 100
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # volume
        pauseMusic(app, True)
        pct = (mouseX - vx0) / (vx1 - vx0)
        app.globalAmp = min(max(app.maxAmp * pct, 0), app.maxAmp)
        clearRenderedTrack(app)
        #app.mode = 'home'

    btnY = cy + 11 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # back
        pauseMusic(app, True)
        if(app.mode == 'instrumentFromMusic'):
            app.mode = 'music'
        else:
            app.mode = 'home'
# instrument page's redraw all function
def instrumentRedrawAll(app, canvas):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr


    btnY = cy + 0 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  normalColor,
    text = f'Playback Instruments', font = font)

    btnY = cy + 1 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'You can change the playback instrument sound here.', font = font)

    btnY = cy + 3 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'-Sound Tone-', font = font)

    btnY = cy + 4 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
    text = f'1: Sinwave', font = font)
    
    btnY = cy + 5 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
    text = f'2: Grand Piano', font = font)

    btnY = cy + 6 * btnH
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  filColor,
    text = f'3: Load Custom .wav File', font = font)

    btnY = cy + 8 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'-Sound Volume-', font = font)

    btnY = cy + 9 * btnH
     
    pct = app.globalAmp / app.maxAmp
    vWidth = 200
    vHeight = btnH / 3
    canvas.create_rectangle(cx - vWidth / 2, btnY, cx + vWidth / 2, btnY + vHeight, fill = 'grey', width = 0)
    filColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - vWidth / 2, btnY, cx - vWidth / 2 + vWidth * pct, btnY + vHeight, width = 0,
                            fill = filColor)

    btnY = cy + 11 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  fillColor,
    text = 'Back', font = font)

# event triggered when mouse is cliked in settings page
def settingClicked(app, mouseX, mouseY):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr
    cfg: Config = app.config


    cx -= 200
    x0,x1 =  cx - 150, cx + 150

    btnY = cy + 3 * btnH # max on screen notes
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): 
        if(cfg.noteMaxCount >= 500):
            cfg.noteMaxCount = 0
        elif(cfg.noteMaxCount >= 200):
            cfg.noteMaxCount += 100
        elif(cfg.noteMaxCount >= 100):
            cfg.noteMaxCount += 50
        else:
            cfg.noteMaxCount += 25


    btnY = cy + 4 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # show keyboard
        cfg.showKeyboard = not cfg.showKeyboard

    btnY = cy + 5 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.noteColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.noteColor = [int(r),int(g),int(b)]

    

    btnY = cy + 6 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.noteBlackColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.noteBlackColor = [int(r),int(g),int(b)]

    btnY = cy + 7 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # bg picture
        cfg.noteGlow = not cfg.noteGlow

    btnY = cy + 8 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # bg picture
        cfg.noteFade = not cfg.noteFade

    btnY = cy + 9 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # note border
        cfg.noteBorder = not cfg.noteBorder
    

    btnY = cy + 10 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # bg picture
        cfg.particleSystem = not cfg.particleSystem


    cx += 400

    btnY = cy + 3 * btnH # keyboard pressed flow
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): 
        cfg.pressedGlow = not cfg.pressedGlow

    btnY = cy + 4 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.whiteKeyColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.whiteKeyColor = [int(r),int(g),int(b)]

    btnY = cy + 5 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.blackKeyColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.blackKeyColor = [int(r),int(g),int(b)]

    btnY = cy + 6 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.whiteKeyPressedColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.whiteKeyPressedColor = [int(r),int(g),int(b)]


    btnY = cy + 7 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.blackKeyPressedColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.blackKeyPressedColor = [int(r),int(g),int(b)]
     

    btnY = cy + 8 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.bgColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.bgColor = [int(r),int(g),int(b)]
    #text = 'Background Color: ', font = font)
    #refreshBg(app)

    btnY = cy + 9 * btnH
    x0,x1 = cx -100, cx + 100
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # bg picture
        cfg.bgPicture = not cfg.bgPicture
        refreshBg(app)

    btnY = cy + 10 * btnH
    x0,x1 = cx -150, cx + 150
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # primrary falling note color
        color = colorchooser.askcolor(color = rgbList(cfg.textColor), title ="Choose color")
        if(color != None and color[0] != None):
            r,g,b = color[0]
            cfg.textColor = [int(r),int(g),int(b)]
        app.textColorStr = rgbList(cfg.textColor)

    #####################################################################
    cx = app.cx

    btnY = cy + 11 * btnH
    cx -= 200
    x0,x1 = cx -100, cx + 100
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # reset configuration
        resetConfig(app)

    btnY = cy + 11 * btnH
    cx += 200
    x0,x1 = cx -100, cx + 100
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # load ini
        readNewConfig(app)

    btnY = cy + 11 * btnH
    cx += 200
    x0,x1 = cx -100, cx + 100
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # back
        pauseMusic(app, True)
        saveConfig(app)
        app.mode = 'home'
# setting page's redraw all function
def settingRedrawAll(app, canvas):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr

    btnY = cy + 0 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  normalColor,
    text = f'Settings', font = font)

    btnY = cy + 1 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'You can change the appearance of the program here.', font = font)

    btnY = cy + 3 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f' ', font = font)

    #####################################################################
    cx -= 200
    cfg : Config = app.config
    
    btnY = cy + 3 * btnH
    border = 0.08 * btnH
    
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)

    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Maximum On-Screen Notes: ' +  str(cfg.noteMaxCount), font = font)

    btnY = cy + 4 * btnH
    
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.showKeyboard):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Show Keyboard: ' +  str(cfg.showKeyboard), font = font)

    btnY = cy + 5 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.noteColor[0],cfg.noteColor[1],cfg.noteColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Primary Falling Note Color', font = font)

    btnY = cy + 6 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.noteBlackColor[0],cfg.noteBlackColor[1],cfg.noteBlackColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Secondary Falling Note Color', font = font)

    btnY = cy + 7 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.noteGlow):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Falling Note Glow: ' + str(cfg.noteGlow), font = font)

    btnY = cy + 8 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.noteFade):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Falling Note Matte: ' + str(cfg.noteFade), font = font)

    btnY = cy + 9 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.noteBorder):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Falling Note Border: ' + str(cfg.noteBorder), font = font)

    btnY = cy + 10 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.particleSystem):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Particle Effect: ' + str(cfg.particleSystem), font = font)


    cx += 400

    btnY = cy + 3 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.pressedGlow):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Keyboard Pressed Effect: ' +  str(cfg.pressedGlow), font = font)

    btnY = cy + 4 * btnH
    
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.whiteKeyColor[0],cfg.whiteKeyColor[1],cfg.whiteKeyColor[2]))
    canvas.create_text(cx - 100, btnY , anchor = 'nw', fill =  fillColor,
    text = 'White Key Color', font = font)

    btnY = cy + 5 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.blackKeyColor[0],cfg.blackKeyColor[1],cfg.blackKeyColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Black Key Color', font = font)

    btnY = cy + 6 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.whiteKeyPressedColor[0],cfg.whiteKeyPressedColor[1],cfg.whiteKeyPressedColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Pressed White Key Color', font = font)


    btnY = cy + 7 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.blackKeyPressedColor[0],cfg.blackKeyPressedColor[1],cfg.blackKeyPressedColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Pressed Black Key Color ', font = font)

    btnY = cy + 8 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.bgColor[0],cfg.bgColor[1],cfg.bgColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Background Color: ', font = font)

    btnY = cy + 9 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_oval(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
    normalColor)
    if(cfg.bgPicture):
        canvas.create_oval(cx - 135 + border,btnY+ border+ 0.1 * btnH,cx - 135 + 0.6 * btnH - border,btnY + 0.7 * btnH - border, 
        width = 0, fill = 'black')
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'Show Background Picture: ' + str(cfg.bgPicture), font = font)

    btnY = cy + 10 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_rectangle(cx - 135,btnY+ 0.1 * btnH,cx - 135 + 0.6 * btnH,btnY + 0.7 * btnH, width = 0, fill =
                        rgbString(cfg.textColor[0],cfg.textColor[1],cfg.textColor[2]))
    canvas.create_text(cx - 100, btnY, anchor = 'nw', fill =  fillColor,
    text = 'UI Text Color ', font = font)

    cx -= 200
    #####################################################################

    btnY = cy + 11 * btnH
    cx -= 200
    fillColor = getBtnColor(app, cx - 100,btnY, cx + 100, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  fillColor,
    text = 'Reset configuration', font = font)

    btnY = cy + 11 * btnH
    cx += 200
    fillColor = getBtnColor(app, cx - 100,btnY, cx + 100, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  fillColor,
    text = 'Load config.ini', font = font)

    btnY = cy + 11 * btnH
    cx += 200
    fillColor = getBtnColor(app, cx - 100,btnY, cx + 100, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  fillColor,
    text = 'Back', font = font)

# event triggered when mouse is cliked in about page
def aboutClicked(app, mouseX, mouseY):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr
    x0,x1 =  cx - 150, cx + 150
    btnY = cy + 11 * btnH
    y0, y1 =  btnY, btnY + btnH
    if(inArea(mouseX, mouseY, x0,y0,x1,y1)): # about
        pauseMusic(app, True)
        app.mode = 'home'
# general redraw all function
def aboutRedrawAll(app, canvas):
    cx, cy = app.cx, app.cy - 275
    btnH = app.btnH
    font = app.btnFont
    textColor = app.textColorStr
    normalColor = app.btnColorStr
    hoverColor = app.btnHoverColorStr


    btnY = cy + 0 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  normalColor,
    text = f'About', font = font)

    btnY = cy + 2 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'Visual synthesizer is a MusicXML format music player and visualizer.', font = font)

    btnY = cy + 3 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'It can also export the synthesized sound as .wav file.', font = font)

    btnY = cy + 4 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'It also supports different instruments, you can even load your own voice as the instrument!', font = font)

    btnY = cy + 6 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = f'TP3 Update: Optimizing the playback experience by utilizing the rendered sound after exporting wav.', font = font)

    btnY = cy + 8 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = app.version, font = font)

    btnY = cy + 9 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = 'Author: Alan Zhang', font = font)

    btnY = cy + 10 * btnH
     
    canvas.create_text(cx, btnY, anchor = 'n', fill =  textColor,
    text = 'Especially made for CMU 15-112', font = font)

    btnY = cy + 11 * btnH
    fillColor = getBtnColor(app, cx - 150,btnY, cx + 150, btnY + btnH, normalColor, hoverColor)
    canvas.create_text(cx, btnY, anchor = 'n', fill =  fillColor,
    text = 'Back', font = font)
# draw (view) the model in the canvas
def redrawAll(app, canvas):
    if(app.working == True):
        print('Redraw all triggered when timerFired is working!')
    if(app.img != None):
        canvas.create_image(0,0,anchor = 'nw', pilImage=app.img, 
                        state="normal")
    
    if(app.mode == 'home'):
        homeRedrawAll(app, canvas)
    elif(app.mode == 'music'):
        musicRedrawAll(app, canvas)
    elif(app.mode == 'instrument' or app.mode == 'instrumentFromMusic'):
        instrumentRedrawAll(app, canvas)
    elif(app.mode == 'setting'):
        settingRedrawAll(app, canvas)
    elif(app.mode == 'about'):
        aboutRedrawAll(app, canvas)
    

# convert '1' to 0, '+1' to 7, etc. '+1#' to 0,+1
def pitchToIndex(s = ''):
    if(s == ''):
        return -100,0 #No notes should be culled
    s = s[:]
    octave =  7 * (s.count('+') - s.count('-'))
    step = int(s.replace('+','').replace('-','').replace('#','').replace('b',''))
    step -= 1 # '1' to 1 to 0
    blackNote = 0
    if('#' in s):
        blackNote = 1
    elif('b' in s):
        blackNote = -1
    return (octave + step, blackNote)
# draw notes in numpy array
def drawNotesNp(app, data):
    cx = app.cx + 100
    cy = app.cy + 100
    noteWidth = app.noteKeyWidth
    noteHeight = app.noteHeight # 50 pixels per second
    noteCount = app.config.noteMaxCount # max note count limit
    if(noteCount <=0):
        return
    for note in app.absNotesList:
        noteStart  = note[1]
        noteEnd = noteStart + note[2]
        if(note[0] == ''):
            continue
        noteId, noteBlack = pitchToIndex(note[0])
        if(noteEnd < app.inMusicTime - app.renderBeforeDuration): # culled situation
            continue
        elif(noteStart > app.inMusicTime + app.renderAfterDuration): # culled situation
            break
        
        relativeTime = noteStart - app.inMusicTime
        relativeTimeEnd = noteEnd - app.inMusicTime

        leftX = cx + noteId * noteWidth 
        rightX = leftX + noteWidth
        if(noteBlack != 0):
            if(noteBlack > 0):
                leftX += noteWidth * 0.75 
            else:
                leftX -= noteWidth * 0.25 
            rightX = leftX + noteWidth * 0.5

        lowerY = cy -  relativeTime * noteHeight
        upperY = cy -  relativeTimeEnd * noteHeight

        r,g,b = app.config.noteColor

        if(noteBlack != 0):
            r,g,b = app.config.noteBlackColor
        
        emit = r,g,b 
            
        # use numpy to draw rect in image to avoid performance issue!
        if(upperY < 100 and app.config.noteFadeIn):
            fRatio = max(0, upperY / 100)
            r = int(r * fRatio + (1-fRatio) * app.config.bgColor[0])
            g = int(g * fRatio+ (1-fRatio) * app.config.bgColor[1])
            b = int(b * fRatio+ (1-fRatio) * app.config.bgColor[2])

        numPyDrawRect(data, int(leftX), int(upperY),int(rightX+1),int(lowerY+1), 
                      r, g, b, border = app.config.noteBorder,  
                      roundC = True, fade= app.config.noteFade, fadeFactor = app.config.noteFadeRatio,
                      glow = app.config.noteGlow, glowDis=app.config.noteGlowDis, glowRatio = app.config.noteGlowRate)

        # draw the key glowing effect.
        # glow effect is too expensive for every notes...
        if(relativeTime < 0 and relativeTimeEnd > -app.config.pressedGlowTime and app.config.pressedGlow):
            r,g,b = emit # emit
            center = int((leftX + rightX)/2)
            glowRatio = app.config.pressedGlowRate
            if(relativeTimeEnd < 0):
                glowRatio = glowRatio * ( 1 + (1/app.config.pressedGlowTime) * relativeTimeEnd)

            applyGlowMask(data,int(center), int(cy+1), r, g, b, app.glowMask,app.config.pressedGlowDis, glowRatio)

        noteCount -= 1
        if(noteCount <= 0):
            break

 
# draw particles in numpy array
def drawParticlesNp(app,data):
    if(app.config.particleSystem == False):
        return
    j = 0
    while j < len(app.particles):
        p: Particle = app.particles[j]
        if(p.expired()):
            app.particles.pop(j)
            continue
        else:
            p.update(data, app.particleMask, app.config.particleRadius, app.config.particleGlowRate)
        j += 1

# create a mask image that looks like glowing
def createGlowMask(row, col, glowDis, power = 0.25):
    totalRows = row + 2 * glowDis
    totalCols = col + 2 * glowDis

    leftCount = glowDis
    rightCount = glowDis

    upCount = glowDis
    downCount = glowDis
    midCount = row - upCount - downCount

    zeroCol = np.zeros(totalCols)
    ansRow = np.zeros(totalCols)
    ansRow[0:leftCount] = np.linspace(1,0,leftCount)
    ansRow[leftCount + col:] = np.linspace(0,1,rightCount)

    ansRow **= 2 # square it to make calculate distance faster

    ansCol = np.zeros(totalRows)
    ansCol[0:upCount] = np.linspace(1,0,upCount)
    ansCol[upCount + row:] = np.linspace(0,1,downCount)
    ansCol **= 2# square it to make calculate distance faster
    ansV = np.repeat(ansCol, totalCols).reshape(totalRows,totalCols)
    

    ansH = np.tile(ansRow, totalRows).reshape(totalRows,totalCols)
    # use power to get actual distance
    ansNeg = (ansV + ansH) ** power 
    # shoud be 0.5 to be linear, but I want a non linear ver glow...

    ans = np.ones((totalRows, totalCols))
    ans -= ansNeg
    return ans.clip(0, 1)
# apply the mask image to a numpy array to create glowing effect
def applyGlowMask(data, x, y, r, g, b, glowMask, glowDis, glowRatio = 0.5):
    alphaRate = glowRatio

    w = len(data[0])
    h = len(data)

    x0Glow = x - glowDis
    x1Glow = x + glowDis
    y0Glow = y - glowDis
    y1Glow = y + glowDis

    maskX0, maskX1 = 0,  2 * glowDis
    maskY0, maskY1 = 0,  2 * glowDis
    if(x0Glow < 0):
        maskX0 = -1 * x0Glow
        x0Glow = 0
    if(y0Glow < 0):
        maskY0 = -1 * y0Glow
        y0Glow = 0
    if(x1Glow >= w):
        maskX1 = maskX1 - (x1Glow - (w - 1))
        x1Glow = w - 1
    if(y1Glow >= h):
        maskY1 = maskY1 - (y1Glow - (h - 1))
        y1Glow = h - 1
    
    tmpR = data[y0Glow:y1Glow,x0Glow:x1Glow,0] + r * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]
    tmpG = data[y0Glow:y1Glow,x0Glow:x1Glow,1] + g * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]
    tmpB = data[y0Glow:y1Glow,x0Glow:x1Glow,2] + b * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]

    tmpR = tmpR.clip(0,255)
    tmpG = tmpG.clip(0,255)
    tmpB = tmpB.clip(0,255)
    data[y0Glow:y1Glow,x0Glow:x1Glow,0] = tmpR.astype(np.uint8)
    data[y0Glow:y1Glow,x0Glow:x1Glow,1] = tmpG.astype(np.uint8)
    data[y0Glow:y1Glow,x0Glow:x1Glow,2] = tmpB.astype(np.uint8)
# draw a rectangle in a 2d+rgb numpy arrany
def numPyDrawRect(data, x0, y0,x1,y1, r, g, b, border = False, roundC = False, fade = False, fadeFactor = 0.5, glow = False, glowDis = 10, glowRatio = 0.5):
    w = len(data[0])
    h = len(data)
    
    if(x0 > x1):
        tmp = x0
        x0 = x1
        x1 = tmp
    
    if(y0 > y1):
        tmp = y0
        y0 = y1
        y1 = tmp
    
    if(x1 <= 70):
        return
    elif(x0 >= w):
        return
    elif(y1 <= 70):
        return
    elif(y0 >= h):
        return
    
    if(x0 < 0 + 70):
        x0 = 0 + 70
    if(y0 < 0 + 70):
        y0 = 0 + 70

    if(x1 >= w - 70):
        x1 = w - 70
    if(y1 >= h - 70):
        y1 = h - 70
        

    rows = y1 - y0
    cols = x1 - x0
    
    if(rows <= 0 or cols <= 0):
        return

    # drawing nothing
    if(not (rows > 0 and cols > 0)):
        return

    if(glow):
        #glowDis = 10
        alphaRate = glowRatio
        glowMask = createGlowMask(rows, cols,glowDis)

        x0Glow = x0 - glowDis
        x1Glow = x1 + glowDis
        y0Glow = y0 - glowDis
        y1Glow = y1 + glowDis

        maskX0, maskX1 = 0, cols + 2 * glowDis
        maskY0, maskY1 = 0, rows + 2 * glowDis
        if(x0Glow < 0):
            maskX0 = -1 * x0Glow
            x0Glow = 0
        if(y0Glow < 0):
            maskY0 = -1 * y0Glow
            y0Glow = 0
        if(x1Glow >= w):
            maskX1 = maskX1 - (x1Glow - (w - 1))
            x1Glow = w - 1
        if(y1Glow >= h):
            maskY1 = maskY1 - (y1Glow - (h - 1))
            y1Glow = h - 1
        
        tmpR = data[y0Glow:y1Glow,x0Glow:x1Glow,0] + r * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]
        tmpG = data[y0Glow:y1Glow,x0Glow:x1Glow,1] + g * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]
        tmpB = data[y0Glow:y1Glow,x0Glow:x1Glow,2] + b * alphaRate * glowMask[maskY0: maskY1, maskX0: maskX1 ]

        tmpR = tmpR.clip(0,255)
        tmpG = tmpG.clip(0,255)
        tmpB = tmpB.clip(0,255)
        data[y0Glow:y1Glow,x0Glow:x1Glow,0] = tmpR.astype(np.uint8)
        data[y0Glow:y1Glow,x0Glow:x1Glow,1] = tmpG.astype(np.uint8)
        data[y0Glow:y1Glow,x0Glow:x1Glow,2] = tmpB.astype(np.uint8)



    if(roundC == True):
        C1 = data[y0,x0,:] 
        C2 = data[y0,x1-1,:] 
        C3 = data[y1-1,x0,:] 
        C4 = data[y1-1,x1-1,:] 
    
    data[y0:y1,x0:x1,0].fill(r)
    data[y0:y1,x0:x1,1].fill(g)
    data[y0:y1,x0:x1,2].fill(b)
    
    if(fade == True ):

        try:

            fadeEffect = fadeFactor
            mask = np.linspace(1,1-fadeEffect,x1 - x0)
            mask = np.repeat(mask,3)
            

            mask = np.tile(mask,y1-y0)
            mask = mask.reshape(y1-y0,x1-x0,3)
            
            tmpDB = ((data[y0:y1,x0:x1,:] * mask).clip(0,255) ).astype(np.uint8)
            data[y0:y1,x0:x1,:] = tmpDB
            
        except:
            print('Error occured!')
            raise


    if(border == True):
        data[y0:y1,x0:x0+1,:] = 0
        data[y0:y1,x1-1:x1,:] = 0
        data[y0:y0+1,x0:x1,:] = 0
        data[y1-1:y1,x0:x1,:] = 0
    # experimental round corner feature. Still under testing.
    if(roundC == True):
        data[y0,x0,:] = C1
        data[y0,x1-1,:] = C2
        data[y1-1,x0,:] = C3
        data[y1-1,x1-1,:] = C4

    

# draw the keyboard in a numpy array
def drawKeyBoardNp(app, data, pressEffect = True):
    # draw the white keyboard first
    if(app.config.showKeyboard == False):
        return
    cx = app.cx + 100
    cy = app.cy + 100
    noteWidth = app.noteKeyWidth
    noteHeight = app.noteKeyHeight  # 50 pixels per second
    for j in range(-7*4,7*4):
        leftX = cx + j * noteWidth
        upperY = cy 
        fillColor = 'white'
        r,g,b = app.config.whiteKeyColor

        pitchIndex = (j,0)
        if(pitchIndex in app.pressedKeys and pressEffect):
            if(app.pressedKeys[pitchIndex][0] >app.timerFiredTime - app.startTime):

                r,g,b = app.config.whiteKeyPressedColor
                endTime = app.pressedKeys[pitchIndex][0]
                dur = app.pressedKeys[pitchIndex][1]
                relativeTime =  (endTime - dur) - (app.timerFiredTime - app.startTime)

        rightX = leftX + noteWidth
        lowerY = upperY  + noteHeight
        numPyDrawRect(data, int(leftX), int(upperY),int(rightX+1),int(lowerY+1), 
                      r, g, b, border = app.config.keyBorder,fade = app.config.whiteKeyFade, fadeFactor = app.config.whiteKeyFadeRate)
        
    for j in range(-7*4,7*4):
        leftX = cx + j * noteWidth
        upperY = cy 
        if(j % 7 != 2 and j % 7 != 6):
            leftX += 0.75 * noteWidth
            fillColor = 'black'
            r,g,b = app.config.blackKeyColor
            pitchIndex = (j,1)
            if(pitchIndex in app.pressedKeys and pressEffect):
                if(app.pressedKeys[pitchIndex][0] > app.timerFiredTime - app.startTime):
                    fillColor = 'blue'
                    r,g,b = app.config.blackKeyPressedColor
                    endTime = app.pressedKeys[pitchIndex][0]
                    dur = app.pressedKeys[pitchIndex][1]
                    relativeTime =  (endTime - dur) - (app.timerFiredTime - app.startTime)

            pitchIndex = (j+1,-1)
            if(pitchIndex in app.pressedKeys and pressEffect):
                if(app.pressedKeys[pitchIndex][0] > app.timerFiredTime - app.startTime):
                    fillColor = 'blue'
                    r,g,b = app.config.blackKeyPressedColor
                    endTime = app.pressedKeys[pitchIndex][0]
                    dur = app.pressedKeys[pitchIndex][1]
                    relativeTime =  (endTime - dur) - (app.timerFiredTime - app.startTime)

            rightX = int(leftX + noteWidth/2)
            lowerY = int(upperY  + noteHeight / 2)
            numPyDrawRect(data, int(leftX), int(upperY),int(rightX+1),int(lowerY+1), 
                      r, g, b, border = app.config.keyBorder,fade = app.config.blackKeyFade, fadeFactor = app.config.blackKeyFadeRate)

# shortcut keys function
def keyPressed(app, event): 
    if(event.key == 'Space'):
        pauseMusic(app, not app.paused)
        #app.paused = not app.paused
    if(event.key == 'r'):
        app.startTime =  time.time() 
        app.inMusicTime = 0
        app.i = 0
        app.pressedKeys = dict()
    if(event.key == 'o'):
        pauseMusic(app, True)
        readNewFile(app)
    if(event.key == 's'):
        readNewSample(app)
    if(event.key == 'p'):
        readGrandPiano(app)
    if(event.key == 'x'):
        exportWavFile(app)
    if(event.key == 'i'):
        readNewConfig(app)
    if(event.key == 'Up'):
        JumpToSecond(app, app.inMusicTime + 5)
    if(event.key == 'Down'):
        JumpToSecond(app, app.inMusicTime - 5)
# when play/paused, trigger this function to play the rendered music or stop it
def JumpToSecondInPause(app, targetSecond):
    targetSecond = max(0, min(app.musicDuration+1, targetSecond))
    app.startTime =  time.time() - targetSecond
    app.inMusicTime = targetSecond
    app.i = 0
    app.pressedKeys = dict()
    while app.i < len(app.absNotesList):
        if(app.inMusicTime > app.absNotesList[app.i][1]):
            app.i+=1
        else: 
            app.i-=1
            break
    if(app.i < 0):
        app.i = 0
# Jump to a certain music time
def JumpToSecond(app, targetSecond):
    pauseMusic(app, True)
    targetSecond = max(0, min(app.musicDuration+1, targetSecond))
    app.startTime =  time.time() - targetSecond
    app.inMusicTime = targetSecond
    app.i = 0
    app.pressedKeys = dict()
    while app.i < len(app.absNotesList):
        if(app.inMusicTime > app.absNotesList[app.i][1]):
            app.i+=1
        else: 
            app.i-=1
            break
    if(app.i < 0):
        app.i = 0

      
# Stop the prerendered music
def appStopped(app): 
    if(app.saObj != None):
        app.saObj.stop()

# mouse clicked trigger event
def mouseReleased(app, event): 
    if(app.mode == 'home'):
        homeClicked(app, event.x, event.y)
    elif(app.mode == 'music'):
        musicClicked(app, event.x, event.y)
    elif(app.mode == 'instrument' or app.mode == 'instrumentFromMusic'):
        instrumentClicked(app, event.x, event.y)
    elif(app.mode == 'setting'):
        settingClicked(app, event.x, event.y)
    elif(app.mode == 'about'):
        aboutClicked(app, event.x, event.y)
# record mouse position
def mouseMoved(app, event):
    app.mouseX = event.x
    app.mouseY = event.y

# triggered when window size changed
# although I does not recommend doing this
def sizeChanged(app):         # respond to window size changes
    app.cx = (app.width / 2) / app.renderScale
    app.cy = app.height * 0.75 / app.renderScale
    iw,ih = app.width, app.height
    app.imgNp = np.ones((ih//app.renderScale + 200, iw//app.renderScale + 200, 3), dtype=np.uint8)
    if(app.config.bgPicture):
        if(os.path.exists(app.config.bgPath)):
            tmpImg = app.bgImg.resize((app.width, app.height), Image.NEAREST)
            app.bgPicNp = np.array(tmpImg.getdata(), dtype=np.uint8).reshape(tmpImg.height, tmpImg.width, 3)
    app.titleImg = Image.open('title.png').resize((app.width, app.height), Image.ANTIALIAS)
    app.musicImg = Image.open('music.png').resize((app.width, app.height), Image.ANTIALIAS)

# run the app
if (__name__ == '__main__'):
    runApp(width=720, height=480, x = 500, y = 500, 
           title = 'Visual Synth 112 VerTP3 By Alan Zhang')