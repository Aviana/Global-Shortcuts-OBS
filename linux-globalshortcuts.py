#!/usr/bin/python

# Copyright 2024 Aviana <winblocker@gmx.de>
#
# Redistribution and use in source and binary forms,
# with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import obspython as obs
from contextlib import contextmanager
from gi.repository import GLib
import threading
import dbus
from dbus.mainloop.glib import DBusGMainLoop

bus_name = 'org.freedesktop.portal.Desktop'
request_interface = 'org.freedesktop.portal.Request'
shortcut_interface = 'org.freedesktop.portal.GlobalShortcuts'
object_path = '/org/freedesktop/portal/desktop'

activeShortcuts = {}
activePushFuncs = {}

pushFuncs = {
    "ptm": True,
    "ptt": True,
    }

defaultShortcuts = {
    "setStreamingStatus||1||": "Basic.Main.StartStreaming",
    "setStreamingStatus||0||": "Basic.Main.StopStreaming",
    # "stopStreamNow": "Basic.Main.ForceStopStreaming",
    "setRecordingStatus||1||": "Basic.Main.StartRecording",
    "setRecordingStatus||0||": "Basic.Main.StopRecording",
    "setPauseRecordingStatus||1||": "Basic.Main.PauseRecording",
    "setPauseRecordingStatus||0||": "Basic.Main.UnpauseRecording",
    "splitRecording": "Basic.Main.SplitFile",
    "setReplayBufferStatus||1||": "Basic.Main.StartReplayBuffer",
    "setReplayBufferStatus||0||": "Basic.Main.StopReplayBuffer",
    "setActivatePreview||1||": "Basic.Main.PreviewConextMenu.Enable",
    "setActivatePreview||0||": "Basic.Main.Preview.Disable",
    "setStudioMode||1||": "Basic.EnablePreviewProgramMode",
    "setStudioMode||0||": "Basic.DisablePreviewProgramMode",
    # "setSourceToolbar||1|||": "Basic.Main.ShowContextBar",
    # "setSourceToolbar||0||": "Basic.Main.HideContextBar",
    "doTransition": "Transition",
    # "resetStatistics": "Basic.Stats.ResetStats",
    "screenshotOutput": "Screenshot",
    "screenshotSource": "Screenshot.SourceHotkey",
    "saveReplayBuffer": "Basic.Main.SaveReplay",
}

# -------------------------------------------------------------


class PortalGlobalShortcuts:
    def __init__(self, handle: str):
        DBusGMainLoop(set_as_default=True)

        self.handle = handle
        self.bus = dbus.SessionBus()
        self.portal = self.bus.get_object(bus_name, object_path)
        self.CreateSession()

    def BindShortcuts(self, shortcuts) -> None:
        self.portal.BindShortcuts(
            self.session,
            shortcuts,
            '',
            {},
            dbus_interface=shortcut_interface
        )

    def ListShortcuts(self) -> None:
        self.portal.ListShortcuts(
            self.session,
            {},
            dbus_interface=shortcut_interface
        )

    def ShortcutsReply(self, shortcuts) -> None:
        pass

    def ShortcutPressed(self, shortcut_id: str, pressed: bool) -> None:
        pass

    def Callback(self, response, results) -> None:
        self.ShortcutsReply(results['shortcuts'])

    def CreateSessionCallback(self, response, results) -> None:
        self.session = results['session_handle']
        reply = self.portal.ListShortcuts(
            self.session,
            {},
            dbus_interface=shortcut_interface
        )

        self.bus.add_signal_receiver(
            self.Callback,
            'Response',
            request_interface,
            bus_name,
            reply
        )

    def KeyActivatedCallback(self, session_handle, shortcut_id, timestamp, options) -> None:
        if session_handle == self.session:
            self.ShortcutPressed(shortcut_id, True)

    def KeyDeactivatedCallback(self, session_handle, shortcut_id, timestamp, options) -> None:
        if session_handle == self.session:
            self.ShortcutPressed(shortcut_id, False)

    def ShortcutsChangedCallback(self, session_handle, shortcuts) -> None:
        if session_handle == self.session:
            self.ShortcutsReply(shortcuts)

    def CreateSession(self) -> None:
        options = {
            'handle_token': self.handle.lower(),
            'session_handle_token': self.handle,
        }

        reply = self.portal.CreateSession(
            options,
            dbus_interface=shortcut_interface
        )

        self.bus.add_signal_receiver(
            self.CreateSessionCallback,
            'Response',
            request_interface,
            bus_name,
            reply
        )

        self.bus.add_signal_receiver(
            self.KeyActivatedCallback,
            'Activated',
            shortcut_interface,
            bus_name,
            object_path
        )

        self.bus.add_signal_receiver(
            self.KeyDeactivatedCallback,
            'Deactivated',
            shortcut_interface,
            bus_name,
            object_path
        )

        self.bus.add_signal_receiver(
            self.ShortcutsChangedCallback,
            'ShortcutsChanged',
            shortcut_interface,
            bus_name,
            object_path
        )


