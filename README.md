﻿# TangentLightroom

**TangentLightroom** is a plugin for Adobe Lightroom Classic that allows you to control it using the Tangent series of hardware control surfaces.

**This is beta quality software!** There are likely to be bugs.

TangentLightroom is based on the *MIDI2LR* project by
[rsjaffe](https://github.com/rsjaffe/). (If you have a MIDI
controller you want to interface with Lightroom, you probably wanted
[MIDI2LR](https://rsjaffe.github.io/MIDI2LR/).)

If you like this and find it useful, please consider shouting me a coffee - hit the Sponsor button at the top of the page.

## What is this and who is it for?

It's all about speed. If you have a lot of photos you want to interactively make
colour corrections to, it's so much faster to put the controls on a
hardware panel than it is to use the mouse.

Professional film and video colour graders use hardware control surfaces all the time.

## System requirements

- Adobe Lightroom Classic. (CC 2019 edition tested; it should work all the way back to Lightroom 6).
- Recent MacOS (tested on 10.14.6) or Windows (10).
- A Tangent control surface. _This plugin was developed and tested
for the Tangent Wave. However, it works through the Tangent Mapper and includes map files for other panels, which you can customise._

## Setup

### Windows

**Caution:** Windows is not my primary development platform. These instructions were written on Windows 10. Please let me know how you go!

1. Install Python 3.7 from the Microsoft store
1. Follow the OSX instructions below.

### OSX

1. Ensure you have installed the Tangent support software (_Tangent Hub_, etc.). This
should be supplied with your panel, or you can download it from [Tangent
Support](https://www.tangentwave.co.uk/tangent-support/).
1. Ensure your panel is connected.
1. Download or clone the latest version of TangentLightroom. [Releases
page](https://github.com/crazyscot/tangent-lightroom/releases)
1. Put the plugin directory somewhere useful (your Documents folder, perhaps).
1. Open up Lightroom, go into the Plugin Manager
(File→Plugin-Manager), press Add, navigate to wherever you just saved
the plugin.

## Using the plugin

### Tangent Wave

If you have a Wave or Wave2, you have the best experience, because I have a wave.
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
- Up+Down: Go to modes menu _Note: Hold Up and press Down to make this work (or the other way round)._

#### Modes

At the time of writing, these are the current defined modes in the default Wave config file:

* Colour/Tone; Tone/Presence; Tone Curve
* Hue Adjust; Saturation Adjust; Luminance Adjust; Grey Adjust (B&W treatment only)
* Split Toning
* Sharpening
* Noise Reduction
* Crop Edges
* Crop Corners
* Flag
* Rotate/Export
* Modes menu (two pages, identified by the legend under the first dial)

### Tangent Element, Ripple

I don't have one of these panels, so while I've created map files you may
want to play around with the mapping. You can do this in the _Tangent Hub_.

If you'd like to contribute your mapping, you'll need to export it
from the Mapper (File → Manage Control Maps) - please create an issue
on the GitHub page and attach the mapping file. (Or, even better, send
in a pull request, but to do that effectively you'll need to understand
the XML generator in TangentMappingDefinitions.py...)

#### Modes

The Ripple does not have modes.

The Element has a modes menu, accessed by a button on the _Bt_ and _Mf_ panel.

The modes are:

* Basic
* Tone Curve
* Grey Adjust (B&W treatment only); Hue Adjust; Saturation Adjust; Luminance Adjust
* Split Toning
* Sharpening
* Noise Reduction
* Crop
* Flag
* Rotate/Export

## Tips for all panel types

### The trackballs don't do anything (yet) !

Yes, you read that right. All of Lightroom's controls are one-dimensional. There isn't a direct correspondence for a trackball control to, well, anything much. (Temperature and Tint, perhaps?) While I could create a composite control, there's no obvious control to map it to.

The knobs, dials and buttons are working well, but I had trouble getting the trackballs working properly so haven't mapped anything to them yet. This isn't a problem with Tangent; it's most likely an issue with how my bridge code is talking to MIDI2LR and/or how MIDI2LR is talking to Lightroom. I may have another go at this some time.

### Undo/Redo

* Lightroom tracks updates and only creates undo points when you stop providing inputs
for a certain time. This time is configurable; you will find it in _File→Plugin
Extras→General options / Other... / Tracking Delay_ .

## Hacking

This plugin consists of three parts:

1. A collection of Lua scripts. (The use of Lua is mandated by the Lightroom SDK.)
These are inherited from the _MIDI2LR_ project, with some light local modifications.
1. A Python script `TangentBridge.py`. This is the bridge between the Lua scripts and the _Tangent Hub_.
1. XML files. These are used by the _Tangent Hub_ to define what controls are available and how
they map to the control surface. (The mappings can be changed in the _Tangent Hub_.)
  1. These XML files are themselves generated by two Python scripts `TangentMapping.py` and
`TangentMappingDefinitions.py`, which build up the relevant data structures in Python before output.

When working on the plugin you might find it convenient to run `TangentBridge` from the command line or
an IDE. There is copious debug output to the console, and you can have the plugin log to a file as well
if you prefer.

In Lightroom, under File→Plugin Extras, you will find menu items for _Stop Helper_ and _Start Helper_.
These stop and restart _TangentBridge_.
