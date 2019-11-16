#!/usr/bin/env python

import abc

# This Python2 module declares:
#   Objects to make it easier to specify control mappings
#   The list of all controls that we support (--> controls.xml)
#   The notion of "default" controls that are shared across all banks
#   A default mapping for the Wave (--> wave-map.xml)
#     (other panels could be added later)

TABSIZE=2
TAB = ' ' * TABSIZE

class XMLable(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.TYPES = {}

    @abc.abstractmethod
    def xml(self, indent=0, controlsfile=None):
        """
        Returns an XML representation of this object, starting at the given indent level.
        Indent levels are expressed as number of tabs (see TABSIZE).
        The result is a multi-line string.
        """
        pass
    def element(self, name, tabs=0):
        """
        Returns an element tag for a property of this object, optionally tabbed.
        Type is read from this object's TYPES dict; if not present, string assumed.
        """
        fmt='%s'
        if name in self.TYPES:
            fmt = self.TYPES[name]
        fmt = "<%s>" + fmt + "</%s>\n"
        return (tabs*TAB) + fmt%(name, self.__dict__[name], name)
    def elements(self, names, tabs=0):
        """
        Returns element tags for the requested list of members.
        """
        rv = []
        for a in names:
            rv.append(self.element(a, tabs))
        return ''.join(rv)

    def optionals(self, names, tabs=0):
        """
        Like elements, but doesn't mind if any are not present.
        """
        rv = []
        for a in names:
            if a in self.__dict__ and self.__dict__[a] is not None:
                rv.append(self.element(a, tabs))
        return ''.join(rv)

    @abc.abstractmethod
    def check(self, controlsfile):
        '''
        Performs sanity checks of this element and all its children.
        A ControlsFile must be given for elements within a Map File,
        in order to cross-reference.
        '''
        pass

##################################################################33
# CONTROLS FILES

class Action(XMLable):
    def __init__(self,id, name, panel=None, name9=None, name14=None, name20=None):
        super(Action, self).__init__()
        self.id = id
        self.Name = name
        self.panel = panel
        self.Name9 = name9 or panel or name
        self.Name14 = name14 or panel or name
        self.Name20 = name20 or panel or name
        if len(self.Name9) > 9:
            self.Name9 = self.Name9[0:9]
        if len(self.Name14) > 14:
            self.Name14 = self.Name14[0:14]
        if len(self.Name20) > 20:
            self.Name20 = self.Name20[0:20]
    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        rv  = baseindent + '<Action id="0x%08x">\n' % self.id
        rv += self.element('Name', indent+1)
        rv += self.optionals(['Name9', 'Name14', 'Name20'], indent+1)
        rv += baseindent + '</Action>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert self.Name is not None
    def __str__(self):
        return 'Action: %s'%self.Name

class Parameter(XMLable):
    def __init__(self, id, name, panel=None, name9=None, name10=None, name12=None, minval=0, maxval=1, stepsize=0.0001):
        super(Parameter, self).__init__()
        self.id = id
        self.Name = name
        self.panel = panel
        self.Name9 = name9 or panel or name
        self.Name10=name10 or panel or name
        self.Name12=name12 or panel or name
        if len(self.Name9) > 9:
            self.Name9 = self.Name9[0:9]
        if len(self.Name10) > 10:
            self.Name10 = self.Name10[0:10]
        if len(self.Name12) > 12:
            self.Name12 = self.Name12[0:12]
        self.MinValue=minval
        self.MaxValue=maxval
        self.StepSize=stepsize
    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        rv  = baseindent + '<Parameter id="0x%08x">\n' % self.id
        rv += self.elements(['Name', 'MinValue', 'MaxValue', 'StepSize'], indent+1)
        rv += self.optionals(['Name9', 'Name10', 'Name12'], indent+1)
        rv += baseindent + '</Parameter>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert self.Name is not None
    def __str__(self):
        return 'Parameter: %s'%self.Name

# a list of all menus, indexed by ID, so we can retrieve their contents efficiently
ALL_MENUS = {} # indexed by id

class Menu(XMLable):
    def __init__(self,id, name, verbs, panel=None, name9=None, name14=None, name20=None):
        # verbs is a dict, mapping DISPLAYNAME to MIDI2LR-VERB
        # e.g. {'Colour':'SetTreatmentColor', 'B&W':'SetTreatmentBW'}
        super(Menu, self).__init__()
        self.id = id
        self.Name = name
        self.verbs = verbs
        self.Name9 = name9 or panel or name
        self.Name14 = name14 or panel or name
        self.Name20 = name20 or panel or name
        if len(self.Name9) > 9:
            self.Name9 = self.Name9[0:9]
        if len(self.Name14) > 14:
            self.Name14 = self.Name14[0:14]
        if len(self.Name20) > 20:
            self.Name20 = self.Name20[0:20]
        assert id not in ALL_MENUS
        self.index = 0 # currently selected index; TODO can we read these out of LR?
        ALL_MENUS[id] = self
    def get(self):
        # returns a tuple (Display string, MIDI2LR verb)
        key = self.verbs.keys()[self.index]
        return (key,self.verbs[key])
    def change(self, incr):
        t=self.index + incr
        if t < 0:
            t = len(self.verbs)-1
        elif t >= len(self.verbs):
            t = 0
        self.index = t
        return self.get()
    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        rv  = baseindent + '<Menu id="0x%08x">\n' % self.id
        rv += self.element('Name', indent+1)
        rv += self.optionals(['Name9', 'Name14', 'Name20'], indent+1)
        rv += baseindent + '</Menu>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert self.Name is not None
        assert self.verbs is not None and len(self.verbs)>1
    def __str__(self):
        return 'Menu : %s %s'%(self.Name,self.verbs)

class Group(XMLable):
    def __init__(self, name, controls):
        super(Group, self).__init__()
        self.name = name
        self.controls = controls
    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        rv  = baseindent + '<Group name="%s">\n' % self.name
        for a in self.controls:
            rv += a.xml(indent+1, cf)
        rv += baseindent + '</Group>\n'
        return rv
    def check(self, controlsfile):
        assert self.name is not None
        assert self.controls is not None
        for c in self.controls:
            c.check(controlsfile)


RESERVED_CONTROLS = [
    Action(0x80000001, 'ALT'),
    Action(0x80000002, 'Next Knob Bank'),
    Action(0x80000003, 'Previous Knob Bank'),
    Action(0x80000004, 'Next Button Bank'),
    Action(0x80000005, 'Previous Button Bank'),
    Action(0x80000006, 'Next Trackerball Bank'),
    Action(0x80000007, 'Previous Trackerball Bank'),
    Action(0x80000008, '<reserved>'),
    Action(0x80000009, 'Next Mode'),
    Action(0x8000000a, 'Previous Mode'),
    Action(0x8000000b, 'Go To Mode'),
    Action(0x8000000c, 'Toggle Jog/Shuttle'),
    Action(0x8000000d, 'Toggle Mouse Emulation'),
    Action(0x8000000e, 'Keyboard Shortcut'),
    Action(0x8000000f, 'Show HUD'),
    Action(0x80000010, 'Goto Knob Bank'),
    Action(0x80000011, 'Goto Button Bank'),
    Action(0x80000012, 'Goto Trackerball Bank'),
    Action(0x80000013, 'Custom Action'),

    Parameter(0x81000001, 'Transport Ring'),
    Parameter(0x81000002, 'Keyboard Shortcut'),
    Parameter(0x81000003, 'Custom Parameter'),
]

class Mode(XMLable):
    # This class does double duty, holding both Mode definitions (in Controls files) and mappings (in Mapping files).
    def __init__(self, id, name=None, controlBanks=None):
        super(Mode, self).__init__()
        self.id = id
        self.Name = name
        self.controlbanks = controlBanks
        if name is None and controlBanks is None:
            raise Error('one of Name and ControlBanks is required')
        if name is not None and controlBanks is not None:
            raise Error('only one of Name and ControlBanks is allowed')
    def merge(self, sharedBanks):
        # sharedBanks is an array of ControlBank objects to merge in
        if self.controlbanks is None:
            raise Error('cannot merge when no ControlBanks are present')
        for cb in self.controlbanks: # for each bank ...
            for mcb in sharedBanks: # find a matching shared bank
                if mcb.id != cb.id:
                    continue
                # got it; merge in
                print('merging %s into %s'%(mcb.id, cb.id))
                if len(mcb.banks)>1:
                    raise Error('shared control bank %s has more than one bank; not supported' % mcb.id)
                for bnk in cb.banks:
                    bnk.controls.extend(mcb.banks[0].controls)
        # And the reverse mapping: a mode need not define all banks, but must still accept all shared banks
        for mcb in sharedBanks:
            found = False
            for cb in self.controlbanks:
                if mcb.id != cb.id:
                    continue
                found = True
            if not found:
                #raise Exception('shared control bank %s has nowhere to go in mode %08x'%(mcb.id, self.id))
                print('Creating control bank %s in mode %08x'%(mcb.id,self.id))
                self.controlbanks.append(mcb)

    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        namecomment = ''
        if not self.Name:
            namecomment = ' <!-- %s -->' % cf.find_mode(self.id).Name
        rv  = baseindent + '<Mode id="0x%08x">%s\n' % (self.id,namecomment)
        if self.Name:
            rv += self.element('Name', indent+1)
        if self.controlbanks:
            for cb in self.controlbanks:
                rv += cb.xml(indent+1, cf)
        rv += baseindent + '</Mode>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert (self.Name and not self.controlbanks) or (self.controlbanks and not self.Name)
        if self.controlbanks:
            assert controlsfile is not None
            # our ID must be found in the controls file
            found=False
            controlsfile.find_mode(self.id)
            for cb in self.controlbanks:
                cb.check(controlsfile)


FILEHEADER = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TangentWave fileType="%s" fileVersion="3.0">
'''

FILEFOOTER = "</TangentWave>"

class ControlsFile(XMLable):
    def __init__(self, modes, groups):
        super(ControlsFile, self).__init__()
        self.modes = modes
        self.groups = groups
    def xml(self, indent, cf):
        self.check(cf)
        rv = FILEHEADER%'ControlSystem' + '''<Capabilities>
    <Jog enabled="true"/>
    <Shuttle enabled="false"/>
    <StatusDisplay lineCount="3"/>
    <CustomControls enabled="true"/>
  </Capabilities>
'''
        rv += TAB + '<Modes>\n'
        for m in self.modes:
            rv += m.xml(2,cf)
        rv += TAB + '</Modes>\n'
        rv += TAB + '<Controls>\n'
        for g in self.groups:
            rv += g.xml(2,cf)
        rv += TAB + '</Controls>\n'
        rv += '''  <DefaultGlobalSettings>
    <KnobSensitivity std="1" alt="5"/>
    <JogDialSensitivity std="1" alt="5"/>
    <TrackerballSensitivity std="1" alt="5"/>
    <TrackerballDialSensitivity std="1" alt="5"/>
    <IndependentPanelBanks enabled="false"/>
  </DefaultGlobalSettings>
''' + FILEFOOTER
        lines = rv.split('\n')
        baseindent = TAB * indent
        return ''.join([ baseindent + l + '\n' for l in lines ])
    def check(self, controlsfile=None):
        for m in self.modes:
            m.check(controlsfile)
        for g in self.groups:
            g.check(controlsfile)
    def find_mode(self, id):
        for m in self.modes:
            if m.id == id:
                return m
        raise Exception('Mode 0x%08x not found'%id)
    def find_mode_index(self, id):
        for idx in range(len(self.modes)):
            if self.modes[idx].id == id:
                return idx
        raise Exception('Mode 0x%08x not found'%id)
    def find_control(self, id):
        for g in self.groups:
            for c in g.controls:
                if c.id == id:
                    return c
        for c in RESERVED_CONTROLS:
            if c.id == id:
                return c
        raise Exception('Control 0x%08x not found'%id)


##################################################################33
# MAP FILES

class Control(XMLable):
    # A control has a Type and a Number; then at least one Mapping within. Each Mapping contains a Key.
    # See Button and Encoder subclasses.
    def __init__(self, type, number, keyStd=None, keyAlt=None, argStd=None, argAlt=None):
        self.type = type
        self.number = number
        self.keyStd = keyStd
        self.keyAlt = keyAlt
        self.argStd = argStd
        self.argAlt = argAlt
    def xml(self, indent, cf):
        self.check(cf)
        baseindent = TAB * indent
        rv = baseindent + '<Control type="%s" number="%d">\n' % (self.type, self.number)
        if self.keyStd:
            rv += baseindent + TAB + '<Mapping mode="Std">\n'
            rv += baseindent + TAB + TAB + '<Key>0x%08x</Key> <!-- %s -->\n' % (self.keyStd, cf.find_control(self.keyStd))
            if self.argStd:
                rv += baseindent + TAB + TAB + '<Argument>0x%08x</Argument>\n' % self.argStd
            rv += baseindent + TAB + '</Mapping>\n'
        if self.keyAlt:
            rv += baseindent + TAB + '<Mapping mode="Alt">\n'
            rv += baseindent + TAB + TAB + '<Key>0x%08x</Key> <!-- %s -->\n' % (self.keyAlt, cf.find_control(self.keyAlt))
            if self.argAlt:
                rv += baseindent + TAB + TAB + '<Argument>0x%08x</Argument>\n' % self.argAlt
            rv += baseindent + TAB + '</Mapping>\n'
        rv += baseindent + '</Control>\n'
        return rv
    def check(self, controlsfile):
        assert self.type is not None
        assert self.number is not None

class Button(Control):
    def __init__(self, number, keyStd=None, keyAlt=None, argStd=None, argAlt=None):
        super(Button, self).__init__('Button', number, keyStd, keyAlt, argStd, argAlt)

class Encoder(Control):
    def __init__(self, number, keyStd=None, keyAlt=None, argStd=None, argAlt=None):
        super(Encoder, self).__init__('Encoder', number, keyStd, keyAlt, argStd, argAlt)

class Bank(XMLable):
    # A bank of one or more controls
    def __init__(self, controls):
        self.controls = controls
    def xml(self, indent, cf):
        self.check(cf)
        rv = TAB*indent + '<Bank>\n'
        for c in self.controls:
            rv += c.xml(indent+1,cf)
        rv += TAB*indent + '</Bank>\n'
        return rv
    def check(self, controlsfile):
        for c in self.controls:
            c.check(controlsfile)

class ControlBank(XMLable):
    # One or more banks, grouped by the type of control (Standard, Encoder, Button)
    def __init__(self, id, banks):
        self.id = id
        self.banks = banks
    def xml(self, indent, cf):
        self.check(cf)
        rv = TAB*indent + '<ControlBank id="%s">\n'%self.id
        for b in self.banks:
            rv += b.xml(indent+1,cf)
        rv += TAB*indent + '</ControlBank>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        for b in self.banks:
            b.check(controlsfile)

class MapFile(XMLable):
    def __init__(self, panelType, sharedControlBanks, modes):
        self.panelType = panelType
        self.modes = modes
        self.sharedControlBanks = sharedControlBanks
        for m in self.modes:
            m.merge(self.sharedControlBanks)
    def xml(self, indent, cf):
        self.check(cf)
        rv = FILEHEADER%'PanelMap'
        rv += TAB*(indent+1) + '<Panels>\n'
        rv += TAB*(indent+2) + '<Panel type="%s">\n' % self.panelType
        for m in self.modes:
            rv += m.xml(indent+3, cf)
        rv += TAB*(indent+2) + '</Panel>\n'
        rv += TAB*(indent+1) + '</Panels>\n'
        rv += FILEFOOTER
        return rv
    def check(self, controlsfile):
        assert controlsfile is not None
        assert self.panelType is not None
        for m in self.modes:
            m.check(controlsfile)
        for cm in controlsfile.modes:
            # every defined mode must be mapped
            found=False
            for m in self.modes:
                if m.id == cm.id:
                    found=True
                    break
            if not found:
                raise Exception('Mode 0x%08x (%s) in controls file not found in map for %s'%(cm.id, cm.Name, self.panelType))


if __name__ == '__main__':
    # This is test code.. for the real outputs, see TangentMappingDefinitions
    t1 = Action(42, 'myACtion', name14='itsname14')
    #print(t1.xml(0))
    t2 = Parameter(69, 'myParam', name9='itsname9', maxval=1.5)
    #print(t2.xml(1))
    mnu = Menu(77, 'mymenu', name9='menu9', verbs=['foo','bar','baz'])
    #print(mnu.xml(1, None))
    g = Group('mygroup', [t1,t2,Action(0x100, 'foo'),Action(0x101, 'bar'),Action(0x200,'baz'),Action(0x201,'qux'),Action(0xfff,'qix'), mnu])
    #print(g.xml(0))
    cf = ControlsFile([Mode(1,'Develop'), Mode(2,'Navigate')], [g, g])
    cf.check(None)
    #print(cf.xml(0,cf))
    c = Button(10, 0x100, 0x101, argStd=0x42, argAlt=0x43)
    #print(c.xml(0,cf))
    e = Encoder(4, 0x200, 0x201)
    #print(e.xml(0))
    b = Bank([c,e])
    #print(b.xml(0))
    cb = ControlBank('Standard', [b])
    cb2 = ControlBank('Standard', [Bank([ Button(32, 0xfff) ])])
    #print(cb.xml(0))
    m = Mode(1, controlBanks = [cb])
    m2 = Mode(2, controlBanks = [ControlBank('Standard', [Bank([c,e])])]) # needs to be a deep clone, so the shared logic doesn't duplicate
    #print(m.xml(0))
    mf = MapFile('Wave', [cb2], [m, m2])
    mf.check(cf)
    print(mf.xml(0, cf))

