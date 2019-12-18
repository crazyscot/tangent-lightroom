/*
 * This file is part of MIDI2LR. Copyright (C) 2015 by Rory Jaffe.
 *
 * MIDI2LR is free software: you can redistribute it and/or modify it under the terms of the GNU
 * General Public License as published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * MIDI2LR is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
 * the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
 * Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with MIDI2LR.  If not,
 * see <http://www.gnu.org/licenses/>.
 *
 */
#include "Ocpp.h"

#import <Carbon/Carbon.h>
#import <Cocoa/Cocoa.h> /* for CheckPermission */
#include <JuceLibraryCode/JuceHeader.h>
#include <fmt/format.h>

#include "Misc.h"

UniChar rsj::Utf8ToUtf16(const std::string& param)
{
   if (!param.empty()) {
      NSString* result = @(param.c_str());
      UniChar ch = [result characterAtIndex:0];
      return ch;
   }
   return 0;
}

std::string rsj::AppDataMac()
{
   NSString* result = (@"~/Library/Application Support/MIDI2LR").stringByExpandingTildeInPath;
   return std::string(result.UTF8String);
}

std::string rsj::AppLogMac()
{
   NSString* result = (@"~/Library/Logs/MIDI2LR").stringByExpandingTildeInPath;
   return std::string(result.UTF8String);
}

#if __MAC_OS_X_VERSION_MIN_REQUIRED <= __MAC_10_14
enum {
    errAEEventWouldRequireUserConsent = -1744,
};
#endif

void rsj::CheckPermission(pid_t pid)
{
   if (@available(macOS 10.14, *)) {
      AEAddressDesc addressDesc;
      NSString* bundleIdentifier =
          [NSRunningApplication runningApplicationWithProcessIdentifier:pid].bundleIdentifier;
      const char* bundleIdentifierCString =
          [bundleIdentifier cStringUsingEncoding:NSUTF8StringEncoding];
      auto aeresult = AECreateDesc(typeApplicationBundleID, bundleIdentifierCString,
          strlen(bundleIdentifierCString), &addressDesc);
      if (aeresult == noErr) {
         auto status =
             AEDeterminePermissionToAutomateTarget(&addressDesc, typeWildCard, typeWildCard, true);
         AEDisposeDesc(&addressDesc);
         switch (status) {
         case errAEEventWouldRequireUserConsent:
            rsj::Log(
                fmt::format("Automation permission pending for {}.", bundleIdentifier.UTF8String));
            break;
         case noErr:
            rsj::Log(
                fmt::format("Automation permission granted for {}.", bundleIdentifier.UTF8String));
            break;
         case errAEEventNotPermitted: {
            rsj::Log(
                fmt::format("Automation permission denied for {}.", bundleIdentifier.UTF8String));
            auto title =
                juce::translate("MIDI2LR needs your authorization to send keystrokes to Lightroom");
            auto message = juce::translate(
                "To authorize MIDI2LR to send keystrokes to Lightroom, please follow these "
                "steps:\r\n1) Open System Preferences\r\n2) Click on Security & Privacy\r\n3) "
                "Select the Privacy tab\r\n4) Find and select Accessibility on the left\r\n5) Find "
                "the checkbox for MIDI2LR on the right\r\n6) Check that checkbox");
            juce::NativeMessageBox::showMessageBox(juce::AlertWindow::WarningIcon, title, message);
            break;
         }
         case procNotFound:
            rsj::Log(fmt::format("Application not found. Automation permission unknown for {}.",
                bundleIdentifier.UTF8String));
            break;
         default:
            rsj::Log(
                fmt::format("Unexpected return value when checking automation permission for {}.",
                    bundleIdentifier.UTF8String));
            break;
         }
      }
      else
         rsj::Log(fmt::format("AECreateDesc returned error {}.", aeresult));
   }
}
