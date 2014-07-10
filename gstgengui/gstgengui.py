#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# * This Program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU Lesser General Public
# * License as published by the Free Software Foundation; either
# * version 2.1 of the License, or (at your option) any later version.
# *
# * Libav is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# * Lesser General Public License for more details.
# *
# * You should have received a copy of the GNU Lesser General Public
# * License along with Libav; if not, write to the Free Software
# * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
GstGengui: utility for testing and controlling live GStreamer pipelines and elements.

Copyright 2014, Dirk Van Haerenborgh, under the terms of LGPL

"""
__author__ = 'Dirk Van Haerenborgh <vhdirk@gmail.com>'
__package__= 'gstgengui'

import os.path
import optparse
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

try:
    # Avoid a deprecation warning about threads_init
    gi.check_version("3.9.1")
except (ValueError, AttributeError):
    GObject.threads_init()

from gi.repository import GLib, GObject, Gtk, Gio, Gdk, Gst


class OptparseDummyDefaults():
    def get(*args):
        return ""

try:
   tmp = Gtk.get_option_group
except AttributeError:
    def get_option_group():
    
        optlist=[GLib.option.make_option("--gtk-module",
                                             metavar="MODULES",
                                             help="Load additional GTK+ modules"),
                 GLib.option.make_option("--g-fatal-warnings",
                                         action="store_true", default="",
                                         help="Make all warnings fatal"),
                 GLib.option.make_option("--gtk-debug",
                                         metavar="FLAGS",
                                         help="GTK+ debugging flags to set"),
                 GLib.option.make_option("--gtk-no-debug",
                                         metavar="FLAGS",
                                         help="GTK+ debugging flags to set"),
                    ]

        group = GLib.option.OptionGroup(
            "gtk", "GTK+ Options", "Show GTK+ Options",
            option_list=optlist)

    
        ggroup = group.get_option_group(None)
        Gdk.add_option_entries_libgtk_only(ggroup)
        
        setattr(ggroup, 'values', dict([(opt.dest,"") for opt in optlist]))

        return ggroup
    
    Gtk.get_option_group = get_option_group



try:
   tmp = Gst.init_get_option_group
except AttributeError:
    def init_get_option_group():
        group = GLib.option.OptionGroup(
            "gst", "GStreamer Options", "Show GStreamer Options",
            option_list=[GLib.option.make_option("--gst-version",
                                                 action="store_true",
                                                 dest="version",
                                                 help="Print the GStreamer version"),
                         GLib.option.make_option("--gst-fatal-warnings",
                                                 action="store_true",
                                                 help="Make all warnings fatal"),
                         GLib.option.make_option("--gst-debug-help",
                                                 action="store_true",
                                                 help="Print available debug categories and exit"),
                         GLib.option.make_option("--gst-debug-level",
                                                 metavar="LEVEL",
                                                 help="Default debug level from 1 (only error) to 9 (anything) or 0 for no output"),
                         GLib.option.make_option("--gst-debug",
                                                 metavar="LIST",
                                                 help="Comma-separated list of category_name:level pairs to set "
                                                      "specific levels for the individual categories. Example: "
                                                      "GST_AUTOPLUG:5,GST_ELEMENT_*:3"),
                         GLib.option.make_option("--gst-debug-no-color",
                                                 action="store_true",
                                                 help="Disable colored debugging output"),
                         GLib.option.make_option("--gst-debug-color-mode",
                                                 metavar="MODE",
                                                 help="Changes coloring mode of the debug log. "
                                                      "Possible modes: off, on, disable, auto, unix"),
                         GLib.option.make_option("--gst-debug-disable",
                                                 action="store_true",
                                                 help="Disable debugging"),
                         GLib.option.make_option("--gst-plugin-spew",
                                                 action="store_true",
                                                 help="Enable verbose plugin loading diagnostics"),
                         GLib.option.make_option("--gst-plugin-path",
                                                 metavar="PATHS",
                                                 help="Colon-separated paths containing plugins"),
                         GLib.option.make_option("--gst-plugin-load",
                                                 metavar="PLUGINS",
                                                 help="Comma-separated list of plugins to preload in addition to the "
                                                      "list stored in environment variable GST_PLUGIN_PATH"),
                         GLib.option.make_option("--gst-disable-segtrap",
                                                 action="store_true",
                                                 help="Disable trapping of segmentation faults during plugin loading"),       
                         GLib.option.make_option("--gst-disable-registry-update",
                                                 action="store_true",
                                                 help="Disable updating the registry"),     
                         GLib.option.make_option("--gst-disable-registry-fork",
                                                 action="store_true",
                                                 help="Disable spawning a helper process while scanning the registry"),    
                        ])
    
        
        ggroup = group.get_option_group(None)

        return ggroup
        
    Gst.init_get_option_group = init_get_option_group




def main():


    parser = GLib.option.OptionParser(prog="gstgengui", description="Utility for testing and controlling live GStreamer pipelines and elements",
        conflict_handler='resolve',
        option_list=[GLib.option.make_option("--messages", "-m",
                                             action="store_true",
                                             dest="show_messages",
                                             default=False,
                                             help="Show Gst.Element messages window before setting the pipeline to PLAYING"),
#                     GLib.option.make_option("pipeline",
#                                             nargs='*',
#                                             help='Pipeline description'),
                    ])

    parser.add_option_group(Gtk.get_option_group())
    parser.add_option_group(Gst.init_get_option_group())
    
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    try:
        parser.parse_args()
    except optparse.BadOptionError as ex:
        print (ex)
        sys.exit()

    






##def main():
##    parser = argparse.ArgumentParser(prog="gstgengui", description='utility for testing and controlling live GStreamer pipelines and elements',  formatter_class=argparse.ArgumentDefaultsHelpFormatter, conflict_handler='resolve')

##    parser.add_argument('-m', "--messages", action="store_true", dest="show_messages", default=False, help="Show Gst.Element messages window before setting the pipeline to PLAYING")
##    parser.add_argument('-c', "--config", dest="config", help="Loads the given configuration file")
##    parser.add_argument('-p', "--preview", action="store_false", dest="display_preview", default=True, help="Disable inline preview")
##    parser.add_argument('pipeline', nargs='*', help='Pipeline description')
##    
##    args = parser.parse_args()
##   


#class GenGuiApp(Gtk.Application):

#    main = None

#    def __init__(self):
#        super().__init__(application_id="org.gstgengui.gstgengui",
#                        flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
#    
#        self.connect("command-line", self.on_command_line)
#        self.connect("activate", self.on_activate)
#    
#    
#    def on_command_line(self, app, cmd):
##        
##        ctx = GLib.OptionContext("gstgengui")

##        # add local options
##        group =  GLib.OptionGroup("options", "main options", "main options", None)
###//    bool show_gui = false;
###        entry = GLib.OptionEntry()
###        entry.long_name = "gui";
###        entry.description = "show the gui."
###        group.add_entries(entry)
##        ctx.add_group(group)

##        # add GTK options, --help-gtk, etc
##        gtkgroup = Gtk.get_option_group()
###    ctx.add_group(gtkgroup);

###    // add GStreamer options
###    Glib::OptionGroup gstoptiongroup = Gst::get_option_group();
###    ctx.add_group(gstoptiongroup);

###    int argc;
###    char **argv = cmd->get_arguments(argc);

##        ctx.parse(sys.argv);
##        
##        


#        group = Gtk.get_option_group()
#        
#        print (group)

#        parser = GLib.option.OptionParser(
#            "NAMES ...", description="A simple gobject.option example.",
#            option_list=[GLib.option.make_option("--file", "-f",
#                                                 type="filename",
#                                                 action="store",
#                                                 dest="file",
#                                                 help="A filename option"),
#                         # ...
#                        ])

#        parser.add_option_group(group)
#        
#        

#        parser.parse_args()
#                
#                
#        
#        
#        
#        
#        print("group: example " + str(group.values.g_fatal_warnings))
#        print("parser: file " + str(parser.values.file))

#        Gtk.init(sys.argv)
#        
#        
#        
#        
#        
#        
#        
#        
#        
#        
#        

#        # show the gui
#        #self.main = new LaunchGUI(argc, argv);
#        self.main = Gtk.Window()

#        self.activate();

#        return False
#        
#                        
#    def on_activate(self, app):
#        self.add_window(self.main)
#        self.main.show()
#        return False



##def main():


##  static const GOptionEntry gst_args[] = {
##    {"gst-version", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##        (gpointer) parse_goption_arg, N_("Print the GStreamer version"), NULL},
##    {"gst-fatal-warnings", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##        (gpointer) parse_goption_arg, N_("Make all warnings fatal"), NULL},
###ifndef GST_DISABLE_GST_DEBUG
##    {"gst-debug-help", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Print available debug categories and exit"),
##        NULL},
##    {"gst-debug-level", 0, 0, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Default debug level from 1 (only error) to 9 (anything) or "
##              "0 for no output"),
##        N_("LEVEL")},
##    {"gst-debug", 0, 0, G_OPTION_ARG_CALLBACK, (gpointer) parse_goption_arg,
##          N_("Comma-separated list of category_name:level pairs to set "
##              "specific levels for the individual categories. Example: "
##              "GST_AUTOPLUG:5,GST_ELEMENT_*:3"),
##        N_("LIST")},
##    {"gst-debug-no-color", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg, N_("Disable colored debugging output"),
##        NULL},
##    {"gst-debug-color-mode", 0, 0, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Changes coloring mode of the debug log. "
##              "Possible modes: off, on, disable, auto, unix"),
##        NULL},
##    {"gst-debug-disable", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##        (gpointer) parse_goption_arg, N_("Disable debugging"), NULL},
###endif
##    {"gst-plugin-spew", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Enable verbose plugin loading diagnostics"),
##        NULL},
##    {"gst-plugin-path", 0, 0, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##        N_("Colon-separated paths containing plugins"), N_("PATHS")},
##    {"gst-plugin-load", 0, 0, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Comma-separated list of plugins to preload in addition to the "
##              "list stored in environment variable GST_PLUGIN_PATH"),
##        N_("PLUGINS")},
##    {"gst-disable-segtrap", 0, G_OPTION_FLAG_NO_ARG, G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Disable trapping of segmentation faults during plugin loading"),
##        NULL},
##    {"gst-disable-registry-update", 0, G_OPTION_FLAG_NO_ARG,
##          G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Disable updating the registry"),
##        NULL},
##    {"gst-disable-registry-fork", 0, G_OPTION_FLAG_NO_ARG,
##          G_OPTION_ARG_CALLBACK,
##          (gpointer) parse_goption_arg,
##          N_("Disable spawning a helper process while scanning the registry"),
##        NULL},
##    {NULL}
##    
##    
##    
##    
##  info = g_new0 (OptionGroupInfo, 1);
##  info->open_default_display = open_default_display;
##  
##  group = g_option_group_new ("gtk", _("GTK+ Options"), _("Show GTK+ Options"), info, g_free);
##  g_option_group_set_parse_hooks (group, pre_parse_hook, post_parse_hook);

##  gdk_add_option_entries_libgtk_only (group);
##  g_option_group_add_entries (group, gtk_args);
##  g_option_group_set_translation_domain (group, GETTEXT_PACKAGE);

#def main():
#    app = GenGuiApp()
#    exit_status = app.run(sys.argv)
#    sys.exit(exit_status)
 
if __name__ == '__main__':
    main()
    
