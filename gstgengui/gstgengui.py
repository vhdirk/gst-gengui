#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GstGengui: utility for testing and controlling live GStreamer pipelines and elements.

"""

import os.path
import optparse
import argparse
import logging
import locale
import gettext
import sys

from contextlib import contextmanager


from gettext import gettext as _, ngettext

# Hack to force GIL creation
# See: https://bugzilla.gnome.org/show_bug.cgi?id=709223
# See: https://bugzilla.gnome.org/show_bug.cgi?id=710530
#import threading
#threading.Thread(target=lambda: None).start()

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, GObject, Gtk, Gdk, GdkPixbuf, Gio, Gst

if  GLib.pyglib_version < (3,10,0):
    # explicitely init glib threading
    GLib.threads_init()
elif GLib.pyglib_version < (3,10,2):
    # workaround for https://bugzilla.gnome.org/show_bug.cgi?id=710447
    import threading
    threading.Thread(target=lambda: None).start()


from misc import *
from elementui import *










(
ROW_ELEMENT_NAME,
ROW_ELEMENT_HANDLE,
ROW_ELEMENT_CHILD_ADDED,
ROW_ELEMENT_CHILD_REMOVED
) = range(4)





class LaunchGUI(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.Window.__init__(self, title=_("GstGengui"), application=app)
        self.statusbar = Gtk.Statusbar()
        
        self.handler_progress_bar_update = None
        
        # set up the GUI
        self.set_default_size(640,480)
        
        vbox = Gtk.VBox()
        self.add(vbox)

        try:
            icon = GdkPixbuf.Pixbuf.new_from_file("gst-launch.png")
            self.set_icon(icon)
        except GLib.GError as e:
            print (e)
            
        # status bar
        vbox.pack_end(self.statusbar, False, True, 6)
        
        #parse line
        parse_line = Gtk.HBox(False, 3)
        vbox.pack_start(parse_line, False, True, 6)
        
        self.pipe_combo = Gtk.ComboBoxText()
        self.combo_load_history()

        self.parse_button = Gtk.Button()
        self.parse_button.set_label(_("Parse"));

        parse_line.pack_start(self.pipe_combo, True, True, 6)
        parse_line.pack_start(self.parse_button, False, True, 6)

        self.parse_button.connect("clicked", self.on_parse)
        
        
        # media control
        media_line = Gtk.HBox(False, 3)
        vbox.pack_end(media_line, False, True, 6)
        self.start_button = Gtk.ToggleButton()
        self.start_button.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
        self.pause_button = Gtk.ToggleButton()
        self.pause_button.set_image(Gtk.Image.new_from_icon_name("media-playback-pause", Gtk.IconSize.BUTTON))
        self.start_button.set_sensitive(False)
        self.pause_button.set_sensitive(False)
        
        self.progress_bar = Gtk.HScale()
        self.progress_bar.set_draw_value(False)
        self.progress_bar.get_adjustment().set_lower(0)
        self.progress_bar.get_adjustment().set_upper(0)

        self.progress_position = Gtk.Label("00:00")
        self.progress_duration = Gtk.Label("00:00")

        media_line.pack_start(self.start_button, False, True, 6)
        media_line.pack_start(self.pause_button, False, True, 6)
        media_line.pack_start(self.progress_position, False, True, 6)
        media_line.pack_start(self.progress_bar, True, True, 6)
        media_line.pack_start(self.progress_duration, False, True, 6)

        self.start_button.connect("clicked", self.on_start)
        self.pause_button.connect("clicked", self.on_pause)

        self.handler_progress_bar_changed = self.progress_bar.get_adjustment().connect("value-changed", self.on_progress_changed)
        
        
        #  element tree
        self.view = Gtk.TreeView()
        self.store = Gtk.TreeStore(str, GObject.TYPE_OBJECT, int, int)
        self.view.set_model(self.store)
        self.view.set_headers_visible(False)
        column = Gtk.TreeViewColumn("Title", Gtk.CellRendererText(), text=ROW_ELEMENT_NAME)
        self.view.append_column(column)

        selection = self.view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self.on_selection_changed)


        self.notebook = Notebook()
        self.notebook.connect('page-remove-requested', self.on_page_remove_requested)
        #TODO: debug ui might be better represented on a different level as the element_uis
        # build_debug_page (notebook);

        # TODO: move this bunch to ElementUI
#        prop_box = Gtk.VBox(False, 5)
#        page_scroll = Gtk.ScrolledWindow()
#        page_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
#        page_scroll.add(prop_box)

        #notebook.append_page(page_scroll, Gtk.Label(_("Properties")))

        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        list_scroll.add(self.view)

        pane = Gtk.HPaned()
        pane.pack1(list_scroll)
        pane.pack2(self.notebook)

        vbox.pack_start(pane, True, True, 6)

        self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("Stopped"))


        #notebook.set_current_page(1)
        #self.element_ui = ElementUI()
        #prop_box.pack_start(self.element_ui, True, True, 6)
        #self.element_ui.show()

        if len(app.args.pipeline) > 0:
            pipeline_desc = " ".join(app.args.pipeline)
            
            #TODO: only unique entries allowed
            self.pipe_combo.append(pipeline_desc, pipeline_desc)
            pipe_id = len(self.pipe_combo)-1
            self.pipe_combo.set_active_id(pipeline_desc)
            self.on_parse()




    def update_progress_bar(self, *args):
    
        if not self.pipeline: return False

        (success_duration, duration) = self.pipeline.query_duration(Gst.Format.TIME)
        (success_position, position) = self.pipeline.query_position(Gst.Format.TIME)

        success = success_duration and success_position
        self.progress_bar.set_sensitive(success)


        with GObject.signal_handler_block(self.progress_bar.get_adjustment(), self.handler_progress_bar_changed):

            if success_duration:
                self.progress_bar.get_adjustment().set_upper(duration)
                if duration > 0:
                    self.progress_duration.set_text("%d:%02d" % ( (duration / Gst.SECOND) / 60, (duration / Gst.SECOND) % 60))
            
            if success_position:
                self.progress_bar.get_adjustment().set_value(position)
                self.progress_position.set_text("%d:%02d" % ( (position / Gst.SECOND) / 60,(position / Gst.SECOND) % 60))


        return success

    def on_progress_changed(self, *args):
        if not self.pipeline: return

        position = self.progress_bar.get_value();

        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position)


    def build_debug_page(self, notebook):
        pass
    #{
    #  //TODO: handle debug page lifetime
    #  Gste::DebugUI* debug_ui = new DebugUI();
    #  notebook.append_page(*debug_ui, _("Debug"));
    #}


    def on_parse(self, *args):
    
        try_pipe  = self.pipe_combo.get_active_text();
        print ("trying pipeline: ", try_pipe )

        self.pipeline = None
        try:
            self.pipeline = Gst.parse_launch(try_pipe)
        except GLib.GError as ex:
            self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("parse error: ") + ex.message)
            return
        
        if not self.pipeline:
            self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("unknown parse error"))
            return

        # TODO: close all element ui tabs
        #self.element_ui.clear_element()

        self.start_button.set_sensitive(True)

        self.store.clear()

        if GObject.type_from_name("GstChildProxy") in GObject.type_interfaces(self.pipeline):
            self.build_tree(self.store.get_iter_first(), self.pipeline)

        self.view.expand_all()

        #update the slider
        self.update_progress_bar();

        #append to history combo
#        if try_pipe:
#            self.pipe_combo.append_text(try_pipe)

        #append to history file
        self.append_history(try_pipe)


    def on_page_remove_requested(self, notebook, page_num):
        notebook.remove_page(page_num)
      


#-------------------------------------------------------------------------------
#TODO: this all belongs in an inspector class
#-------------------------------------------------------------------------------
    def build_tree(self, treeiter, childproxy):
        if not childproxy: return
        
        n_elements = childproxy.get_children_count()

        #iterate child elements
        for i in range(n_elements):
            elem = childproxy.get_child_by_index(i)
            
            if not elem:
                continue
            
            self.add_child_to_tree(treeiter, elem)


    def add_child_to_tree(self, treeiter, elem):
        
        row = []
        row.insert(ROW_ELEMENT_NAME, elem.get_name())
        row.insert(ROW_ELEMENT_HANDLE, elem)
        row.insert(ROW_ELEMENT_CHILD_ADDED, None)
        row.insert(ROW_ELEMENT_CHILD_REMOVED, None)

        newiter = self.store.append(treeiter, row)
        
        if GObject.type_from_name("GstChildProxy") in GObject.type_interfaces(elem):
            self.store[newiter][ROW_ELEMENT_CHILD_ADDED] = elem.connect('child-added', self.on_child_added, newiter)
            self.store[newiter][ROW_ELEMENT_CHILD_REMOVED] = elem.connect('child-removed', self.on_child_removed, newiter)
            
            self.build_tree(newiter, elem)

    def on_child_added(self, parent_elem, elem, name, titer):
        self.add_child_to_tree(titer, elem)
        self.view.expand_all()

    def on_child_removed(self, parent_elem, elem, name, titer):
        
        childiter = self.store.iter_children(titer)
        
        while childiter and self.store.iter_is_valid(childiter):
            #TODO: disconnect all children as well
            if self.store[childiter][ROW_ELEMENT_NAME] == elem.get_name():
                self._remove_with_children(childiter)
            else:
                childiter = self.store.iter_next(childiter)
    
    
    def _remove_with_children(self, titer):
        childiter = self.store.iter_children(titer)
        
        while childiter and self.store.iter_is_valid(childiter):
            
            if self.store.iter_has_child(childiter):
                self._remove_with_children(childiter)
            else:
                break
        
        if self.store[titer][ROW_ELEMENT_CHILD_ADDED]:
            GObject.signal_handler_disconnect(self.store[titer][ROW_ELEMENT_HANDLE], self.store[titer][ROW_ELEMENT_CHILD_ADDED])
        if self.store[titer][ROW_ELEMENT_CHILD_REMOVED]:
            GObject.signal_handler_disconnect(self.store[titer][ROW_ELEMENT_HANDLE], self.store[titer][ROW_ELEMENT_CHILD_REMOVED])
        self.store.remove(titer)

#-------------------------------------------------------------------------------
#\end TODO
#-------------------------------------------------------------------------------


    def on_start(self, *args):
        
        if self.handler_progress_bar_update:
            GObject.source_remove(self.handler_progress_bar_update)
            self.handler_progress_bar_update = None

        if self.start_button.get_active():
            ret = self.pipeline.set_state(Gst.State.PLAYING)

            #FIXME: this call might hang
            (ret, state, pending) = self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

            if ret != Gst.StateChangeReturn.FAILURE:
                self.start_button.set_image(Gtk.Image.new_from_icon_name("media-playback-stop", Gtk.IconSize.BUTTON))

                self.pause_button.set_sensitive(True)
                self.pause_button.set_active(False)
                self.parse_button.set_sensitive(False)
                self.pipe_combo.set_sensitive(False)
                self.statusbar.push(self.statusbar.get_context_id("pipeline"),_("Playing"));

                # TODO: handle this by letting element_ui connect to a signal
                #self.element_ui.disable_construct_only(True)
                self.handler_progress_bar_update = GObject.timeout_add(500, self.update_progress_bar)

            else:
                self.start_button.set_active(False)
                self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("Error while settings pipeline to playing state."))

        else:
            self.start_button.set_image(Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON))
            self.pause_button.set_sensitive(False)
            self.pause_button.set_active(False)
            self.parse_button.set_sensitive(True)
            self.pipe_combo.set_sensitive(True)
            self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("Stopped"))

            # TODO: handle this by letting element_ui connect to a signal
            #self.element_ui.disable_construct_only(False)

            self.pipeline.set_state(Gst.State.NULL)


    def on_pause(self, *args):
        if self.pause_button.get_active():
            self.pipeline.set_state(Gst.State.PAUSED)
            self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("Paused"))
        else:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.statusbar.push(self.statusbar.get_context_id("pipeline"), _("Playing"))



    def on_selection_changed(self, selection):
        
        store, titer = selection.get_selected()

        if not titer or not store.iter_is_valid(titer): return

        print (store[titer][ROW_ELEMENT_NAME])
        
        #TODO: make new element ui tab for element
        #self.element_ui.set_element(store[titer][ROW_ELEMENT_HANDLE]);
        page = ElementUI(store[titer][ROW_ELEMENT_HANDLE])
        idx = self.notebook.append_page(page, store[titer][ROW_ELEMENT_NAME])
        self.notebook.set_current_page(idx)
        page.show()

    def get_history_filename(self):
        
        history_path = os.path.join(GLib.get_user_config_dir(), "gsteditor" )
        
        if not GLib.file_test(history_path, GLib.FileTest.IS_DIR):
            history_dir = Gio.file_new_for_path(history_path)
            history_dir.make_directory_with_parents()

        history_file = os.path.join( history_path, "gst-launch-gui.history")
        if not GLib.file_test(history_file, GLib.FileTest.IS_REGULAR):
            history_f = Gio.file_new_for_path(history_file)
            history_f.create(Gio.FileCreateFlags.NONE)
        
        return history_file


    def combo_load_history(self):
        entries = self.load_history()

        for entry in entries:
            self.pipe_combo.prepend(entry, entry)


    def load_history(self):
        
        entries = []
        history_filename = self.get_history_filename()
        if not GLib.file_test(history_filename, GLib.FileTest.IS_REGULAR):
            return entries
        

        with open(history_filename, 'r') as histfile:
            entries = histfile.read().splitlines()
        return entries
        

    def append_history(self, pipeline_desc):
        
        history_filename = self.get_history_filename()
        entries = self.load_history()
        
        entries.append(pipeline_desc)
        
        #filter out duplicates
        entries = list(set(entries))
        
        #filter empty lines
        entries = [entry for entry in entries if len(entry) > 0]
        
        with open(history_filename, 'w') as histfile:
            histfile.write('\n'.join(str(entry) for entry in entries))








class GenGuiApp(Gtk.Application):
    '''
    Main application class
    '''
    
    main_window = None
    
    def __init__(self):
        # init the parent class
        # the Gio.ApplicationFlags.HANDLES_COMMAND_LINE flags tells that
        # we want to handle the command line and do_command_line will be called
        super().__init__(application_id="org.gstgengui.gstgengui", 
                        flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.args = None # store for parsed command line options

        self.connect("command-line", self.on_command_line)
        self.connect("activate", self.on_activate)

    def run(self, argv):
        #we handle arguments through argparse, not through gtkapplication
        super().run()

    def do_startup(self):
        '''
        Gtk.Application startup handler
        '''
        Gtk.Application.do_startup(self)

    def on_command_line(self, app, cmd):
        '''
        Gtk.Application command line handler
        called if Gio.ApplicationFlags.HANDLES_COMMAND_LINE is set.
        must call the self.do_activate() to get the application up and running.
        '''
        # make a command line parser
        parser = ArgumentParser(prog="gstgengui",
                                conflict_handler='resolve',
                                description="Utility for testing and controlling live GStreamer pipelines and elements",
                                add_help=True,
                                collapse_groups=True)
        
        add_gtk_option_group(parser)
        add_gst_option_group(parser)
        
        parser.add_argument( "-m", "--messages", action="store_true",
                                                 dest="show_messages",
                                                 default=False,
                                                 help="Show Gst.Element messages window before setting the pipeline to PLAYING")
        #parser.add_argument('-c', "--config", dest="config", help="Loads the given configuration file")
        #parser.add_argument('-p', "--preview", action="store_false", dest="display_preview", default=True, help="Disable inline preview")
        parser.add_argument('pipeline', type=str, nargs='*', help='Pipeline description')

        #TODO: is this the correct place for initialising libs?
        Gst.init(sys.argv)
        Gtk.init(sys.argv)
        Gdk.init(sys.argv)
        
        # parse the command line stored in args, but skip the first element (the filename)
        self.args = parser.parse_args(sys.argv[1:])
        
        # create our main window
        self.main_window = LaunchGUI(self)
        
        # call the main program do_activate() to start up the app
        self.activate()
        return 0
     
     
    def on_activate(self, app):
        '''
        Gtk.Application activate handler
        '''
        # connect a delete_event handler ((riggered by clicking on the windows close button)
        self.main_window.connect('delete_event', self.on_quit)
        # show the window
        self.main_window.show_all()

    def do_shutdown(self):
        '''
        Gtk.Application shutdown handler
        Do clean up before the application is closed.
        this is triggered when self.quit() is called.
        '''
        Gtk.Application.do_shutdown(self)

    def on_quit(self, widget, data):
        '''
        custom quit handler
        '''
        self.quit() # quit the application

    def quit(self, *args):
        print ('quitting')
        super().quit()

def main():
    app = GenGuiApp()
    import signal
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, app.quit, None)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
 
if __name__ == '__main__':
    main()
    
