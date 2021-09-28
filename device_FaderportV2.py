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
PREV_NEXT_MODE = 0
IDLE_COUNT = 0
PULSE_VAL = 0

class TFaderportV2:

	def OnInit(self):
		print("On Init")
		self.BTN = self.BTN()
		self.STATUS = self.STATUS()
		self.ENC = self.ENC()
		self.PN = self.PN()
		self.UpdateEncMode(2)
		global PREV_NEXT_MODE
		PREV_NEXT_MODE = 0
		self.OnRefresh(0)

	def OnDeInit(self):
		print("On De Init")
		
	def OnMidiIn(self, event):

		print("On Midi In")
		print("Status: ", event.status, "Data1: ", event.data1, "Data2: ", event.data2)
		event.handled = False

		i = mixer.trackNumber()

		if event.status == self.STATUS.FADER:
			intVol = self.scaleValue(event.data2, 127, 1)
			fracVol = self.scaleValue(event.data1, 127, 1)/100
			sVol = intVol + fracVol
			mixer.setTrackVolume(i, sVol)
			event.handled = True

		elif event.status == self.STATUS.KNOB:
			if ENC_MODE == self.ENC.LINK:
				event.handled = True
			elif ENC_MODE == self.ENC.PAN:
				if event.data2 > 64: 
					sPan = mixer.getTrackPan(i) + ((64 - event.data2)/100)
				else:
					sPan = mixer.getTrackPan(i) + (event.data2/100)
				mixer.setTrackPan(i, sPan)
				event.handled = True
			elif ENC_MODE == self.ENC.CHANNEL:
				if event.data2 > 64:
					self.Previous()
				else:
					self.Next()
				event.handled = True
			elif ENC_MODE == self.ENC.SCROLL:
				event.handled = True

		elif (event.status == self.STATUS.BTN) & (event.controlVal == 127):
			
			if (event.controlNum == self.BTN.PREV_UNDO):
				self.Previous()
				event.handled = True

			if (event.controlNum == self.BTN.NEXT_REDO):
				self.Next()
				event.handled = True

			if (event.controlNum == self.BTN.CLICK_F2):
				transport.globalTransport(midi.FPT_Metronome,1)
				event.handled = True

			if (event.controlNum == self.BTN.PLAY):
				transport.start()
				event.handled = True

			if (event.controlNum == self.BTN.STOP):
				transport.stop()
				event.handled = True

			if (event.controlNum == self.BTN.RECORD):
				transport.record()
				event.handled = True

			if (event.controlNum == self.BTN.LOOPMODE):
				transport.setLoopMode()
				event.handled = True

			if (event.controlNum == self.BTN.MUTE_CLEAR):
				mixer.enableTrack(i)
				event.handled = True

			if (event.controlNum == self.BTN.SOLO_CLEAR):
				mixer.soloTrack(i)
				event.handled = True

			if (event.controlNum == self.BTN.ARM_ALL):
				mixer.armTrack(i)
				event.handled = True
			
			if (event.controlNum == self.BTN.LINK_LOCK):
				self.UpdateEncMode(1)
				event.handled = True

			if (event.controlNum == self.BTN.PAN_FLIP):
				self.UpdateEncMode(2)
				event.handled = True

			if (event.controlNum == self.BTN.CHANNEL_LOCK):
				self.UpdateEncMode(3)
				event.handled = True

			if (event.controlNum == self.BTN.SCROLL_ZOOM):
				self.UpdateEncMode(4)
				event.handled = True

			if (event.controlNum == self.BTN.KNOB):
				mixer.setTrackPan(i, 0)
				event.handled = True

		elif (event.status == self.STATUS.BTN) & (event.controlVal == 0):
			event.handled = True

	def OnRefresh(self, flags):

		if device.isAssigned():
			print("On Refresh")

			i = mixer.trackNumber()

			Volume = mixer.getTrackVolume(i)
			sVol = math.modf(self.scaleValue(Volume, 1, 127))
			fracVol = round(self.scaleValue(sVol[0], 1, 127))
			intVol = round(sVol[1])
			self.UpdateFader(fracVol, intVol)

			Pan = (mixer.getTrackPan(i))

			if mixer.isTrackSolo(i):
				self.UpdateLEDs(self.BTN.SOLO_CLEAR, 127)
			else:
				self.UpdateLEDs(self.BTN.SOLO_CLEAR, 0)

			if mixer.isTrackEnabled(i):
				self.UpdateLEDs(self.BTN.MUTE_CLEAR, 0)
			else:
				self.UpdateLEDs(self.BTN.MUTE_CLEAR, 127)

			if mixer.isTrackArmed(i):
				self.UpdateLEDs(self.BTN.ARM_ALL, 127)
			else:
				self.UpdateLEDs(self.BTN.ARM_ALL, 0)

			if general.getUseMetronome():
				self.UpdateLEDs(self.BTN.CLICK_F2, 127)
			else:
				self.UpdateLEDs(self.BTN.CLICK_F2, 0)

			if transport.isPlaying():
				self.UpdateLEDs(self.BTN.PLAY, 127)
			else:
				self.UpdateLEDs(self.BTN.PLAY, 0)

			if transport.isRecording():
				self.UpdateLEDs(self.BTN.RECORD, 127)
			else:
				self.UpdateLEDs(self.BTN.RECORD, 0)
			
			if transport.getLoopMode():
				self.UpdateLEDs(self.BTN.LOOPMODE, 0)
			else:
				self.UpdateLEDs(self.BTN.LOOPMODE, 127)
			
			self.UpdateEncMode(ENC_MODE)
			
			global PREV_NEXT_MODE
			if ui.getFocused(0):
				PREV_NEXT_MODE = 0
			elif ui.getFocused(1):
				PREV_NEXT_MODE = 1

	def OnUpdateBeatIndicator(self, value):

		print("On Update Beat Indicator")

	def OnIdle(self):

		
		global IDLE_COUNT
		IDLE_COUNT = IDLE_COUNT + 1

		global PULSE_VAL
		if IDLE_COUNT == 1:
			PULSE_VAL = 127
			self.OnRefresh(0)
		elif IDLE_COUNT == 13:
			PULSE_VAL = 0
			self.OnRefresh(0)
		elif IDLE_COUNT > 24:
			IDLE_COUNT = 0
		
		print("PULSE : ", PULSE_VAL)
		


	def scaleValue(self, value, scaleIn, scaleOut):
		return ((value/scaleIn) * scaleOut)

	def UpdateFader(self, Frac, Int):
		device.midiOutMsg(self.STATUS.FADER + (Frac << 8) + (Int << 16))

	def UpdateLEDs(self, Index, Value):
		device.midiOutMsg(self.STATUS.BTN + (Index << 8) + (Value << 16))

	def UpdateEncMode(self, mode):
		global ENC_MODE
		ENC_MODE = mode

		self.UpdateLEDs(self.BTN.LINK_LOCK, 0)
		self.UpdateLEDs(self.BTN.PAN_FLIP, 0)
		self.UpdateLEDs(self.BTN.CHANNEL_LOCK, 0)
		self.UpdateLEDs(self.BTN.SCROLL_ZOOM, 0)

		if mode == self.ENC.LINK:
			self.UpdateLEDs(self.BTN.LINK_LOCK, PULSE_VAL)
		elif mode == self.ENC.PAN:
			self.UpdateLEDs(self.BTN.PAN_FLIP, PULSE_VAL)
		elif mode == self.ENC.CHANNEL:
			self.UpdateLEDs(self.BTN.CHANNEL_LOCK, PULSE_VAL)
		elif mode == self.ENC.SCROLL:
			self.UpdateLEDs(self.BTN.SCROLL_ZOOM, PULSE_VAL)
	
	def Next(self):
		if PREV_NEXT_MODE == self.PN.MIXER:
			mixer.setTrackNumber(mixer.trackNumber() + 1)
		elif PREV_NEXT_MODE == self.PN.CHANNEL:
			channels.selectOneChannel(channels.channelNumber() + 1)
		else:
			transport.globalTransport(midi.FPT_Next,1)
	
	def Previous(self):
		if PREV_NEXT_MODE == self.PN.MIXER:
			mixer.setTrackNumber(mixer.trackNumber() - 1) 
		elif PREV_NEXT_MODE == self.PN.CHANNEL:
			channels.selectOneChannel(channels.channelNumber() - 1)
		else:
			transport.globalTransport(midi.FPT_Previous,1)
			

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

	class PN:
		MIXER = 	0
		CHANNEL = 	1

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

def OnDoFullRefresh(Flags):
	FaderportV2.OnDoFullRefresh(Flags)

def OnUpdateBeatIndicator(value):
	FaderportV2.OnUpdateBeatIndicator(value)
