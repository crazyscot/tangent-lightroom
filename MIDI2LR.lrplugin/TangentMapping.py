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

class Action(XMLable):
    def __init__(self,id, name, name9=None, name14=None, name20=None):
        super(Action, self).__init__()
        self.id = id
        self.Name = name
        self.Name9 = name9
        self.Name14 = name14
        self.Name20 = name20
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Action id="0x%x">\n' % self.id
        rv += self.element('Name', indent+1)
        rv += self.optionals(['Name9', 'Name14', 'Name20'], indent+1)
        rv += baseindent + '</Action>\n'
        return rv


class Parameter(XMLable):
    def __init__(self, id, name, name9=None, name10=None, name12=None, minval=0, maxval=1, stepsize=0.0001):
        super(Parameter, self).__init__()
        self.id = id
        self.Name = name
        self.Name9 = name9
        self.Name10=name10
        self.Name12=name12
        self.MinValue=minval
        self.MaxValue=maxval
        self.StepSize=stepsize
    def xml(self, indent):
        baseindent = TAB * indent
        rv  = baseindent + '<Parameter id="0x%x">\n' % self.id
        rv += self.elements(['Name', 'MinValue', 'MaxValue', 'StepSize'], indent+1)
        rv += self.optionals(['Name9', 'Name10', 'Name12'], indent+1)
        rv += baseindent + '</Parameter>\n'
        return rv

if __name__ == '__main__':
    t1 = Action(42, 'myACtion', name14='itsname14')
    print(t1.xml(0))
    t2 = Parameter(69, 'myParam', name9='itsname9', maxval=1.5)
    print(t2.xml(1))
    # TODO write out files
    pass
