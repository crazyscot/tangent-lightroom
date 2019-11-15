#!/usr/bin/env python

from TangentMapping import *

controls = ControlsFile(
    [Mode(1,'Develop'),
     Mode(2,'Develop2')],
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

wave = MapFile(
    'Wave',
    [ # common definitions
            ControlBank('Standard',[
                # Buttons and encoders without displays
                Bank([
                    # Truly standard controls which should appear in every bank:
                    Button(36, 0x102, 0x102), # Previous
                    Button(37, 0x103, 0x103), # Next
                    Button( 9, 0x80000001, 0x80000001), # Alt
                    Button(25, 0x80000009), # Up arrow -> next mode
                    Button(26, 0x8000000a), # Down arrow -> prev mode
                    Encoder(12, 0x81000001, 0x81000001), # Transport dial
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                    Button(10, 0x100), # Undo
                    Button(11, 0x101), # Redo
                ]),
            ]),
    ],
    [ # Mode-specific definitions
        Mode(1, controlBanks=[
            ControlBank('Standard',[
                # Buttons and encoders without displays
                Bank([
                    Encoder( 9, 0x205, 0x205), # Dial 1 - Shadows
                    Encoder(10, 0x203, 0x203), # Dial 2 - Exposure
                    Encoder(11, 0x204, 0x204), # Dial 3 - Highlights
                ]),
            ]),
            ControlBank('Encoder',[
                # Encoders with displays
                Bank([
                    Encoder(0, 0x201, 0x201), # Temp
                    Encoder(1, 0x202, 0x202), # Tint
                    Encoder(4, 0x208, 0x208), # Knob 5 -> Blacks
                    Encoder(5, 0x209, 0x209), # Knob 6 -> Whites
                    Encoder(6, 0x20a, 0x20a), # Knob 7 -> Clarity
                    Encoder(7, 0x20b, 0x20b), # Knob 8 -> Vibrance
                    Encoder(8, 0x20c, 0x20c), # Knob 9 -> Saturation
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                    Button(12, 0x200), # Auto Tone
                    Button(15, 0x102), # Prev (TODO - Remove)
                    Button(16, 0x103), # Next (Ditto)
                ]),
            ]),
        ]),
        Mode(2, controlBanks=[
            ControlBank('Standard',[
                # Buttons and encoders without displays
                Bank([
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                ]),
            ]),
        ]),
    ]
)

controls.check(None)
wave.check(controls)

if __name__ == '__main__':
    with open('controls.xml','w') as f:
        f.write( controls.xml(0, controls) )
        print("Wrote to controls.xml")
    with open('wave-map.xml', 'w') as f:
        f.write( wave.xml(0, controls) )
        print("Wrote to wave-map.xml")
