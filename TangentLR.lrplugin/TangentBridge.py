#!/usr/bin/env python
# Written to work on both Python 2 and 3 (OSX provides 2.7)

import binascii
import os
import select
import socket
import struct
import sys
if sys.version_info[0] < 3:
    import Queue
    PYTHON3=False
else:
    import queue as Queue
    PYTHON3=True

from TangentMapping import ALL_MENUS
import TangentMappingDefinitions

TANGENT_PORT = 64246
# of course, lrsend and lrecv ports are the opposite way round to what's in the lua side
LRSEND_PORT = 54778
LRRECV_PORT = 54779

APPNAME = 'Adobe Lightroom Classic'

def connect(port, address='127.0.0.1'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address,port))
    return sock

# Packet wrangling syntactic sugar
def rd4(seq, pos=0):
    return struct.unpack(">i", seq[pos:pos+4])[0]
def rd4f(seq, pos=0):
    return struct.unpack(">f", seq[pos:pos+4])[0]
def rd4multi(seq, pos, n):
    return [ rd4(seq, pos*i+4) for i in range(n)]
def u4(i):
    return bytearray(struct.pack('>i', i))
def rdstr(seq,pos):
    # returns (string, how far to advance the stream)
    length = rd4(seq,pos)
    return seq[pos+4:pos+4+length], 4+length
def encstr(s):
    if type(s) is str and PYTHON3:
        s = bytes(s, 'utf-8')
    return u4(len(s)) + s
def encf(f):
    return bytearray(struct.pack('>f', f))

def split(seq, length=4):
    ''' splits data into words '''
    return [seq[i:i+length] for i in range(0, len(seq), length)]
def hexdump(seq, length=4):
    ''' dumps data as words, for debug '''
    return [(binascii.hexlify(x)) for x in split(seq,length)]

##############################################################

# Mapping from control IDs (defined in controls.xml) to LR parameters (strings the plugin is expecting)

class Control(object):
    by_name = {}
    by_id = {}

    def __init__(self, id, name):
        self.id = id
        self.name = name

        Control.by_name[name] = self
        Control.by_id[id] = self

    @staticmethod
    def name_for(id):
        return Control.by_id[id].name

    @staticmethod
    def id_for(name):
        return Control.by_name[name].id

ALL_CONTROLS = []
for group in TangentMappingDefinitions.controls.groups:
    for ctrl in group.controls:
        ALL_CONTROLS.append(Control(ctrl.id, ctrl.Name))

# Current values, indexed by ID [for now]
VALUES = {}

ALL_MODES = TangentMappingDefinitions.controls.modes

##############################################################

