# name=Presonus Faderport v2
# url=

import patterns
import mixer
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

class TFaderportV2:

	def OnInit(self):
		print("On Init")
		self.BTN = self.BTN()
		self.STATUS = self.STATUS()
		self.OnRefresh(0)

	def OnDeInit(self):
		print("On De Init")

	# def UpdateKnobs(self, Index, Value):

	# 	#print("Update KNOB")
	# 	if (self.KNOB.PAN == Index):
	# 		if (64 < Value < 65): Value = 65
	# 		if (64 > Value > 63): Value = 63
	# 	Value = int(Value)
	# 	#print("Knob Output: i=", Index, ", val=", Value)
	# 	device.midiOutMsg(0 + midi.MIDI_CONTROLCHANGE + (Index << 8) + (Value << 16))

	def UpdateFader(self, Value1, Value2):
		device.midiOutMsg(self.STATUS.FADER + (Value1 << 8) + (Value2 << 16))

	def UpdateLEDs(self, Index, Value):
		device.midiOutMsg(self.STATUS.BTN + (Index << 8) + (Value << 16))

	def OnMidiIn(self, event):

		print("On Midi In")
		print("Status: ", event.status, "Data1: ", event.data1, "Data2: ", event.data2)
		event.handled = False

		i = mixer.trackNumber()

		if event.status == self.STATUS.FADER:
			#TODO involve data 1 and make high res fader
			sVol = self.scaleValue(event.data2, 127, 1)
			mixer.setTrackVolume(mixer.trackNumber(), sVol)
			event.handled = True

		elif event.status == self.STATUS.KNOB:
			sPan = (self.scaleValue(event.data1, 127, 2) - 1)
			if (abs(sPan) < 0.008):
				sPan = 0
			mixer.setTrackPan(mixer.trackNumber(), sPan)
			event.handled = True

		elif (event.status == self.STATUS.BTN) & (event.controlVal == 127):
			
			if (event.controlNum == self.BTN.PREV_UNDO):
				transport.globalTransport(midi.FPT_Previous,1)
				event.handled = True

			if (event.controlNum == self.BTN.NEXT_REDO):
				transport.globalTransport(midi.FPT_Next,1)
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

		elif (event.status == self.STATUS.BTN) & (event.controlVal == 0):
			event.handled = True

	def OnMidiMsg(self, event):

		print("On Midi Msg")
		event.handled = False
		

	def OnControlChange(self, event):

		print("On Control Change")
		event.handled = False

	def OnMidiOutMsg(self, event):

		print("On Midi Out Msg")
		event.handled = False

	def OnRefresh(self, flags):

		if device.isAssigned():
			print("On Refresh")

			i = mixer.trackNumber()

			Volume = mixer.getTrackVolume(i)
			sVol = round(self.scaleValue(Volume, 1, 127))
			print(sVol)
			self.UpdateFader(0, sVol)

			# Pan = 1 + (mixer.getTrackPan(i))
			# sPan = self.scaleValue(Pan, 2, 127)
			# self.UpdateKnobs(self.KNOB.PAN, sPan)

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

	def OnDoFullRefresh(self):

		print("On Do Full Refresh: ")

	def OnUpdateBeatIndicator(self, value):

		print("On Update Beat Indicator")

	#def OnIdle(self):

		#self.dirtyRefreshMacros()

	def scaleValue(self, value, scaleIn, scaleOut):
		return ((value/scaleIn) * scaleOut)

	#def dirtyRefreshMacros(self):

		# print("On Dirty Refresh Macros")

		# for controlId in range(8):
		# 	eventID = device.findEventID(midi.EncodeRemoteControlID(device.getPortNumber(), 0, 0) + controlId, 1)
		# 	sVal = self.scaleValue(device.getLinkedValue(eventID), 1, 127)
		# 	#print("CID: ", controlId, "val: ", sVal)
		# 	self.UpdateKnobs(controlId, sVal)

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



FaderportV2 = TFaderportV2()

def OnInit():
	FaderportV2.OnInit()

def OnDeInit():
	FaderportV2.OnDeInit()

def OnMidiIn(event):
	FaderportV2.OnMidiIn(event)

def OnMidiMsg(event):
	FaderportV2.OnMidiMsg(event)

def OnControlChange(event):
	FaderportV2.OnControlChange(event)

# def OnNoteOn(event):
# 	FaderportV2.OnNoteOn(event)

# def OnNoteOff(event):
# 	FaderportV2.OnNoteOff(event)

#def OnIdle():
#	FaderportV2.OnIdle()

def OnMidiOutMsg(event):
	FaderportV2.OnMidiOutMsg(event)

def OnRefresh(Flags):
	FaderportV2.OnRefresh(Flags)

def OnDoFullRefresh(Flags):
	FaderportV2.OnDoFullRefresh(Flags)

def OnUpdateBeatIndicator(value):
	FaderportV2.OnUpdateBeatIndicator(value)
