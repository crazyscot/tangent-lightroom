#!/usr/bin/env python
# Python 2 as that's what OSX provides

import binascii
import os
import Queue
import select
import socket
import struct
import sys

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
    return struct.pack('>i', i)
def rdstr(seq,pos):
    # returns (string, how far to advance the stream)
    length = rd4(seq,pos)
    return seq[pos+4:pos+4+length], 4+length
def encstr(s):
    return u4(len(s)) + s
def encf(f):
    return struct.pack('>f', f)

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

ALL_CONTROLS = [
    Control(0x10001, 'Prev'),
    Control(0x10002, 'Next'),

    Control(0x20001, 'Temperature'),
    Control(0x20002, 'Tint'),
    Control(0x20004, 'Highlights'),
    Control(0x20005, 'Shadows'),
]
# TODO: This is temporary. Likely better to read commands from the XML.

# Current values, indexed by ID [for now]
VALUES = {}


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
        s.sendall(pkt)

    def handleTangent(self, pkt):
        ''' Deal with a single Tangent command '''
        cmd = rd4(pkt)
        if cmd==1:
            protocol, npanels = rd4multi(pkt, 4, 2)
            self.log('Tangent Initiate Comms: protocol %d, %d panels'%(protocol,npanels))
            # We don't really care about the panel type data
            self.sendTangent(u4(0x81) + encstr(APPNAME) + encstr(self.pluginDir) + encstr(''))
            #self.sendLR('GetPluginInfo', 1)
            # Mode: Develop
            # TODO: determine current mode & send that to panel?
            self.sendTangent(u4(0x85)+u4(1))

        # Parameters. Note that these always range from 0 to 1 in midi2lr's world; it keeps a mapping.
        elif cmd==2:
            param,incr = rd4(pkt,4), rd4f(pkt,8)
            name = Control.name_for(param)
            VALUES[param] += incr
            print('T< Param Change: 0x%x (%s): %f -> %f'%(param,name,incr,VALUES[param]))
            self.sendLR(name, VALUES[param])
        elif cmd==4:
            param = rd4(pkt,4)
            name = Control.name_for(param)
            self.log('T< READ PARAM: 0x%x (%s)'%(param,name))
            #self.log('>>> GetValue %s'%name)
            self.sendLRQueued('GetValue', name)
            # And the response will DTRT (--> 0x82)
        elif cmd==3: # Reset param (knob pushed)
            param = rd4(pkt,4)
            name = Control.name_for(param)
            self.log('T< RESET PARAM: 0x%x (%s)'%(param,name))
            self.sendLR('Reset'+name, '1')

        # Custom Parameters.
        elif cmd==0x36:
            name,offset = rdstr(pkt, 4)
            incr = rd4f(pkt, 4+offset)
            self.log('T< CUSTOM PARAM: %s, %f'%(name,incr))
            VALUES[name] += incr
            print('T< Param Change: %s: %f -> %f'%(name,incr,VALUES[name]))
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

        # Button actions. We action on DOWN and ignore UP.
        elif cmd==8:
            action = rd4(pkt,4)
            name = Control.name_for(action)
            self.log('T< ACTION ON: 0x%x (%s)'%(action,name))
            self.sendLR(name, '1')
        elif cmd==0xb:
            action = rd4(pkt,4)
            name = Control.name_for(action)
            self.log('T< ACTION OFF: 0x%x (%s) (ignored)'%(action,name))

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

    # -----------------------------------------------------------------
    # MIDI2LR logic

    def runLRSendQ(self):
        if not self.lrSendInProgress:
            try:
                item = self.lrQueue.get(False)
                self.lrSendInProgress = True
                #print('>>> %s'%item.strip())
                self.LRSend.sendall(item)
            except Queue.Empty:
                pass

    def sendLR(self, param, value):
        self.LRSend.sendall("%s %s\n"%(param,value))

    def sendLRQueued(self, param, value):
        # LR can't cope with too many messages at once, so queue them
        self.lrQueue.put("%s %s\n"%(param,value))
        self.runLRSendQ()

    def handleLR(self, message):
        ''' Deal with a single Midi2LR request '''
        #self.log('<<< %s'%message)
        command,value = message.split(' ',1)
        if value=='' and command != 'TerminateApplication':
            self.log('Received message without value: %s'%command)
        elif command == 'SwitchProfile':
            # WRITEME
            self.log('<<< SWITCH PROFILE %s (ignored)'%value)
        elif command == 'TerminateApplication':
            self.log('<<< TERMINATE (bye!)')
            self.halt = True
        elif command == 'Log':
            self.log('<<< LOG: %s'%value)
        elif command == 'SendKey':
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
        packets = msg.split('\n')
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
    # First argument is the path to the plugin Info.lua, which must be in the same dir as the XML files
    bridge = Bridge(sys.argv[0])
    bridge.run()
