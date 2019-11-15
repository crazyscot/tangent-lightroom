#!/usr/bin/env python

from TangentMapping import *

controls = ControlsFile(
    [Mode(1,'Colour/Tone'),
     Mode(2,'Tone/Presence')],
    [
        Group('General', [
            Action(0x100, 'Undo'),
            Action(0x101, 'Redo'),
            Action(0x102, 'Prev'),
            Action(0x103, 'Next'),
            Action(0x104, 'ShowClipping', panel='Clipping'),
            Action(0x105, 'VirtualCopy'),
            ]),

        Group('WB', [
            Action(0x111, 'WhiteBalanceAuto', panel='Auto WB'),
            ]),
        Group('Tone', [
            Action(0x110, 'AutoTone', panel='Auto Tone'),

            Parameter(0x201, 'Temperature', name9='ColorTemp', name10='Color Temp', name12='Temperature'),
            Parameter(0x202, 'Tint'),
            Parameter(0x203, 'Exposure'),
            Parameter(0x204, 'Highlights'),
            Parameter(0x205, 'Shadows'),
            Parameter(0x206, 'Brightness', name9='Bright'),
            Parameter(0x207, 'Contrast'),
            Parameter(0x208, 'Blacks'),
            Parameter(0x209, 'Whites'),
            ]),
        Group('Presence', [
            Parameter(0x20a, 'Clarity'),
            Parameter(0x20b, 'Vibrance'),
            Parameter(0x20c, 'Saturation', name9='Saturate'),
            Parameter(0x20d, 'Dehaze'),
            Parameter(0x20e, 'Texture'),
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

                    Encoder( 9, 0x205, 0x205), # Dial 1 - Shadows
                    Encoder(10, 0x203, 0x203), # Dial 2 - Exposure
                    Encoder(11, 0x204, 0x204), # Dial 3 - Highlights
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                    Button(20, 0x100), # Undo # Could move to an F key?
                    Button(21, 0x101), # Redo
                    Button(22, 0x105), # VirtualCopy
                ]),
            ]),
    ],
    [ # Mode-specific definitions

        # Develop WB/Tone
        Mode(1, controlBanks=[
            ControlBank('Standard',[
                # Buttons and encoders without displays
                Bank([
                ]),
            ]),
            ControlBank('Encoder',[
                # Encoders with displays
                Bank([
                    Encoder(0, 0x201, 0x201), # Temp
                    Encoder(1, 0x202, 0x202), # Tint
                    # WB mode on enc 2?
                    Encoder(3, 0x207, 0x207), # Contrast
                    Encoder(4, 0x208, 0x208), # Blacks
                    Encoder(5, 0x209, 0x209), # Whites
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                    Button(12, 0x111), # Auto WB
                    Button(16, 0x110), # Auto Tone
                ]),
            ]),
        ]),

        # Develop Tone/Presence
        Mode(2, controlBanks=[
            ControlBank('Encoder',[
                # Encoders with displays
                Bank([
                    Encoder(0, 0x207, 0x207), # Contrast
                    Encoder(1, 0x208, 0x208), # Blacks
                    Encoder(2, 0x209, 0x209), # Whites

                    Encoder(3, 0x20e, 0x20e), # Texture
                    Encoder(4, 0x20a, 0x20a), # Clarity
                    Encoder(5, 0x20d, 0x20d), # Dehaze
                    Encoder(6, 0x20b, 0x20b), # Vibrance
                    Encoder(7, 0x20c, 0x20c), # Saturation
                ]),
            ]),
            ControlBank('Button',[
                # Buttons with displays
                Bank([
                    Button(11, 0x110), # Auto Tone
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
