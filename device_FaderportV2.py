# name=Presonus Faderport v2
# url=

import patterns
import mixer
import channels
import device
import transport
import arrangement
import general
import ui
import launchMapPages
import playlist
import math
import midi
import utils

ENC_MODE = 0
SHIFT_MOMENTARY = False
KNOB_MOMENTARY = False
SHIFT_ON = False
PREV_NEXT_MODE = 0
MASTER_MODE = False
IDLE_COUNT = 0
PULSE_VAL = 0
getPan = 0
getVol = 0
setPan = 0
setVol = 0

#TODO
#channel rack volume and pan control
#knob momentary functions
#shift functions? if pressing the shift button it returns back though...
#shift button stays lit
#master doesn't light
#fader doesn't set for channel
#flip doesn't work with channel


class TFaderportV2:

	def OnInit(self):
		print("On Init")
		self.BTN = self.BTN()
		self.STATUS = self.STATUS()
		self.ENC = self.ENC()
		self.PN = self.PN()
		self.WINDOW = self.WINDOW()
		global ENC_MODE
		ENC_MODE = self.ENC.PAN
		global PREV_NEXT_MODE
		PREV_NEXT_MODE = self.PN.MIXER
		self.OnRefresh(0)

	def OnDeInit(self):
		print("On De Init")
		
	def OnMidiIn(self, event):

		print("On Midi In")
		print("Status: ", event.status, "Data1: ", event.data1, "Data2: ", event.data2)
		
		global ENC_MODE
		global SHIFT_MOMENTARY
		global MASTER_MODE
		global KNOB_MOMENTARY
		global getPan
		global getVol
		global setPan
		global setVol

		event.handled = True

		if PREV_NEXT_MODE == self.PN.MIXER: ##todo this is terrible pt1
			i = 0 if MASTER_MODE else mixer.trackNumber()
			getPan = mixer.getTrackPan(i)
			getVol = mixer.getTrackVolume(i)
		elif PREV_NEXT_MODE == self.PN.CHANNEL:
			i = channels.channelNumber()
			getPan = channels.getChannelPan(i)
			getVol = channels.getChannelVolume(i)
		
		print(PREV_NEXT_MODE)
		setPan = getPan
		setVol = getVol
		
		if event.status == self.STATUS.FADER:
			intVol = self.scaleValue(event.data2, 127, (2 if ENC_MODE == self.ENC.FLIP else 1))
			fracVol = self.scaleValue(event.data1, 127, 1)/100
			sVol = intVol + fracVol
			if ENC_MODE == self.ENC.FLIP:
				setPan = sVol-1
				print('setpan:',setPan)
			else:
				setVol = sVol
				print('setVol:',setVol)


		elif event.status == self.STATUS.KNOB:
			
			knobVal = 64-event.data2 if event.data2 > 64 else event.data2
			knobVal = knobVal * 4 if KNOB_MOMENTARY else knobVal

			#if ENC_MODE == self.ENC.LINK:
			if ENC_MODE == self.ENC.PAN:
				if SHIFT_MOMENTARY:
					inc = 0.25
					sPan = round((getPan) * 4)/4
					rPan = sPan + inc if knobVal > 0 else sPan - inc
					dPan = abs(rPan - getPan)
					setPan = sPan if dPan > inc else rPan			
				else:
					setPan = getPan + (knobVal/100)
		
			elif ENC_MODE == self.ENC.CHANNEL:
				jump = 4
				k = math.ceil(abs(knobVal)/jump)
				for x in range(k):
					self.Next() if knobVal > 0 else self.Previous()
			elif ENC_MODE == self.ENC.SCROLL:
				sPosAbsTicks = transport.getSongPos(midi.SONGLENGTH_ABSTICKS)
				if SHIFT_MOMENTARY:
					inc = 384
					sPos = round(sPosAbsTicks/384) * 384 #TOTO MAKE THIS A FUNCTION
					rPos = sPos + inc if knobVal > 0 else sPos - inc
					dPos = abs(rPos - sPosAbsTicks)
					transport.setSongPos(sPos if dPos > inc else rPos, midi.SONGLENGTH_ABSTICKS)
				else:
					knobVal = knobVal * 24
					transport.setSongPos(sPosAbsTicks + knobVal, midi.SONGLENGTH_ABSTICKS)
			elif ENC_MODE == self.ENC.FLIP:
				if SHIFT_MOMENTARY:
					inc = 0.2
					sVol = round(getVol * 5)/5
					rVol = round(sVol + inc,1) if knobVal > 0 else round(sVol - inc,1)
					dVol = round(abs(rVol - getVol),2)
					setVol = sVol if dVol > inc else rVol		
				else:
					setVol =  getVol + (knobVal/100)

		elif (event.status == self.STATUS.BTN):
			
			if (event.controlNum == self.BTN.SHIFT):
				
				SHIFT_MOMENTARY = True if event.controlVal == 127 else False
				self.UpdateLEDs(self.BTN.SHIFT, (127 if (SHIFT_MOMENTARY or ENC_MODE > 4) else 0))

			if (event.controlNum == self.BTN.KNOB):
					KNOB_MOMENTARY = True if event.controlVal == 127 else False
					
			if (event.controlVal == 127):

				if (event.controlNum == self.BTN.PREV_UNDO):
					if SHIFT_MOMENTARY: general.undoUp()
					else: self.Previous()
				elif (event.controlNum == self.BTN.NEXT_REDO):
					if SHIFT_MOMENTARY: general.undoDown()
					else: self.Next()
				elif (event.controlNum == self.BTN.LINK_LOCK):		ENC_MODE = self.ENC.LI_LOCK if SHIFT_MOMENTARY else self.ENC.LINK
				elif (event.controlNum == self.BTN.PAN_FLIP):		ENC_MODE = self.ENC.FLIP if (SHIFT_MOMENTARY and ENC_MODE == self.ENC.PAN) else self.ENC.PAN
				elif (event.controlNum == self.BTN.CHANNEL_LOCK):	ENC_MODE = self.ENC.CH_LOCK if SHIFT_MOMENTARY else self.ENC.CHANNEL
				elif (event.controlNum == self.BTN.SCROLL_ZOOM):	ENC_MODE = self.ENC.ZOOM if SHIFT_MOMENTARY else self.ENC.SCROLL
				elif (event.controlNum == self.BTN.MASTER_F1):
					if SHIFT_MOMENTARY: transport.globalTransport(midi.FPT_F9,1)
					else: MASTER_MODE = MASTER_MODE ^ True
				elif (event.controlNum == self.BTN.CLICK_F2):
					if SHIFT_MOMENTARY: transport.globalTransport(midi.FPT_F6,1)
					else: transport.globalTransport(midi.FPT_Metronome,1)
				
				elif (event.controlNum == self.BTN.PLAY): 			transport.start()
				elif (event.controlNum == self.BTN.STOP):			transport.stop()
				elif (event.controlNum == self.BTN.RECORD):			transport.record()
				elif (event.controlNum == self.BTN.LOOPMODE):		transport.setLoopMode()
				elif (event.controlNum == self.BTN.MUTE_CLEAR):		mixer.muteTrack(i)
				elif (event.controlNum == self.BTN.SOLO_CLEAR):		mixer.soloTrack(i)
				elif (event.controlNum == self.BTN.ARM_ALL):		mixer.armTrack(i)

		if PREV_NEXT_MODE == self.PN.MIXER: #todo terrible pt2
			mixer.setTrackPan(i, setPan)
			mixer.setTrackVolume(i, setVol)
		elif PREV_NEXT_MODE == self.PN.CHANNEL:
			channels.setChannelPan(i, setPan)
			channels.setChannelVolume(i, setVol)

		self.OnRefresh(0)
		#elif (event.status == self.STATUS.BTN) & (event.controlVal == 0):

	def OnRefresh(self, flags):

		if device.isAssigned():
			print("On Refresh")

			global PREV_NEXT_MODE

			if PREV_NEXT_MODE == self.PN.MIXER: ##todo this is terrible pt3
				i = 0 if MASTER_MODE else mixer.trackNumber() #START 
				Pan = mixer.getTrackPan(i)
				Volume = mixer.getTrackVolume(i)
			elif PREV_NEXT_MODE == self.PN.CHANNEL:
				i = channels.channelNumber()
				Pan = channels.getChannelPan(i)
				Volume = channels.getChannelVolume(i)

			# if PREV_NEXT_MODE == self.PN.MIXER:
			# 	Volume = mixer.getTrackVolume(i)
			# 	Pan = mixer.getTrackPan(i) + 1
			# elif PREV_NEXT_MODE == self.PN.CHANNEL:
			# 	Volume = channels.getChannelVolume(i)
			# 	Pan = channels.getChannelPan(i) + 1
			
			sVol = math.modf(self.scaleValue((Pan if ENC_MODE == self.ENC.FLIP else Volume), (2 if ENC_MODE == self.ENC.FLIP else 1), 127))
			fracVol = round(self.scaleValue(sVol[0], 1, 127))
			intVol = round(sVol[1])
			self.UpdateFader(fracVol, intVol)

			self.UpdateLEDs(self.BTN.SOLO_CLEAR, (127 if mixer.isTrackSolo(i) else 0))
			self.UpdateLEDs(self.BTN.MUTE_CLEAR, (0 if mixer.isTrackEnabled(i) else 127))
			self.UpdateLEDs(self.BTN.ARM_ALL, (127 if mixer.isTrackArmed(i) else 0))
			self.UpdateLEDs(self.BTN.MASTER_F1, (127 if MASTER_MODE else 0))
			self.UpdateLEDs(self.BTN.CLICK_F2, (127 if general.getUseMetronome() else 0))
			self.UpdateLEDs(self.BTN.PLAY, (127 if transport.isPlaying() else 0))
			self.UpdateLEDs(self.BTN.RECORD, (127 if transport.isRecording() else 0))
			self.UpdateLEDs(self.BTN.LOOPMODE, (0 if transport.getLoopMode() else 127))
			
			LED_OUT = 127 #PULSE_VAL if (ENC_MODE > 4) else 127 # not sure about blinking stuff

			self.UpdateLEDs(self.BTN.SHIFT, 127 if (ENC_MODE > 4 or SHIFT_MOMENTARY) else 0)
			self.UpdateLEDs(self.BTN.LINK_LOCK, (LED_OUT if (ENC_MODE == self.ENC.LINK or ENC_MODE == self.ENC.LI_LOCK) else 0))
			self.UpdateLEDs(self.BTN.PAN_FLIP, (LED_OUT if (ENC_MODE == self.ENC.PAN or ENC_MODE == self.ENC.FLIP) else 0))
			self.UpdateLEDs(self.BTN.CHANNEL_LOCK, (LED_OUT if (ENC_MODE == self.ENC.CHANNEL or ENC_MODE == self.ENC.CH_LOCK) else 0))
			self.UpdateLEDs(self.BTN.SCROLL_ZOOM, (LED_OUT if (ENC_MODE == self.ENC.SCROLL or ENC_MODE == self.ENC.ZOOM) else 0))
			
			
			if ui.getFocused(0): PREV_NEXT_MODE = self.PN.MIXER
			elif ui.getFocused(1): PREV_NEXT_MODE = self.PN.CHANNEL

	def OnUpdateBeatIndicator(self, value):

		print("On Update Beat Indicator")

	def OnIdle(self):

		global IDLE_COUNT
		global PULSE_VAL

		IDLE_COUNT = IDLE_COUNT + 1 if IDLE_COUNT < 24 else 0
		PULSE_VAL = 127 if IDLE_COUNT < 13 else 0
		
		#if (ENC_MODE > 4 and (IDLE_COUNT == 1 or IDLE_COUNT == 14)): self.OnRefresh(0)
		
		
	def scaleValue(self, value, scaleIn, scaleOut):
		return ((value/scaleIn) * scaleOut)

	def UpdateFader(self, Frac, Int):
		device.midiOutMsg(self.STATUS.FADER + (Frac << 8) + (Int << 16))

	def UpdateLEDs(self, Index, Value):
		device.midiOutMsg(self.STATUS.BTN + (Index << 8) + (Value << 16))
	
	def Next(self):
		print(mixer.trackNumber()+1)
		if PREV_NEXT_MODE == self.PN.MIXER: 
			mixer.setTrackNumber(mixer.trackNumber() + 1 if mixer.trackNumber() < 126 else 0)
			#no worky in 20.8.4 ui.scrollWindow(self.WINDOW.MIXER,mixer.trackNumber())
		elif PREV_NEXT_MODE == self.PN.CHANNEL: 
			channels.selectOneChannel(channels.channelNumber() + 1 if (channels.channelNumber()+1) < channels.channelCount() else 0)
		else: transport.globalTransport(midi.FPT_Next,1)
	
	def Previous(self):
		print(mixer.trackNumber()-1)
		if PREV_NEXT_MODE == self.PN.MIXER: mixer.setTrackNumber(mixer.trackNumber() - 1 if mixer.trackNumber() > 0 else 126) 
		elif PREV_NEXT_MODE == self.PN.CHANNEL: channels.selectOneChannel(channels.channelNumber() - 1 if channels.channelNumber() > 0 else channels.channelCount()-1)
		else: transport.globalTransport(midi.FPT_Previous,1)
			

	class BTN:
		SOLO_CLEAR = 	8
		MUTE_CLEAR = 	16
		ARM_ALL = 		0
		SHIFT = 		70
		BYPASS_ALL = 	3
		TOUCH_LATCH = 	77
		WRITE_TRIP = 	75
		READ_OFF = 		74
		PREV_UNDO = 	46
		NEXT_REDO = 	47
		LINK_LOCK = 	5
		PAN_FLIP = 		42
		CHANNEL_LOCK = 	54
		SCROLL_ZOOM = 	56
		MASTER_F1 = 	58
		CLICK_F2 = 		59
		SECTION_F3 = 	60
		MARKER_F4 = 	61
		LOOPMODE = 		86
		REWIND = 		91
		FORWARD = 		92
		STOP = 			93
		PLAY = 			94
		RECORD =		95
		KNOB = 			32

	class STATUS:
		FADER = 	224
		KNOB = 		176
		BTN = 		144
	
	class ENC:
		LINK = 		1
		PAN = 		2
		CHANNEL = 	3
		SCROLL = 	4
		LI_LOCK =	5
		FLIP =		6
		CH_LOCK = 	7
		ZOOM = 		8

	class PN:
		MIXER = 	0
		CHANNEL = 	1

	class WINDOW:
		MIXER = 	0
		CHANNEL =	1
		PLAYLIST =	2

FaderportV2 = TFaderportV2()

def OnInit():
	FaderportV2.OnInit()

def OnDeInit():
	FaderportV2.OnDeInit()

def OnMidiIn(event):
	FaderportV2.OnMidiIn(event)

def OnIdle():
	FaderportV2.OnIdle()

def OnRefresh(Flags):
	FaderportV2.OnRefresh(Flags)

def OnUpdateBeatIndicator(value):
	FaderportV2.OnUpdateBeatIndicator(value)
