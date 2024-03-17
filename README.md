# Global-Shortcuts-OBS
Global shortcuts for OBS-Studio using xdg-desktop-portal

This is a python script that can be loaded through the scripting system in OBS.

Python dependencies:
- dbus https://pypi.org/project/dbus-python/
- gi   https://pypi.org/project/PyGObject/


Usage:
Start by going to Tools -> Scripts in the main OBS window.
Then load the script by clicking the + at the bottom left and selecting the
file 'linux-globalshortcuts.py' from the location where you downloaded it to.
Now every time you change the available hotkeys (ex adding a scene) you have
to push the button labeled "Update Keybinds". After that you can find the
updated options in your respective desktop environments hotkey options.

If you think it is bothersome to hit this update button ervery time yourself
then consider voicing your opinion here:
https://github.com/flatpak/xdg-desktop-portal/issues/1101


Due to this not being a native implementation and the scripting environment having
no direct access to the hotkeys of OBS the following restrictions apply:

These bindings have not been implemented because of missing functionality in
the python interface:
- "Stop Streaming (discard delay)"
- "Show Source Toolbar"
- "Hide Source Toolbar"
- "Reset Stats"

The "push to mute" and "push to talk" bindings do not use the same functions
as the native OBS implementations. The use the same as the general mute/unmute
bindings and therefore might conflict with it.
