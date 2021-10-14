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
PN_MODE = 0
MASTER_MODE = False
LOCK_MODE = False
IDLE_COUNT = 0
TEMP_COUNT = 0
PULSE_VAL = 0
LOCK_INDEX = -1
HINT_MSG = "nothing"
PREV_HINT_MSG = "nothing"

#TODO
#change Prev() next() to ui.scrollWindow when version 13 comes out
#channel rack mute solo
#fast forward / rewind buttons
#make knob handler funciton. if inc > 0 -> round(val / inc) * inc else round(val * (1))//inc(1/inc)
#remote link setup stuff

class TFaderportV2:

	def OnInit(self):
		print("On Init")
		self.BTN = self.BTN()
		self.STATUS = self.STATUS()
		self.ENC = self.ENC()
		self.PN = self.PN()
		self.WINDOW = self.WINDOW()
		global ENC_MODE, PN_MODE
		ENC_MODE = self.ENC.PAN
		PN_MODE = self.PN.MIXER
		self.OnRefresh(0)

	def OnDeInit(self):
		print("On De Init")
		
	def OnMidiIn(self, event):

		print("On Midi In")
		print("Status: ", event.status, "Data1: ", event.data1, "Data2: ", event.data2)
		
		global ENC_MODE, SHIFT_MOMENTARY, MASTER_MODE, LOCK_MODE, KNOB_MOMENTARY, HINT_MSG, PREV_HINT_MSG, LOCK_INDEX

		event.handled = True
				
		getVol, getPan, curIndex = self.getVolPan(LOCK_INDEX)
		setVol = getVol
		setPan = getPan
		
		if event.status == self.STATUS.FADER:
			intVol = self.scaleValue(event.data2, 127, (2 if ENC_MODE == self.ENC.FLIP else 1))
			fracVol = self.scaleValue(event.data1, 127, 1)/100
			mVol = intVol + fracVol
			if ENC_MODE == self.ENC.FLIP:
				setPan = mVol-1
			else:
				setVol = mVol

		elif event.status == self.STATUS.KNOB:
			
			knobVal = 64-event.data2 if event.data2 > 64 else event.data2
			print('eventdata2 ', event.data2)
			knobVal = knobVal * 4 if KNOB_MOMENTARY else knobVal

			if ENC_MODE == self.ENC.LINK:
				event.handled = False
				controlId = 7
				eventID = device.findEventID(midi.EncodeRemoteControlID(device.getPortNumber(), 0, 0) + controlId, 1)
				value = device.getLinkedValue(eventID)
				print('value : ',value)
				sVal = round(self.scaleValue(value, 1, 127))
				print('sval ',sVal)
				if SHIFT_MOMENTARY:
					increment = 16	
					r1Val = round(sVal/increment)*increment
					r2Val = r1Val + increment if knobVal > 0 else r1Val - increment
					dVal = abs(r2Val - sVal)
					tempData2 = r1Val if dVal > increment else r2Val			
				else:
					tempData2 = sVal + knobVal
				print('knonbval ',knobVal)
				print('tempdata2 ',tempData2)
				if tempData2 < 0:
					event.data2 = 0
				elif tempData2 > 127:
					event.data2 = 127
				else:
					event.data2 = tempData2
				
				event.data1 = controlId
				device.processMIDICC(event)
				#print("Status: ", event.status, "Data1: ", event.data1, "Data2: ", event.data2)
			if ENC_MODE == self.ENC.PAN:
				if SHIFT_MOMENTARY:
					increment = 0.25
					scaledPan = round((getPan) * 4)/4
					roundedPan = scaledPan + increment if knobVal > 0 else scaledPan - increment
					deltaPan = abs(roundedPan - getPan)
					setPan = scaledPan if deltaPan > increment else roundedPan			
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
					sPos = round(sPosAbsTicks/inc) * inc
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
					rVol = sVol + inc if knobVal > 0 else sVol - inc
					rVol = round(rVol,1)
					dVol = round(abs(rVol - getVol),2)
					setVol = sVol if dVol > inc else rVol		
				else:
					setVol =  getVol + (knobVal/100)
			
			elif ENC_MODE == self.ENC.ZOOM:
				ui.setFocused(self.WINDOW.PLAYLIST)
				if SHIFT_MOMENTARY:
					ui.verZoom(knobVal)
				else:
					ui.horZoom(knobVal)
				
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
				elif (event.controlNum == self.BTN.LINK_LOCK):
					if SHIFT_MOMENTARY:
						LOCK_MODE = LOCK_MODE ^ True
						LOCK_INDEX = curIndex if LOCK_MODE else -1
						HINT_MSG = str("Lock Mode ON" if LOCK_MODE else "Lock Mode OFF")				
					else:
						ENC_MODE = self.ENC.LINK
				elif (event.controlNum == self.BTN.PAN_FLIP):
					ENC_MODE = self.ENC.FLIP if (SHIFT_MOMENTARY and ENC_MODE == self.ENC.PAN) else self.ENC.PAN
				elif (event.controlNum == self.BTN.CHANNEL_LOCK):
					ENC_MODE = self.ENC.CH_LOCK if SHIFT_MOMENTARY else self.ENC.CHANNEL
				elif (event.controlNum == self.BTN.SCROLL_ZOOM):
					ENC_MODE = self.ENC.ZOOM if SHIFT_MOMENTARY else self.ENC.SCROLL
				elif (event.controlNum == self.BTN.MASTER_F1):
					if SHIFT_MOMENTARY: 
						transport.globalTransport(midi.FPT_F9,1)
					else: 
						MASTER_MODE = MASTER_MODE ^ True
						getVol, getPan, curIndex = self.getVolPan()
						setVol = getVol
						setPan = getPan
				elif (event.controlNum == self.BTN.CLICK_F2):
					if SHIFT_MOMENTARY: transport.globalTransport(midi.FPT_F6,1)
					else: transport.globalTransport(midi.FPT_Metronome,1)
				elif (event.controlNum == self.BTN.SECTION_F3):
					if SHIFT_MOMENTARY: transport.globalTransport(midi.FPT_MarkerSelJog,1)
					else: transport.globalTransport(midi.FPT_MarkerJumpJog,1)
				elif (event.controlNum == self.BTN.MARKER_F4):
					if SHIFT_MOMENTARY: transport.globalTransport(midi.FPT_F5,1)
					else: transport.globalTransport(midi.FPT_AddMarker,1)
				
				elif (event.controlNum == self.BTN.PLAY): 			transport.start()
				elif (event.controlNum == self.BTN.STOP):			transport.stop()
				elif (event.controlNum == self.BTN.RECORD):			transport.record()
				elif (event.controlNum == self.BTN.LOOPMODE):		transport.setLoopMode()
				elif (event.controlNum == self.BTN.MUTE_CLEAR):		mixer.muteTrack(curIndex)
				elif (event.controlNum == self.BTN.SOLO_CLEAR):		mixer.soloTrack(curIndex)
				elif (event.controlNum == self.BTN.ARM_ALL):		mixer.armTrack(curIndex)

		if (setVol != getVol) or (setPan != getPan):
			self.setVolPan(setVol, setPan, curIndex)

		self.OnRefresh(0)

	def OnRefresh(self, flags):

		if device.isAssigned():
			print("On Refresh")

			global PN_MODE, HINT_MSG, PREV_HINT_MSG, TEMP_COUNT, LOCK_INDEX

			getVol, getPan, curIndex = self.getVolPan(LOCK_INDEX)
			getPan = getPan + 1
			
			sVol = math.modf(self.scaleValue((getPan if ENC_MODE == self.ENC.FLIP else getVol), (2 if ENC_MODE == self.ENC.FLIP else 1), 127))
			fracVol = round(self.scaleValue(sVol[0], 1, 127))
			intVol = round(sVol[1])
			self.UpdateFader(fracVol, intVol)

			self.UpdateLEDs(self.BTN.SOLO_CLEAR, (127 if mixer.isTrackSolo(curIndex) else 0))
			self.UpdateLEDs(self.BTN.MUTE_CLEAR, (0 if mixer.isTrackEnabled(curIndex) else 127))
			self.UpdateLEDs(self.BTN.ARM_ALL, (127 if mixer.isTrackArmed(curIndex) else 0))
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
			
			if not LOCK_MODE:
				if ui.getFocused(0): PN_MODE = self.PN.MIXER 
				elif ui.getFocused(1): PN_MODE = self.PN.CHANNEL

			if (HINT_MSG != PREV_HINT_MSG):
				ui.setHintMsg(HINT_MSG)
				PREV_HINT_MSG = HINT_MSG

	# def OnUpdateBeatIndicator(self):

	# 	print("On Update Beat Indicator")

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
		if PN_MODE == self.PN.MIXER: 
			mixer.setTrackNumber(mixer.trackNumber() + 1 if mixer.trackNumber() < 126 else 0)
			#no worky in 20.8.4 ui.scrollWindow(self.WINDOW.MIXER,mixer.trackNumber())
		elif PN_MODE == self.PN.CHANNEL: 
			channels.selectOneChannel(channels.channelNumber() + 1 if (channels.channelNumber()+1) < channels.channelCount() else 0)
		else: transport.globalTransport(midi.FPT_Next,1)
	
	def Previous(self):
		print(mixer.trackNumber()-1)
		if PN_MODE == self.PN.MIXER: mixer.setTrackNumber(mixer.trackNumber() - 1 if mixer.trackNumber() > 0 else 126) 
		elif PN_MODE == self.PN.CHANNEL: channels.selectOneChannel(channels.channelNumber() - 1 if channels.channelNumber() > 0 else channels.channelCount()-1)
		else: transport.globalTransport(midi.FPT_Previous,1)
	
	def getVolPan(self, indexOverride):
		if (PN_MODE == self.PN.MIXER) or MASTER_MODE:
			if MASTER_MODE: i = 0
			elif indexOverride >= 0: i = indexOverride
			else: i = mixer.trackNumber()
			pan = mixer.getTrackPan(i)
			vol = mixer.getTrackVolume(i)
		elif PN_MODE == self.PN.CHANNEL:
			i = indexOverride if indexOverride > 0 else channels.channelNumber()
			pan = channels.getChannelPan(i)
			vol = channels.getChannelVolume(i)
		return vol, pan, i
	
	def setVolPan(self, vol, pan, i):
		if (PN_MODE == self.PN.MIXER) or MASTER_MODE:
			mixer.setTrackPan(i, pan)
			mixer.setTrackVolume(i, vol)
		elif PN_MODE == self.PN.CHANNEL:
			channels.setChannelPan(i, pan)
			channels.setChannelVolume(i, vol)

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

# def OnUpdateBeatIndicator(value):
# 	FaderportV2.OnUpdateBeatIndicator(value)
