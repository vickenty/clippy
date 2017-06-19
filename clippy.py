#!/usr/bin/env python2.7
import re
from time import strftime, gmtime, localtime

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Notify

FORMAT='%Y-%m-%d %H:%M:%S'
FORMAT_UTC='%s UTC' % FORMAT
FORMAT_LOC='%s %%Z' % FORMAT

# Gnome 3 ignores client supplied timeout value and clears non-critical
# notifications after 4 seconds. That's too quick for me to read.
class Notification (object):
    TIMEOUT = 30000

    def __init__(self, *args, **kwargs):
        self.notification = Notify.Notification.new(*args, **kwargs)
        self.notification.set_hint("transient", GLib.Variant.new_boolean(True))
        self.notification.set_urgency(Notify.Urgency.CRITICAL)

        self.timeout = GLib.timeout_add(self.TIMEOUT, self.close)

    def show(self):
        self.notification.show()

    def close(self):
        self.notification.close()
        GLib.source_remove(self.timeout)

    def add_action(self, *args, **kwargs):
        self.notification.add_action(*args, **kwargs)

class Clippy (object):
    def __init__(self):
        self.current = None
        self.listeners = {}

    def listen_to(self, selection):
        clip = Gtk.Clipboard.get(selection)
        sig = clip.connect("owner-change", self.render)
        self.listeners[sig] = clip

    def render(self, clip, event):
        self.close()

        t = clip.wait_for_text()
        if not t:
            return

        m = re.match('^\s*([0-9]{4,}).*$', t)

        if m:
            tn = int(m.group(1))
            utc_str = strftime(FORMAT_UTC, gmtime(tn))
            loc_str = strftime(FORMAT_LOC, localtime(tn))
            tz_name = strftime('%Z', localtime(tn))
            text = u'%s\r%s' % (utc_str, loc_str)

            self.current = n = Notification(m.group(1), body=text, icon="preferences-system-time-symbolic")
            
            n.add_action("copy-utc", "Copy UTC", self.copy, utc_str)
            n.add_action("copy-local", "Copy %s" % tz_name, self.copy, loc_str)
            n.show()

    def close(self):
        if self.current:
            self.current.close()
            self.current = None

    def copy(self, notification, action, content):
        clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clip.set_text(content, len(content))
        
Notify.init("clippy")

clippy = Clippy()
clippy.listen_to(Gdk.SELECTION_PRIMARY)

Gtk.main()
