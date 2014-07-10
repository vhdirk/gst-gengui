#!/usr/bin/env python3

import os.path
import argparse
import logging
import locale
import gettext
import sys

# Hack to force GIL creation
# See: https://bugzilla.gnome.org/show_bug.cgi?id=709223
# See: https://bugzilla.gnome.org/show_bug.cgi?id=710530
#import threading
#threading.Thread(target=lambda: None).start()

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")


from gi.repository import GLib, Gst

def main():

    args = Gst.init(sys.argv)

    parser = argparse.ArgumentParser(prog="gstgengui", description='utility for testing and controlling live GStreamer pipelines and elements',  formatter_class=argparse.ArgumentDefaultsHelpFormatter, conflict_handler='resolve')
    parser.add_argument('-d', "--debug", action="store_true", dest="debug", default=False, help="Use DEBUG verbosity level")
    parser.add_argument('-m', "--messages", action="store_true", dest="show_messages", default=False, help="Show Gst.Element messages window before setting the pipeline to PLAYING")
    parser.add_argument('-c', "--config", dest="config", help="Loads the given configuration file")
    parser.add_argument('-p', "--preview", action="store_false", dest="display_preview", default=True, help="Disable inline preview")
    parser.add_argument('pipeline', nargs='*', help='Pipeline description')
    
    print (args)
    
    args = parser.parse_args(args)


    print (args)


if __name__ == '__main__':
    main()