def loop_th() -> None:
    loop.run()


loop = GLib.MainLoop()
portal = PortalGlobalShortcuts("OBSbindings")

thread = threading.Thread(target=loop_th)
thread.daemon = True
thread.start()


# -------------------------------------------------------------


@contextmanager
def scene_ar(scene):
    scene = obs.obs_scene_from_source(scene)
    try:
        yield scene
    finally:
        obs.obs_scene_release(scene)


@contextmanager
def scene_enum(_scene):
    items = obs.obs_scene_enum_items(_scene)
    try:
        yield items
    finally:
        obs.sceneitem_list_release(items)


def script_description() -> str:
    return "Adds support for xdg-desktop-portal based global hotkeys.\n\nBy Aviana"


def script_load(settings) -> None:
    PortalGlobalShortcuts.ShortcutsReply = onKeybindsChanged
    PortalGlobalShortcuts.ShortcutPressed = onKeybind


def script_unload() -> None:
    pass


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_button(
        props,
        "button1",
        "Update Keybinds",
        open_settings)
    return props


def open_settings(props, prop) -> None:
    # compile keybinds and call BindShortcuts
    # This opens system keybindings on KDE
    shortcuts = []

    # Default shortcuts
    for bind, desc in defaultShortcuts.items():
        shortcuts.append((bind, {"description": obs.obs_frontend_get_locale_string(desc)}))

    # Scenes
    scenes = obs.obs_frontend_get_scenes()
    selectScene = obs.obs_frontend_get_locale_string("Basic.Hotkeys.SelectScene")
    showScene = obs.obs_frontend_get_locale_string("SceneItemShow")
    hideScene = obs.obs_frontend_get_locale_string("SceneItemHide")
    for scene in scenes:
        name = obs.obs_source_get_name(scene)
        shortcuts.append((
            "setActiveScene||1||" + name,
            {"description": name + ": " + selectScene}
        ))
        with scene_ar(scene) as current_scene:
            with scene_enum(current_scene) as scene_items:
                for scene_item in scene_items:
                    sourceobj = obs.obs_sceneitem_get_source(scene_item)
                    sourcename = obs.obs_source_get_name(sourceobj)
                    shortcuts.append((
                        "setSceneItemEnable||1||" + name + "||" + sourcename,
                        {"description": name + ": " + showScene.replace("%1", sourcename)}
                    ))
                    shortcuts.append((
                        "setSceneItemEnable||0||" + name + "||" + sourcename,
                        {"description": name + ": " + hideScene.replace("%1", sourcename)}
                    ))

    # Audio sources
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            mixers = obs.obs_source_get_audio_mixers(source)
            if mixers > 0:
                name = obs.obs_source_get_name(source)
                shortcuts.append((
                    "setItemMute||1||" + name,
                    {"description": name + ": " + obs.obs_frontend_get_locale_string("Mute")}
                ))
                shortcuts.append((
                    "setItemMute||0||" + name,
                    {"description": name + ": " + obs.obs_frontend_get_locale_string("Unmute")}
                ))
                shortcuts.append((
                    "ptm||" + name,
                    {"description": name + ": " + obs.obs_frontend_get_locale_string("Push-to-mute")}
                ))
                shortcuts.append((
                    "ptt||" + name,
                    {"description": name + ": " + obs.obs_frontend_get_locale_string("Push-to-talk")}
                ))

    # Can't do stingers at the moment

    portal.BindShortcuts(shortcuts)


def onKeybind(portalobj, shortcut_id: str, pressed: bool) -> None:
    args = shortcut_id.split("||")
    func = args.pop(0)
    if func in pushFuncs:
        globals()[func](pressed, *args)
        return
    if pressed:
        return
    if len(args) > 0:
        arg1 = args.pop(0)
        if args[0] == "":
            args.pop(0)
        enable = bool(int(arg1))
        invert = shortcut_id.replace(
            "||" + arg1 + "||",
            "||" + str(int(not enable)) + "||"
            )
        if invert not in activeShortcuts:
            enable = None
        globals()[func](enable, *args)
        return
    globals()[func](*args)


def onKeybindsChanged(portalobj, shortcuts) -> None:
    global activeShortcuts
    activeShortcuts.clear()
    activePushFuncs.clear()
    for keybind in shortcuts:
        if keybind[1]["trigger_description"] != "":
            bindName = str(keybind[0])
            if bindName[:3] in pushFuncs:
                activePushFuncs[bindName] = False
            activeShortcuts[bindName] = str(
                keybind[1]["trigger_description"]
                )


