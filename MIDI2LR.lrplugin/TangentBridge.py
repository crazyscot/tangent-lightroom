#!/usr/bin/env python
# Python 2 as that's what OSX provides

import binascii
import select
import socket
import struct
import os
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
            self.sendLR('GetPluginInfo', 1)
            # Mode: Develop
            # TODO: determine current mode & send that to panel?
            self.sendTangent(u4(0x85)+u4(1))

        elif cmd==2:
            param,incr = rd4(pkt,4), rd4f(pkt,8)
            name = Control.name_for(param)
            VALUES[param] += incr
            print('T< Param Change: %u (%s): %f -> %f'%(param,name,incr,VALUES[param]))
            self.sendLR(name, VALUES[param])

        elif cmd==4:
            param = rd4(pkt,4)
            name = Control.name_for(param)
            self.log('T< READ PARAM: %x (%s)'%(param,name))

            self.log('>>> GetValue %s'%name)
            self.sendLR('GetValue', name)
            # And the response will DTRT.

        # Button actions. We action on DOWN and ignore UP.
        elif cmd==8:
            action = rd4(pkt,4)
            name = Control.name_for(action)
            self.log('T< ACTION ON: %x (%s)'%(action,name))
            self.sendLR(name, '1')
        elif cmd==0xb:
            action = rd4(pkt,4)
            name = Control.name_for(action)
            self.log('T< ACTION OFF: %x (%s) (ignored)'%(action,name))

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

    def sendLR(self, param, value):
        self.LRSend.sendall("%s %s\n"%(param,value))

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
                id = Control.id_for(command)
                VALUES[id] = float(value)
                
                self.sendTangent(u4(0x82) + u4(id) + encf(VALUES[id]) + u4(0))
                # Caution! MIDI2LR use values 0..1 ... midi2lr has a xlation layer, need to play nicely with that. This is a job for the XML.
            except KeyError:
                pass

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
                self.LRSend.recv(4096) # this is just an 'ok' for each command; sink it

if __name__ == '__main__':
    # First argument is the path to the plugin Info.lua, which must be in the same dir as the XML files
    bridge = Bridge(sys.argv[0])
    bridge.run()
