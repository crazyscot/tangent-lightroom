# TangentLightroom

**TangentLightroom** is a plugin that interfaces the Tangent series of hardware control surfaces with Lightroom.

**This is alpha quality software!** There are likely to be bugs.

TangentLightroom is based on the *MIDI2LR* project by [rsjaffe](https://github.com/rsjaffe/). (If you have a MIDI controller you want to interface with Lightroom, you probably wanted [MIDI2LR](https://rsjaffe.github.io/MIDI2LR/).)

## What is this and who is it for?

It's all about speed. If you have a lot of photos you want to make colour corrections to, it's so much faster to put the controls on a hardware panel than it is to use the mouse.

Professional film and video colour graders use hardware control surfaces all the time.

## System requirements

- Adobe Lightroom Classic. (CC 2019 edition tested; it should work all the way back to Lightroom 6).
- Recent MacOS (tested on 10.14.6); _Windows is untested but ought to work, see below_.
- A Tangent control surface. _This plugin was developed and tested for the Tangent Wave. However, it works with the Tangent Mapper so should work on all Tangent panels (see below)._

## Setup

### OSX

1. Ensure you have installed the Tangent support software. This should be supplied with your panel, or you can download it from [Tangent Support](https://www.tangentwave.co.uk/tangent-support/).
1. Ensure your panel is connected.
1. Download the latest version of TangentLightroom (or clone from GitHub).
1. Put the plugin directory somewhere useful (your Documents folder, perhaps).
1. Open up Lightroom, go into the Plugin Manager (File→Plugin-Manager), press Add, navigate to wherever you just saved the plugin.

### Windows

**Caution:** These instructions are theoretical and have not yet been tested on Windows. Please let me know how you go!

1. Install [Python 2.7](https://www.python.org/download/releases/2.7/). Make sure the _python.exe_ is on your path (you may need to reboot for that to take effect).
1. Follow the OSX instructions above.

## Using the plugin

### Tangent Wave

If you have a Wave or Wave2, everything is ready to go.
You get my mappings file, and can customise it through the Tangent Mapper.

#### Fixed mappings

The following mappings apply in all modes:

- Left Dial: Shadows
- Centre Dial: Exposure
- Right Dial: Highlights

- Transport Dial: Step through current selection
- Next Frame/Back Frame: Step forward/back

- F1: Undo
- F2: Redo
- F3: Create Virtual Copy
- F4: Show/Hide Clipping
- F5: Select Left
- F6: Select Right
- F7: Library mode
- F8: Develop mode
- F9: Zoom in/out

- Up/Down: Step through modes
- Up AND Down together: Go to modes menu

#### Modes

At the time of writing, these are the current defined modes in the default Wave config file:

* Colour/Tone; Tone/Presence; Tone Curve
* Hue Adjust; Saturation Adjust; Luminance Adjust; Grey Adjust (B&W treatment only)
* Split Toning
* Sharpening
* Noise Reduction
* Crop
* Flag
* Rotate/Export
* Modes menu (two pages worth)

### Tangent Arc, Element, Ripple

I haven't yet written a mapping file for these panels. (If you'd like me to create one for you, it'd be easier if I had access to such a panel...)

All is not lost; you will want to set up a mapping in the Tangent Mapper application.
*If you do this, don't forget to save your mapping from within Tangent Mapper!*

If you'd like to contribute your mapping, you'll need to export it from the Mapper (File → Manage Control Maps) - please create an issue on the GitHub page and attach the mapping file.
