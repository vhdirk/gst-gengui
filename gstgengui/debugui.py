# -*- coding: utf-8 -*-

"""

"""

import collections
from operator import itemgetter

from gettext import gettext as _, ngettext

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, GObject, Gtk, Gdk, GdkPixbuf, Gio, Gst


def debug_level_get_name(debug_level):

    debug_name = Gst.debug_level_get_name(debug_level)

    if debug_name:
        return debug_name

    if debug_level == 0:
        return "NONE"

    return "##"




class AddCustomLevelDialog(Gtk.Dialog):
    
    def __init__(self, title, parent=None):
        super().__init__(title=title, 
                         parent=parent,
                         buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        
        self.set_border_width(10)

        scrolled_window = Gtk.ScrolledWindow()
        self.get_content_area().pack_start(scrolled_window, True, True, 6)
        
        self.add_categories_view = Gtk.TreeView()
        scrolled_window.add(self.add_categories_view)
                
        self.add_categories_store = Gtk.ListStore(str, str, GObject.TYPE_PYOBJECT)
        self.add_categories_view.set_model(self.add_categories_store)
        self.add_categories_view.set_headers_visible(True)
        self.add_categories_store.set_sort_column_id(ROW_DEBUG_NAME, Gtk.SortType.ASCENDING)
        
        column = Gtk.TreeViewColumn(_("Name"), Gtk.CellRendererText(), text=0)
        self.add_categories_view.append_column(column)
        
        column = Gtk.TreeViewColumn(_("Description"), Gtk.CellRendererText(), text=1)
        self.add_categories_view.append_column(column)

        selection = self.add_categories_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.show_all()

    @property
    def selected_categories(self):
        
        selection = self.add_categories_view.get_selection()
        
        model, rowiters = selection.get_selected_rows()
        
        return [model[rowiter][2] for rowiter in rowiters]
            
        
        
        

(
ROW_DEBUG_LEVEL,
ROW_DEBUG_NAME,
ROW_DEBUG_DESCRIPTION,
ROW_DEBUG_CATEGORY
) = range(4)





class DebugUI(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        
        self.add_window= None
        
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
        self.content .props.margin = 6
        self.add(self.content)
        
        default_frame = Gtk.Frame.new(_("Default level"))
        self.content.pack_start(default_frame, expand=False, fill=True, padding=6)
        
        default_box = Gtk.Box()
        self.default_adjustment = self.make_level_slider_ui(default_box).get_adjustment()
        default_frame.add(default_box)
        
        
        
        custom_frame = Gtk.Frame.new(_("Custom level"))
        self.content.pack_start(custom_frame, expand=True, fill=True, padding=6)
        
        custom_box = Gtk.VBox.new(Gtk.Orientation.VERTICAL, 2)
        custom_box.set_homogeneous(False)
        custom_frame.add(custom_box) 
        
        custom_level_box = Gtk.Box()
        
        self.custom_scale = self.make_level_slider_ui(custom_level_box)
        self.custom_adjustment = self.custom_scale.get_adjustment()
        custom_box.pack_start(custom_level_box, expand=False, fill=True, padding=0)
        self.custom_scale.set_sensitive(False)

        self.custom_level_view = Gtk.TreeView()
        custom_box.pack_start(self.custom_level_view, expand=True, fill=True, padding=0)
        
        button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        custom_box.pack_end(button_box, expand=False, fill=True, padding=0)
        
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        
        add_button = Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.BUTTON)
        button_box.pack_start(add_button, expand=False, fill=True, padding=0)
        
        remove_button = Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
        button_box.pack_start(remove_button, expand=False, fill=True, padding=0)
        
        refresh_button = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON)
        button_box.pack_start(refresh_button, expand=False, fill=True, padding=0)
        
        
        self.custom_level_store = Gtk.ListStore(str, str, str, GObject.TYPE_PYOBJECT)
        self.custom_level_view.set_model(self.custom_level_store)
        self.custom_level_view.set_headers_visible(True)
        self.custom_level_store.set_sort_column_id(ROW_DEBUG_NAME, Gtk.SortType.ASCENDING)
        
        column = Gtk.TreeViewColumn(_("Level"), Gtk.CellRendererText(), text=ROW_DEBUG_LEVEL)
        self.custom_level_view.append_column(column)

        column = Gtk.TreeViewColumn(_("Name"), Gtk.CellRendererText(), text=ROW_DEBUG_NAME)
        self.custom_level_view.append_column(column)
        
        column = Gtk.TreeViewColumn(_("Description"), Gtk.CellRendererText(), text=ROW_DEBUG_DESCRIPTION)
        self.custom_level_view.append_column(column)
        
        
        self.default_adjustment.set_value(Gst.debug_get_default_threshold())

        
        self.default_adjustment.connect('value-changed', self.set_default_level)
        self.sighandle_custom_adjustment = self.custom_adjustment.connect('value-changed', self.set_custom_level)
        
        add_button.connect('clicked', self.show_add_window)
        remove_button.connect('clicked', self.remove_custom_categories)
        refresh_button.connect('clicked', self.refresh_categories)
        
        selection = self.custom_level_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        selection.connect('changed', self.on_selection_changed)
        
        self.show_all()
        
        self.init_custom_levels()

        
        
        
    def make_level_slider_ui(self, box):
        
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
       
        label_min = Gtk.Label(_("no output"))
        label_max = Gtk.Label(_("lots of output"))
       
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, Gst.DebugLevel.COUNT-1, 1)
        
        box.pack_start(label_min, expand=False, fill=True, padding=6)
        box.pack_start(scale, expand=True, fill=True, padding=6)
        box.pack_end(label_max, expand=False, fill=True, padding=6)

        return scale
        

    def init_custom_levels(self):
        # Get the current default threshold. Add all categories set to a
        # different level to the custom list and refresh the tree


        default_threshold = Gst.debug_get_default_threshold()

        #TODO: when the pipeline is in the null state, this will only return the default
        # debug categories, and not those for all elements in the pipeline
        for category in Gst.debug_get_all_categories():
            
            if category.threshold != default_threshold:        
                row = []
                row.insert(ROW_DEBUG_LEVEL, debug_level_get_name(category.threshold))
                row.insert(ROW_DEBUG_NAME, category.name)
                row.insert(ROW_DEBUG_DESCRIPTION, category.description)
                row.insert(ROW_DEBUG_CATEGORY, category)

                self.custom_level_store.append(row)


    def refresh_categories(self, button=None):
        for row in self.custom_level_store:
            row[ROW_DEBUG_LEVEL] = debug_level_get_name(row[ROW_DEBUG_CATEGORY].threshold)        
 
        
    def set_default_level(self, adjustment):
        
        level = adjustment.get_value()
        
        if level == 8:
            return
        
        Gst.debug_set_default_threshold(level)
        self.refresh_categories()
        
        
    def set_custom_level(self, adjustment):
    
        level = adjustment.get_value()
        
        if level == 8:
            return

        # Walk through selected items in the list and set the debug category
        selection = self.custom_level_view.get_selection()
        model, rowiters = selection.get_selected_rows()
        
        for rowiter in rowiters:
            model[rowiter][ROW_DEBUG_CATEGORY].set_threshold(int(level))
        
        
        self.refresh_categories()
    
    
    def on_selection_changed(self, selection):
        model, rowiters = selection.get_selected_rows()
               
        self.custom_scale.set_sensitive(len(rowiters)>0)
        
        if len(rowiters) == 0:
            return
            
        #make the scale show the most common debug level, or the lowest if there's a draw
        levels = [model[rowiter][ROW_DEBUG_CATEGORY].threshold for rowiter in rowiters]
        
        counter = collections.Counter(levels)
        mc = sorted(counter.most_common(1), key=itemgetter(0))
        
        with GObject.signal_handler_block(self.custom_adjustment, self.sighandle_custom_adjustment):
            self.custom_adjustment.set_value(mc[0][0])
        
    
    
    def populate_add_categories(self):
        
        if not self.add_window:
            return

        self.add_window.add_categories_store.clear()
        
        for category in Gst.debug_get_all_categories():
            
            if self.category_in_customlist(category):
                continue

            self.add_window.add_categories_store.append([category.name, category.description, category])


    def category_in_customlist(self, category):
        for row in self.custom_level_store:
            if row[ROW_DEBUG_NAME] == category.name:
                return True
        return False
        
        
        
    def show_add_window(self, button=None):
    
        if not self.add_window:
            self.add_window = AddCustomLevelDialog(_("Select Categories"))
        
        self.populate_add_categories()
        response = self.add_window.run()
        
        if response == Gtk.ResponseType.OK:
            self.add_custom_categories(self.add_window.selected_categories)
        elif response == Gtk.ResponseType.CANCEL:
            pass

        self.add_window.hide()
        
       

    def add_custom_categories(self, category_list):
        
        for category in category_list:
            row = []
            row.insert(ROW_DEBUG_LEVEL, debug_level_get_name(category.threshold))
            row.insert(ROW_DEBUG_NAME, category.name)
            row.insert(ROW_DEBUG_DESCRIPTION, category.description)
            row.insert(ROW_DEBUG_CATEGORY, category)

            self.custom_level_store.append(row)


    def remove_custom_categories(self, button=None):
        
        selection = self.custom_level_view.get_selection()
        model, rowiters = selection.get_selected_rows()
        category_list = [model[rowiter][ROW_DEBUG_CATEGORY] for rowiter in rowiters]
        
        for row in self.custom_level_store:
            category = row[ROW_DEBUG_CATEGORY]
            if category in category_list:
                self.custom_level_store.remove(row.iter)
                category.reset_threshold()

        
        