class Bridge(object):
    def __init__(self, pluginPath):
        self.pluginInfo = pluginPath
        self.pluginDir = os.path.abspath(os.path.dirname(pluginPath))
        # Initialise these first in case connection fails
        self.Tangent = None
        self.LRSend = None
        self.LRRecv = None
        self.lrQueue = Queue.Queue()
        self.lrSendInProgress= False
        self.udsm = 0
        self.log('Starting up, plugin dir is %s'%self.pluginDir)
        self.connectAll()

    def __del__(self):
        self.closeAll()

    def connectAll(self):
        self.closeAll()
        self.Tangent = connect(TANGENT_PORT)
        self.Tangent.setblocking(False)
        self.LRSend = connect(LRSEND_PORT)
        self.LRSend.setblocking(False)
        self.LRRecv = connect(LRRECV_PORT)
        self.LRRecv.setblocking(False)

    def closeAll(self):
        if self.Tangent:
            self.Tangent.close()
        if self.LRSend:
            self.LRSend.close()
        if self.LRRecv:
            self.LRRecv.close()

    def log(self, msg):
        print(msg)
        # TODO: write to logfile?

    # -----------------------------------------------------------------
    # Tangent logic

    def sendTangent(self, pkt):
        ''' Sends a Tangent packet. This function takes care of sending the length word. '''
        s = self.Tangent
        s.sendall(u4(len(pkt)))
        pkt = bytearray(pkt)
        s.sendall(pkt)

    def changeMode(self, mode):
        self.log('ChangeMode %08x'%mode)
        self.sendTangent(u4(0x85) + u4(mode))
        self.modeIndex = TangentMappingDefinitions.controls.find_mode_index(mode)
        self.log('new index %d'%self.modeIndex)
    def nextMode(self, step):
        prev = self.modeIndex
        self.modeIndex += step
        if self.modeIndex >= len(ALL_MODES):
            self.modeIndex = 0
        if self.modeIndex < 0:
            self.modeIndex = len(ALL_MODES) - 1
        newMode = ALL_MODES[self.modeIndex]
        self.log('NextMode index %d + %d --> index %d, id %08x'%(prev, step, self.modeIndex, newMode.id))
        self.changeMode(newMode.id)

    def handleTangent(self, pkt):
        ''' Deal with a single Tangent command '''
        cmd = rd4(pkt)
        if cmd==1:
            protocol, npanels = rd4multi(pkt, 4, 2)
            self.log('Tangent Initiate Comms: protocol %d, %d panels'%(protocol,npanels))
            # We don't really care about the panel type data
            self.sendTangent(u4(0x81) + encstr(APPNAME) + encstr(self.pluginDir) + encstr(''))
            #self.sendLR('GetPluginInfo', 1)
            # Initial Mode: Colour/Tone
            self.changeMode(1)
            self.sendLR('SwToMdevelop', 1)

        # Mode switching
        elif cmd==9:
            mode = rd4(pkt, 4)
            self.log('CHANGE MODE: %08x'%mode)
            self.changeMode(mode)
            self.sendLR('SwToMdevelop', 1)

        # Parameters. Note that these always range from 0 to 1 in midi2lr's world; it keeps a mapping.
        elif cmd==2:
            param,incr = rd4(pkt,4), rd4f(pkt,8)
            if param & 0x40000000:
                return self.encoderCustom(param, incr=incr)
            name = Control.name_for(param)
            if param not in VALUES:
                VALUES[param]=0.5 # safeish default?
                self.log('!!! no param for ' + name)
                self.sendLR('GetValue', name)
            VALUES[param] += incr
            self.log('T< Param Change: 0x%x (%s): %f -> %f'%(param,name,incr,VALUES[param]))
            self.sendLR(name, VALUES[param])
        elif cmd==4:
            param = rd4(pkt,4)
            name = Control.name_for(param)
            self.log('T< READ PARAM: 0x%x (%s)'%(param,name))
            if param & 0x40000000:
                return self.encoderCustom(param)
            #self.log('>>> GetValue %s'%name)
            self.sendLRQueued('GetValue', name)
            # And the response will DTRT (--> 0x82)
        elif cmd==3: # Reset param (knob pushed)
            param = rd4(pkt,4)
            name = Control.name_for(param)
            self.log('T< RESET PARAM: 0x%x (%s)'%(param,name))
            if param & 0x40000000:
                return self.encoderCustom(param, reset=True)
            self.sendLR('Reset'+name, '1')

        # Custom Parameters.
        elif cmd==0x36:
            name,offset = rdstr(pkt, 4)
            incr = rd4f(pkt, 4+offset)
            self.log('T< CUSTOM PARAM: %s, %f'%(name,incr))
            VALUES[name] += incr
            self.log('T< Param Change: %s: %f -> %f'%(name,incr,VALUES[name]))
            self.sendLR(name, VALUES[name])
        elif cmd==0x37:
            name,_ = rdstr(pkt, 4)
            self.log('T< CUSTOM PARAM RESET: %s'%name)
            self.sendLR('Reset'+name, '1')
        elif cmd==0x38:
            name,_ = rdstr(pkt, 4)
            self.log('T< READ CUSTOM PARAM: %s'%name)
            self.sendLRQueued('GetValue', name)
            # And the response will DTRT (--> 0xa6)

        # Button actions. We generally action on DOWN and ignore UP, but there are special cases.
        elif cmd==8:
            action = rd4(pkt,4)
            if action & 0x40000000:
                self.buttonCustom(action, up=False)
                return
            name = Control.name_for(action)
            self.log('T< ACTION ON: 0x%x (%s)'%(action,name))
            self.sendLR(name, '1')
        elif cmd==0xb:
            action = rd4(pkt,4)
            if action & 0x40000000:
                self.buttonCustom(action, up=True)
                return
            name = Control.name_for(action)
            self.log('T< ACTION OFF: 0x%x (%s) (ignored)'%(action,name))
        elif cmd==0x3c:
            name,_ = rdstr(pkt, 4)
            self.log('T< CUSTOM ACTION ON: %s'%name)
            self.sendLR(name, '1')
        elif cmd==0x3d:
            name,_ = rdstr(pkt, 4)
            self.log('T< CUSTOM ACTION OFF: %s'%name)


        # Transport Ring. We use jog mode only.
        elif cmd==0xa:
            jog,shutl = rd4multi(pkt, 4, 2)
            self.log('T< TRANSPORT: jog %d, shuttle %d'%(jog,shutl))
            if jog<0:
                for i in range(-jog):
                    self.sendLR('Prev','1')
            else:
                for i in range(jog):
                    self.sendLR('Next','1')

        elif cmd==5:
            id,incr = rd4multi(pkt, 4, 2)
            display,verb = ALL_MENUS[id].change(incr)
            self.log('T< MENU CHANGE: %08x, incr %d --> %s'%(id,incr,display))
            self.log('>>> %s'%verb)
            self.sendLR(verb, '1')
            self.sendTangent(u4(0x83)+u4(id)+encstr(display)+u4(0))
        elif cmd==6:
            id = rd4(pkt, 4)
            mnu = ALL_MENUS[id]
            mnu.index = 0
            display, verb = mnu.get()
            self.log('T< MENU RESET: %08x --> %s'%(id,display))
            self.log('>>> %s'%verb)
            self.sendLR(verb, '1')
            self.sendTangent(u4(0x83)+u4(id)+encstr(display)+u4(0))
        elif cmd==7:
            id = rd4(pkt, 4)
            display, _= ALL_MENUS[id].get()
            self.log('T< MENU STRING REQ: %08x --> %s'%(id,display))
            self.sendTangent(u4(0x83)+u4(id)+encstr(display)+u4(0))

        else:
            self.log('T< ??? (0x%x): %s'%(cmd, hexdump(pkt[4:])))

    def inboundTangent(self):
        ''' Process inbound data from Tangent '''
        s = self.Tangent
        raw = None
        try:
            raw = s.recv(4)
        except socket.error as e:
            self.log('Tangent socket closed (%s); bailing' % e)
            self.halt = True
            return
        dlen = rd4(raw)
        data = s.recv(dlen)
        self.handleTangent(data)

    # Custom logic
    def upDownStateMachine(self, key, keyUp):
        # key is 1 for up arrow, 2 for down arrow
        # keyUp is True for key up

        # STATES:
        #  0 = both released; Up -> 1, Down -> 2
        #  1 = Up pressed; UpRelease -> 0 & change mode; Down -> 3
        #  2 = Down pressed; DownRelease -> 0 & change mode; Up -> 3
        #  3 = Both pressed - action on entry; UpRelease -> 4; DownRelease -> 5
        #  4 = DrainingDown; Up -> 3; DownRelease -> 0
        #  5 = DrainingUp; Down -> 3; UpRelease -> 0

        previousState = self.udsm
        if self.udsm==0: # Both keys released
            if keyUp:
                return # ignore Up events, shouldn't happen
            self.udsm = key
        elif self.udsm==1: # Up already pressed
            if key==1 and keyUp:
                self.nextMode(-1)
                self.udsm = 0
            if key==2 and not keyUp:
                self.udsm=3
        elif self.udsm==2: # Down already pressed
            if key==2 and keyUp:
                self.nextMode(1)
                self.udsm = 0
            if key==1 and not keyUp:
                self.udsm = 3
        elif self.udsm==3: # Both pressed
            if not keyUp:
                return # ignore Down events, shouldn't happen
            if key==1:
                self.udsm = 4
            else:
                self.udsm = 5
        elif self.udsm==4: # Down pressed, draining
            if key==1 and not keyUp:
                self.udsm=3
            if key==2 and keyUp:
                self.udsm=0
        elif self.udsm==5: # Up pressed, draining
            if key==2 and not keyUp:
                self.udsm=3
            if key==1 and keyUp:
                self.udsm=0
        # State entry actions
        if self.udsm == 3 and previousState != 3:
            self.changeMode(100) # menu

    def buttonCustom(self, action, up):
        if action==0x40000001:
            self.upDownStateMachine(1, up)
        elif action==0x40000002:
            self.upDownStateMachine(2, up)
        else:
            self.log('Unhandled custom button action %08x'%action)

    def encoderCustom(self, param, incr=None, reset=False):
        if action==0x40000003:
            # Acknowledge, but otherwise ignore
            self.sendTangent(u4(0x82) + u4(action) + encf(0.5) + u4(0))
        else:
            self.log('Unhandled custom encoder action %08x'%action)

    # -----------------------------------------------------------------
    # MIDI2LR logic

    def runLRSendQ(self):
        if not self.lrSendInProgress:
            try:
                item = self.lrQueue.get(False)
                self.lrSendInProgress = True
                if PYTHON3:
                    item = bytes(item,'utf-8')
                self.LRSend.sendall(item)
            except Queue.Empty:
                pass

    def sendLR(self, param, value):
        msg="%s %s\n"%(param,value)
        if PYTHON3:
            msg = bytes(msg, 'utf-8')
        self.LRSend.sendall(msg)

    def sendLRQueued(self, param, value):
        # LR can't cope with too many messages at once, so queue them
        self.lrQueue.put("%s %s\n"%(param,value))
        self.runLRSendQ()

    def handleLR(self, message):
        ''' Deal with a single Midi2LR request '''
        #self.log('<<< %s'%message)
        command,value = message.split(b' ',1)
        if PYTHON3:
             command = command.decode('ascii')
        if value == b'':
            value = None
        else:
            value=float(value)
        if value is None and command != b'TerminateApplication':
            self.log('Received message without value: %s'%command)
        elif command == b'SwitchProfile':
            # WRITEME
            self.log('<<< SWITCH PROFILE %s (ignored)'%value)
        elif command == b'TerminateApplication':
            self.log('<<< TERMINATE (bye!)')
            self.halt = True
        elif command == b'Log':
            self.log('<<< LOG: %s'%value)
        elif command == b'SendKey':
            self.log('<<< SENDKEY %s (ignored)'%value)
            # TODO: This is used to send fake keystrokes to the app
        else:
            self.log('<<< PARAM: %s -> %s (->Tangent)'%(command,value))
            try:
                id = Control.id_for(command) # may fail with KeyError
                VALUES[id] = float(value)
                self.sendTangent(u4(0x82) + u4(id) + encf(VALUES[id]) + u4(0))
                # Caution! MIDI2LR uses values 0..1 ... midi2lr has a xlation layer, need to play nicely with that. This is a job for the XML.
            except KeyError:
                # Assume it's a custom param
                VALUES[command] = float(value)
                self.sendTangent(u4(0xa6) + encstr(command) + encf(float(value)) + u4(0))

    def inboundLR(self):
        ''' Process inbound data from MIDI2LR '''
        msg = None
        try:
            msg = self.LRRecv.recv(4096)
        except socket.error as e:
            self.log('LR inbound socket closed (%s); bailing' % e)
            self.halt = True
            return
        # commands are strings, terminated with \n
        packets = msg.split(b'\n')
        for p in packets:
            if len(p):
                self.handleLR(p)
        self.lrSendInProgress = False
        self.runLRSendQ()

    # -----------------------------------------------------------------

    def run(self):
        ''' Main loop, runs until termination command received '''
        tangent = self.Tangent.fileno()
        lrrx = self.LRRecv.fileno()
        lrtx = self.LRSend.fileno()
        self.halt = False
        while not self.halt:
            socketList = [ tangent, lrtx, lrrx ]
            rlist,_,_ = select.select( socketList, [], [] )
            if tangent in rlist:
                self.inboundTangent()
            if lrrx in rlist:
                self.inboundLR()
            if lrtx in rlist:
                # this is an 'ok' for each command, which we just sink
                _ = self.LRSend.recv(128)

if __name__ == '__main__':
    # First argument is the path to the plugin Info.lua, which must be in the same dir as the XML files. If not given, it's assumed to be the directory this file lives in.
    bridge = Bridge(sys.argv[0])
    bridge.run()
