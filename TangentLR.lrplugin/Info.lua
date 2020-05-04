--[[----------------------------------------------------------------------------

Info.lua
MIDI2LR Plugin properties

This file is part of MIDI2LR. Copyright 2015 by Rory Jaffe.

MIDI2LR is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

MIDI2LR is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
MIDI2LR.  If not, see <http://www.gnu.org/licenses/>.
------------------------------------------------------------------------------]]

return {
  LrAlsoUseBuiltInTranslations = true,
  LrForceInitPlugin = true,
  LrInitPlugin = 'Client.lua', -- Main client logic
  LrPluginInfoUrl = 'https://github.com/crazyscot/tangent-lightroom',
  LrPluginName = 'TangentLR',
  LrSdkMinimumVersion = 6.0, -- minimum SDK version required by this plug-in
  LrSdkVersion = 6.0,
  LrShutdownPlugin = 'ShutDownPlugin.lua',
  LrDisablePlugin = 'ShutDownPlugin.lua',
  LrEnablePlugin = 'Client.lua',
  LrToolkitIdentifier = 'nz.mediary.tangentlr',
  LrExportMenuItems = {
    {
      title = LOC("$$$/MIDI2LR/Menu/GeneralOptions=General &options"),
      file = 'Options.lua',
    },
    --[[--
    {
      title = LOC("$$$/SmartCollection/Criteria/DevelopPreset=Develop Preset"),
      file = 'PresetsDialog.lua',
    },
    {
      title = LOC("$$$/AgLibrary/Filter/BrowserCriteria/Keywords=Keywords"),
      file = 'KeywordsDialog.lua',
    },
    --]]--
    {
      title = 'Start Helper',
      file = "LaunchServer.lua"
    },
    {
      title = 'Stop Helper',
      file = "StopServer.lua"
    },
    {
      title = LOC("$$$/MIDI2LR/Menu/ImportConfiguration=&Import configuration"),
      file = "FileLoadPref.lua",
    },
    {
      title = LOC("$$$/MIDI2LR/Menu/ExportConfiguration=&Export configuration"),
      file = "FileSavePref.lua"
    },
    {
      title = LOC("$$$/MIDI2LR/Help/OnlineHelp=Online &help"),
      file = "OnlineHelp.lua",
    },     
    --[[--
    {
      title = LOC("$$$/MIDI2LR/Info/BuildFiles=Build files (development use only)"),
      file = "Build.lua"
    },
    --]]--
  },
  LrHelpMenuItems = {
    {
      title = LOC("$$$/MIDI2LR/Help/OnlineHelp=&Online help"),
      file = "OnlineHelp.lua",
    }, 
    --[[--
    {
      title = LOC("$$$/MIDI2LR/Help/Support=&Support"),
      file = "Support.lua",
    },
    {
      title = LOC("$$$/MIDI2LR/Help/Latest=&View latest release"),
      file = "Latest.lua",
    },
    --]]--
    {
      title = 'Donate to the MIDI2LR project',
      file = "Donate.lua",
    },
    {
      title = LOC("$$$/AgWPG/Dialogs/About/Title=About"),
      file = "About.lua",
    },
  },
  VERSION = { major=1, minor=3, revision=1, build=0}
}
