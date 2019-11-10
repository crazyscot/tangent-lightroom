#!/usr/bin/env python

from TangentMapping import *

controls = ControlsFile(
    [Mode(1,'Develop')],
    [
        Group('General', [
            Action(0x100, 'Undo'),
            Action(0x101, 'Redo'),
            Action(0x102, 'Prev'),
            Action(0x103, 'Next'),
            ]),

        Group('Tone', [
            Action(0x200, 'AutoTone', name9='Auto Tone'),

            Parameter(0x201, 'Temperature', name9='ColorTemp', name10='Color Temp', name12='Temperature'),
            Parameter(0x202, 'Tint'),
            Parameter(0x203, 'Exposure'),
            Parameter(0x204, 'Highlights'),
            Parameter(0x205, 'Shadows'),
            Parameter(0x206, 'Brightness', name9='Bright'),
            Parameter(0x207, 'Contrast'),
            Parameter(0x208, 'Blacks'),
            Parameter(0x209, 'Whites'),
            Parameter(0x20a, 'Clarity'),
            Parameter(0x20b, 'Vibrance'),
            Parameter(0x20c, 'Saturation', name9='Saturate'),
            ]),
    ]
)


if __name__ == '__main__':
    with open('controls.xml','w') as f:
        f.write( controls.xml(0) )
        print("Wrote to controls.xml")
    # TODO mapping..
