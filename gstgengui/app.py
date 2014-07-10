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

import sys
import logging
logger = logging.getLogger('gstgengui')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, Gio, GLib

from .pipelinemanager import PipelineManager
from .gtk_controller import GtkGstController


def cb(*args):
    print (args)


class GenGuiApp(Gtk.Application):

    main = None

    def __init__(self):
        super().__init__(application_id="org.gstgengui.gstgengui",
                        flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
    
        self.connect("command-line", self.on_command_line)
        self.connect("activate", self.on_activate)
    
    
    def on_command_line(self, app, cmd):
        
        ctx = GLib.OptionContext("gstgengui")

        # add local options
        group =  GLib.OptionGroup("options", "main options", "main options", None)
#//    bool show_gui = false;
        entry = GLib.OptionEntry()
        entry.long_name = "gui";
        entry.description = "show the gui."
        group.add_entries(entry)
        ctx.add_group(group)

        # add GTK options, --help-gtk, etc
#        gtkgroup = Glib::OptionGroup(gtk_get_option_group(true));
#    ctx.add_group(gtkgroup);

#    // add GStreamer options
#    Glib::OptionGroup gstoptiongroup = Gst::get_option_group();
#    ctx.add_group(gstoptiongroup);

#    int argc;
#    char **argv = cmd->get_arguments(argc);

        ctx.parse(sys.argv);

        # show the gui
        #self.main = new LaunchGUI(argc, argv);
        self.main = Gtk.Window()

        self.activate();

        return False
        
                        
    def on_activate(self, app):
        self.add_window(self.main)
        self.main.show()
        return False
#{
#public:
#  LaunchGUIApp()
#    : Gtk::Application("org.gste.gst-launch-gui",
#                       Gio::APPLICATION_HANDLES_COMMAND_LINE)
#  {}

#  int on_command_line(const Glib::RefPtr<Gio::ApplicationCommandLine> &cmd)
#  {
#    Glib::OptionContext ctx(PACKAGE);

#    // add local options
#//    Glib::OptionGroup group("options", "main options");
#//    bool show_gui = false;
#//    Glib::OptionEntry entry;
#//    entry.set_long_name("gui");
#//    entry.set_description("show the gui.");
#//    group.add_entry(entry, show_gui);
#//    ctx.add_group(group);

#    // add GTK options, --help-gtk, etc
#    Glib::OptionGroup gtkgroup(gtk_get_option_group(true));
#    ctx.add_group(gtkgroup);

#    // add GStreamer options
#    Glib::OptionGroup gstoptiongroup = Gst::get_option_group();
#    ctx.add_group(gstoptiongroup);

#    int argc;
#    char **argv = cmd->get_arguments(argc);

#    ctx.parse(argc, argv);

#    // show the gui
#    main = new LaunchGUI(argc, argv);

#    activate();
#    return 0;
#  }


#protected:

#  void on_activate()
#  {
#    add_window(*main);
#    main->show();
#  }

#protected:
#  LaunchGUI *main;
#};

#}



def main():

    #init Gstreamer. Has to be called first!
    Gst.init(sys.argv)
    
    Gst.debug_set_active(True)
    Gst.debug_set_colored(True)
    Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

    #GenGuiApp

    #return Gste::LaunchGUIApp().run(argc, argv);
#    app = Gtk.Application(application_id="org.gstgengui.gstgengui", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
#    app.connect("command-line", on_command_line)
#    app.connect("activate", on_activate)
#    app.run(sys.argv)

    return GenGuiApp().run(sys.argv)


if __name__ == '__main__':

    main()
    
