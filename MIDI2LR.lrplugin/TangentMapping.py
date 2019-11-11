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
    def xml(self, indent=0):
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
    def __init__(self,id, name, name9=None, name14=None, name20=None):
        super(Action, self).__init__()
        self.id = id
        self.Name = name
        self.Name9 = name9 or name
        self.Name14 = name14 or name
        self.Name20 = name20 or name
        if len(self.Name9) > 9:
            self.Name9 = self.Name9[0:9]
        if len(self.Name14) > 14:
            self.Name14 = self.Name14[0:14]
        if len(self.Name20) > 20:
            self.Name20 = self.Name20[0:20]
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Action id="0x%08x">\n' % self.id
        rv += self.element('Name', indent+1)
        rv += self.optionals(['Name9', 'Name14', 'Name20'], indent+1)
        rv += baseindent + '</Action>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert self.Name is not None

class Parameter(XMLable):
    def __init__(self, id, name, name9=None, name10=None, name12=None, minval=0, maxval=1, stepsize=0.0001):
        super(Parameter, self).__init__()
        self.id = id
        self.Name = name
        self.Name9 = name9 or name
        self.Name10=name10 or name
        self.Name12=name12 or name
        if len(self.Name9) > 9:
            self.Name9 = self.Name9[0:9]
        if len(self.Name10) > 10:
            self.Name10 = self.Name10[0:10]
        if len(self.Name12) > 12:
            self.Name12 = self.Name12[0:12]
        self.MinValue=minval
        self.MaxValue=maxval
        self.StepSize=stepsize
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Parameter id="0x%08x">\n' % self.id
        rv += self.elements(['Name', 'MinValue', 'MaxValue', 'StepSize'], indent+1)
        rv += self.optionals(['Name9', 'Name10', 'Name12'], indent+1)
        rv += baseindent + '</Parameter>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert self.Name is not None

class Group(XMLable):
    def __init__(self, name, controls):
        super(Group, self).__init__()
        self.name = name
        self.controls = controls
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Group name="%s">\n' % self.name
        for a in self.controls:
            rv += a.xml(indent+1)
        rv += baseindent + '</Group>\n'
        return rv
    def check(self, controlsfile):
        assert self.name is not None
        assert self.controls is not None
        for c in self.controls:
            c.check(controlsfile)

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
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Mode id="0x%08x">\n' % self.id
        if self.Name:
            rv += self.element('Name', indent+1)
        if self.controlbanks:
            for cb in self.controlbanks:
                rv += cb.xml(indent+1)
        rv += baseindent + '</Mode>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        assert (self.Name and not self.controlbanks) or (self.controlbanks and not self.Name)
        if self.controlbanks:
            assert controlsfile is not None
            # our ID must be found in the controls file
            found=False
            for m in controlsfile.modes:
                if m.id == self.id:
                    found=True
                    break
            if not found:
                raise Error('mode id %08x not found in controls file'%self.id)
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
    def xml(self, indent):
        rv = FILEHEADER%'ControlSystem' + '''<Capabilities>
    <Jog enabled="true"/>
    <Shuttle enabled="false"/>
    <StatusDisplay lineCount="3"/>
    <CustomControls enabled="true"/>
  </Capabilities>
'''
        rv += TAB + '<Modes>\n'
        for m in self.modes:
            rv += m.xml(2)
        rv += TAB + '</Modes>\n'
        rv += TAB + '<Controls>\n'
        for g in self.groups:
            rv += g.xml(2)
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


##################################################################33
# MAP FILES

class Control(XMLable):
    # A control has a Type and a Number; then at least one Mapping within. Each Mapping contains a Key.
    # See Button and Encoder subclasses.
    def __init__(self, type, number, keyStd=None, keyAlt=None):
        self.type = type
        self.number = number
        self.keyStd = keyStd
        self.keyAlt = keyAlt
    def xml(self, indent):
        baseindent = TAB * indent
        rv = baseindent + '<Control type="%s" number="%d">\n' % (self.type, self.number)
        if self.keyStd:
            rv += baseindent + TAB + '<Mapping mode="Std">\n'
            rv += baseindent + TAB + TAB + '<Key>0x%08x</Key>\n' % self.keyStd
            # TODO add comment, what is it? look it up ...
            rv += baseindent + TAB + '</Mapping>\n'
        if self.keyAlt:
            rv += baseindent + TAB + '<Mapping mode="Alt">\n'
            rv += baseindent + TAB + TAB + '<Key>0x%08x</Key>\n' % self.keyAlt
            # TODO add comment, what is it? look it up ...
            rv += baseindent + TAB + '</Mapping>\n'
        rv += baseindent + '</Control>\n'
        return rv
    def check(self, controlsfile):
        assert self.type is not None
        assert self.number is not None

class Button(Control):
    def __init__(self, number, keyStd=None, keyAlt=None):
        super(Button, self).__init__('Button', number, keyStd, keyAlt)

class Encoder(Control):
    def __init__(self, number, keyStd=None, keyAlt=None):
        super(Encoder, self).__init__('Encoder', number, keyStd, keyAlt)

class Bank(XMLable):
    # A bank of one or more controls
    def __init__(self, controls):
        self.controls = controls
    def xml(self, indent):
        rv = TAB*indent + '<Bank>\n'
        for c in self.controls:
            rv += c.xml(indent+1)
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
    def xml(self, indent):
        rv = TAB*indent + '<ControlBank id="%s">\n'%self.id
        for b in self.banks:
            rv += b.xml(indent+1)
        rv += TAB*indent + '</ControlBank>\n'
        return rv
    def check(self, controlsfile):
        assert self.id is not None
        for b in self.banks:
            b.check(controlsfile)

class MapFile(XMLable):
    def __init__(self, panelType, modes):
        self.panelType = panelType
        self.modes = modes
    def xml(self, indent):
        rv = FILEHEADER%'PanelMap'
        rv += TAB*(indent+1) + '<Panels>\n'
        rv += TAB*(indent+2) + '<Panel type="%s">\n' % self.panelType
        for m in self.modes:
            rv += m.xml(indent+3)
        rv += TAB*(indent+2) + '</Panel>\n'
        rv += TAB*(indent+1) + '</Panels>\n'
        rv += FILEFOOTER
        return rv
    def check(self, controlsfile):
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
    # TODO: common sections


if __name__ == '__main__':
    # This is test code.. for the real outputs, see TangentMappingDefinitions
    t1 = Action(42, 'myACtion', name14='itsname14')
    #print(t1.xml(0))
    t2 = Parameter(69, 'myParam', name9='itsname9', maxval=1.5)
    #print(t2.xml(1))
    g = Group('mygroup', [t1,t2,t2])
    #print(g.xml(0))
    cf = ControlsFile([Mode(1,'Develop'), Mode(2,'Navigate')], [g, g])
    cf.check(None)
    #print(cf.xml(0))
    c = Button(10, 0x100, 0x101)
    #print(c.xml(0))
    e = Encoder(4, 0x200, 0x201)
    #print(e.xml(0))
    b = Bank([c,e])
    #print(b.xml(0))
    cb = ControlBank('Standard', [b])
    #print(cb.xml(0))
    m = Mode(1, controlBanks = [cb])
    m2 = Mode(2, controlBanks = [cb])
    #print(m.xml(0))
    mf = MapFile('Wave', [m, m2])
    mf.check(cf)
    print(mf.xml(0))

