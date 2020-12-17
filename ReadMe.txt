----------------------------------------------------------------------
Visual Synthesizer TP3
Author: Alan Zhang
Especially made for 15-112
----------------------------------------------------------------------

Project description:
	
Visual Synthesizer is a MusicXML format music player and visualizer. It supports and
plays >95% piano solo format MusicXML file, which is downloadable via
https://musescore.com/. It can also export .wav sound file that this player 
played. User will also be able to customize this programs’ UIs and instrument
sounds, which makes this program more fun and interactive.

This program also supports a custom defined .synnote format music notes file.
This music note format is compact and human-readable. 
User can easily compose music in this format and play it directly in the Visual Synthesizer.

----------------------------------------------------------------------

How to run the project:

There are two ways to run this project:

	Option1: Open ProgramGUI.py via Visual Studio Code and then Ctrl+B
	
	Option2: (Windos OS): Double click the 'run.bat' to run the program.

After you started the program, you can click '[Load MusicXML File]' and then select 
'canon.xml' or 'Waltz_in_A_MinorChopin.mxl' to play these starter MusicXML file!

If you want to play the .synnote file, after click  '[Load MusicXML File]' , in the file
choosing dialog's bottom right corner, change the file type from 'Music XML file' to 
'Custom defined music note' and then select 'CustomMusic.synnote.' Now the program
will play this synnote file!

----------------------------------------------------------------------

Additional Note: (Important!)

This program's computation task is heavy, if this program is laggy or crashs frequently, you probably need a computer with better CPU to run this program. Another fix option is to run this program in stable mode (simple graphics mode.) In program's setting menu, there is a load config.ini button, click it and then select config_stable.ini. In this mode, this program requires less computation power and will be less laggy.

----------------------------------------------------------------------

Required libraries:

My program requires two extermal library:
	Numpy
	Simpleaudio

----------------------------------------------------------------------

Keyboard shortcuts:

Here are some shortcut keys:
	Space:	Pause/play the current music
	Up:		Fast forward 5 seconds
	Down:	Backward 5 seconds
	R:		Replay the current music
	O:		Open a new musicXML/ synnote file
	S:		Read a custom .wav file as the intrument
	P:		Read the grand piano instrument
	X:		Export the .wav file 
	I:		Load a new config.ini file
	
----------------------------------------------------------------------