def setStreamingStatus(enabled: bool) -> None:
    if enabled is not None:
        if enabled:
            obs.obs_frontend_streaming_start()
        else:
            obs.obs_frontend_streaming_stop()
    elif not obs.obs_frontend_streaming_active():
        obs.obs_frontend_streaming_start()
    else:
        obs.obs_frontend_streaming_stop()


def stopStreamNow() -> None:
    pass


def setRecordingStatus(enabled: bool) -> None:
    if enabled is not None:
        if enabled:
            obs.obs_frontend_recording_start()
        else:
            obs.obs_frontend_recording_stop()
    elif not obs.obs_frontend_recording_active():
        obs.obs_frontend_recording_start()
    else:
        obs.obs_frontend_recording_stop()


def setPauseRecordingStatus(enabled: bool) -> None:
    if enabled is not None:
        obs.obs_frontend_recording_pause(enabled)
    else:
        boolean = not obs.obs_frontend_recording_paused()
        obs.obs_frontend_recording_pause(boolean)


def splitRecording() -> None:
    obs.obs_frontend_recording_split_file()


def setReplayBufferStatus(enabled: bool) -> None:
    if enabled is not None:
        if enabled:
            obs.obs_frontend_replay_buffer_start()
        else:
            obs.obs_frontend_replay_buffer_stop()
    elif not obs.obs_frontend_replay_buffer_active():
        obs.obs_frontend_replay_buffer_start()
    else:
        obs.obs_frontend_replay_buffer_stop()


def setActivatePreview(enabled: bool) -> None:
    if enabled is not None:
        obs.obs_frontend_set_preview_enabled(enabled)
    else:
        boolean = not obs.obs_frontend_preview_enabled()
        obs.obs_frontend_set_preview_enabled(boolean)


def setStudioMode(enabled: bool) -> None:
    if enabled is not None:
        obs.obs_frontend_set_preview_program_mode(enabled)
    else:
        boolean = not obs.obs_frontend_preview_program_mode_active()
        obs.obs_frontend_set_preview_program_mode(boolean)


def setSourceToolbar(enabled: bool) -> None:
    pass


def doTransition() -> None:
    obs.obs_frontend_preview_program_trigger_transition()


def resetStatistics() -> None:
    pass


def screenshotOutput() -> None:
    obs.obs_frontend_take_screenshot()


def screenshotSource() -> None:
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        with scene_ar(scene) as current_scene:
            scene_items = obs.obs_scene_enum_items(current_scene)
        for item in reversed(scene_items):
            if obs.obs_sceneitem_selected(item):
                obs.obs_frontend_take_source_screenshot(
                    obs.obs_sceneitem_get_source(item)
                )


def saveReplayBuffer() -> None:
    obs.obs_frontend_replay_buffer_save()


def setActiveScene(enabled: bool, sceneName: str) -> None:
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        name = obs.obs_source_get_name(scene)
        if name == sceneName:
            obs.obs_frontend_set_current_scene(scene)
            return
    print(f"ERROR: Did not find scene '{sceneName}'.")


def setItemMute(enabled: bool, itemName: str) -> None:
    source = obs.obs_get_source_by_name(itemName)
    if source is not None:
        if enabled is not None:
            obs.obs_source_set_muted(source, enabled)
        else:
            boolean = not obs.obs_source_muted(source)
            obs.obs_source_set_muted(source, boolean)
    else:
        print(f"ERROR: Did not find source '{itemName}'.")


def setSceneItemEnable(enabled: bool, sceneName: str, itemName: str) -> None:
    scenes = obs.obs_frontend_get_scenes()
    for scene in scenes:
        name = obs.obs_source_get_name(scene)
        if name == sceneName:
            with scene_ar(scene) as current_scene:
                scene_item = obs.obs_scene_find_source(current_scene, itemName)
            if scene_item is not None:
                if enabled is not None:
                    obs.obs_sceneitem_set_visible(scene_item, enabled)
                else:
                    boolean = not obs.obs_sceneitem_visible(scene_item)
                    obs.obs_sceneitem_set_visible(scene_item, boolean)
            else:
                print(f"ERROR: Did not find source '{itemName}' in scene '{sceneName}'.")
            return
    print(f"ERROR: Did not find scene '{sceneName}'.")


def ptm(pressed: bool, itemName: str) -> None:
    global activePushFuncs
    if activePushFuncs["ptm||" + itemName] == pressed:
        return
    activePushFuncs["ptm||" + itemName] = pressed
    setItemMute(pressed, itemName)


def ptt(pressed: bool, itemName: str) -> None:
    global activePushFuncs
    if activePushFuncs["ptt||" + itemName] == pressed:
        return
    activePushFuncs["ptt||" + itemName] = pressed
    setItemMute(not pressed, itemName)
