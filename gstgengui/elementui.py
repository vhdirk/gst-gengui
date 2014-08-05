# -*- coding: utf-8 -*-

"""

"""

from gettext import gettext as _, ngettext

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, GObject, Gtk, Gdk, GdkPixbuf, Gio, Gst


INTEGER_GTYPES = (GObject.TYPE_INT, GObject.TYPE_UINT, GObject.TYPE_LONG, GObject.TYPE_ULONG, GObject.TYPE_INT64, GObject.TYPE_UINT64)
FLOAT_GTYPES = (GObject.TYPE_FLOAT, GObject.TYPE_DOUBLE)
NUMBER_GTYPES = INTEGER_GTYPES + FLOAT_GTYPES
STRING_GTYPES = (GObject.TYPE_CHAR, GObject.TYPE_UCHAR, GObject.TYPE_UNICHAR, GObject.TYPE_GSTRING, GObject.TYPE_STRING)




#TODO: use abstract base class here??

class ElementUIPropertyView(Gtk.VBox):
    
    @staticmethod
    def create(element, prop):
        
        if prop.value_type in NUMBER_GTYPES:
            return ElementUIPropertyViewNumber(element, prop)
        
        if prop.value_type == GObject.TYPE_BOOLEAN:
            return ElementUIPropertyViewSwitch(element, prop)
    
        if prop.value_type in STRING_GTYPES:
            if prop.name in ["location", "filename", "file", "uri"]:
                return ElementUIPropertyViewFile(element, prop)
            else:
                return ElementUIPropertyViewText(element, prop)
    
        if prop.value_type.is_a(GObject.TYPE_ENUM):
            return ElementUIPropertyViewChoice(element, prop)    
    
        return None
    
    
    
    def __init__(self, element, prop):
        super().__init__()
    
        self.element = element
        self.prop = prop
        self.set_hexpand(True)
        
        self.element_sighandle = None
        
        if prop.flags & GObject.PARAM_READABLE:
            self.element_sighandle = self.element.connect('notify::%s'%prop.name, self.update)

        self.set_sensitive(prop.flags & GObject.PARAM_WRITABLE);
                

    def update(self, elem, prop):
        raise NotImplementedError()
        
    def on_value_changed(self, origin):
        raise NotImplementedError()
        
    def block_element_signals(self):
        return GObject.signal_handler_block(self.element, self.element_sighandle)



    
#-------------------------------------------------------------------------------
# Number
#-------------------------------------------------------------------------------

class ElementUIPropertyViewNumber(ElementUIPropertyView):
    
    def __init__(self, element, prop):
        super().__init__(element, prop)
        self.is_integer = prop.value_type in INTEGER_GTYPES
        
        # spin button stuff
        grid_spin = Gtk.Grid()
        self.add(grid_spin)
        grid_spin.set_hexpand(True)

        self.show()

        self.label_lower = Gtk.Label("{}".format(prop.minimum))
        grid_spin.attach(self.label_lower, 0, 0, 1, 1)
        self.label_lower.set_justify(Gtk.Justification.LEFT)

        # As the step size is unknown and variable, 100 steps seems reasonable
        value_range = prop.maximum - prop.minimum
        stepsize = value_range/100.0
        
        self.adjustment = Gtk.Adjustment(prop.default_value, prop.minimum, prop.maximum, stepsize)
        self.spinbutton = Gtk.SpinButton()
        #self.spinbutton.set_adjustment(self.adjustment)
        num_digits = 0 if self.is_integer else 3
        self.spinbutton.configure(self.adjustment, stepsize, num_digits)

        grid_spin.attach(self.spinbutton, 1, 0, 2, 1)

        self.label_upper = Gtk.Label("{}".format(prop.maximum))
        grid_spin.attach(self.label_upper, 3, 0, 1, 1)
        self.label_upper.set_justify(Gtk.Justification.RIGHT)

        self.hscale = Gtk.HScale()
        self.hscale.set_adjustment(self.adjustment);
        grid_spin.attach(self.hscale, 0, 1, 4, 1);
        self.hscale.set_draw_value(False)
        self.hscale.set_hexpand(True)

        if not self.is_integer:
            self.hscale.set_digits(2)

        self.widget_sighandle = self.adjustment.connect('value-changed', self.on_value_changed)
                
        if prop.flags & GObject.PARAM_READABLE:
            self.update(element, prop)

        self.show_all()

    def on_value_changed(self, adjustment):
        #TODO: set async
        with self.block_element_signals():
            value = adjustment.get_value()
            
            if self.is_integer:
                value = int(value)
            
            self.element.set_property(self.prop.name, value)
        
        
    def update(self, elem, prop):
        with GObject.signal_handler_block(self.adjustment, self.widget_sighandle):
        
            value = elem.get_property(prop.name)
            if value is not None:
                self.adjustment.set_value(value)


#-------------------------------------------------------------------------------
# Toggle
#-------------------------------------------------------------------------------

class ElementUIPropertyViewSwitch(ElementUIPropertyView):
    
    def __init__(self, element, prop):
        super().__init__(element, prop)

        self.switch = Gtk.Switch()
        self.add(self.switch)
        
        self.widget_sighandle = self.switch.connect('activate', self.on_value_changed)
        
        if prop.flags & GObject.PARAM_READABLE:
            self.update(element, prop)
        
        self.show_all()

    def on_value_changed(self, switch):

        #TODO: set async
        with self.block_element_signals():
            self.element.set_property(self.prop.name, switch.get_active())


    def update(self, elem, prop):
        with GObject.signal_handler_block(self.switch, self.widget_sighandle):
            self.switch.set_active(elem.get_property(prop.name))

        
#-------------------------------------------------------------------------------
# Text
#-------------------------------------------------------------------------------

class ElementUIPropertyViewText(ElementUIPropertyView):
    
    def __init__(self, element, prop):
        super().__init__(element, prop)
        
        self.entry = Gtk.Entry()
        self.add(self.entry)
        
        self.widget_sighandle = self.entry.connect('changed', self.on_value_changed)

        if prop.flags & GObject.PARAM_READABLE:
            self.update(element, prop)

        self.show_all()

    def on_value_changed(self, entry):

        #TODO: set async
        with self.block_element_signals():
            self.element.set_property(self.prop.name, entry.get_text())
        
        
    def update(self, elem, prop):
        with GObject.signal_handler_block(self.entry, self.widget_sighandle):
        
            value = elem.get_property(prop.name)
            
            if value is None:
                value = ""
        
            self.entry.set_text(value)
            

#-------------------------------------------------------------------------------
# Choice
#-------------------------------------------------------------------------------

class ElementUIPropertyViewChoice(ElementUIPropertyView):
    
    def __init__(self, element, prop):
        super().__init__(element, prop)
        
        self.combo = Gtk.ComboBoxText()
        self.values = []
        
        self.add(self.combo)
        
        if prop.__gtype__.has_value_table:
            values = prop.enum_class.__enum_values__
            for index in values:
                self.combo.append(str(index), values[index].value_name)
       
        
        self.widget_sighandle = self.combo.connect('changed', self.on_value_changed)

        if prop.flags & GObject.PARAM_READABLE:
            self.update(element, prop)

        self.show_all()

    def on_value_changed(self, combo):

        #TODO: set async
        with self.block_element_signals():
            self.element.set_property(self.prop.name, combo.get_active())
        
        
    def update(self, elem, prop):
        with GObject.signal_handler_block(self.combo, self.widget_sighandle):
            self.combo.set_active(elem.get_property(prop.name))
        


#-------------------------------------------------------------------------------
# File
#-------------------------------------------------------------------------------

class ElementUIPropertyViewFile(ElementUIPropertyView):
    
    def __init__(self, element, prop):
        super().__init__(element, prop)

        self.file_button = Gtk.FileChooserButton()
        self.add(self.file_button)

        self.widget_sighandle = self.file_button.connect('file-set', self.on_value_changed)

        if prop.flags & GObject.PARAM_READABLE:
            self.update(element, prop)
        
        self.show_all()


    def on_value_changed(self, combo):

        if self.prop.name == 'uri':
            value = file_button.get_uri()
        else:
            value = file_button.get_filename()
        
        #TODO: set async
        with self.block_element_signals():
            self.element.set_property(self.prop.name, value)
    
    
    def update(self, elem, prop):
        with GObject.signal_handler_block(self.file_button, self.widget_sighandle):
            
            value = elem.get_property(prop.name)
            
            if value is None:
                value = ""
            
            if self.prop.name == 'uri':
                self.file_button.set_uri(value)
            else:
                self.file_button.set_filename(value)
        

#===============================================================================

class ElementUISignalParam(Gtk.Frame):

    _get_value = None
    _set_value = None

    def __init__(self, value_type):
        super().__init__()
        self.set_shadow_type(Gtk.ShadowType.NONE)
        
        widget = None
        if value_type in NUMBER_GTYPES:
            widget = Gtk.SpinButton()
            
            self._get_value = widget.get_value
            self._set_value = widget.set_value
        
        if value_type == GObject.TYPE_BOOLEAN:
            widget = Gtk.Switch()
                        
            self._get_value = widget.get_active
            self._set_value = widget.set_active
    
        if value_type in STRING_GTYPES:
#            if prop.name in ["location", "filename", "file", "uri"]:
#                return Gtk.FileChooserButton()
#            else:
            widget = Gtk.Entry()
            self._get_value = widget.get_text
            self._set_value = widget.set_text
    
        if value_type.is_a(GObject.TYPE_ENUM):
            widget = Gtk.ComboBoxText()
            
#            if value_type.has_value_table:
#                values = prop.enum_class.__enum_values__
#                for index in values:
#                    widget.append(str(index), values[index].value_name)
   
            self._get_value = widget.get_active
            self._set_value = widget.set_active
   
   
        if widget:
            self.add(widget)


    @property
    def value(self):
        if self._get_value:
            return self._get_value()
        else:
            return None
    
    @value.setter        
    def value(self, val):
        if self._set_value:
            self._set_value(val)
       


class ElementUISignalView(Gtk.Grid):
    
    def __init__(self, element, signal_query):
        super().__init__()
    
        self.element = element
        self.signal_query = signal_query
    
#        print ('constructing ui for signal', signal_query.signal_name)
#        
#        print ('count', signal_query.count)
#        print ('itype', signal_query.itype)
#        print ('return_type', signal_query.return_type)
#        print ('signal_id', signal_query.signal_id)
#        print ('index', signal_query.index)

#        print ('signal_flags', signal_query.signal_flags) 
        
        frame = Gtk.Frame()
        #frame.set_padding(6)
        self.attach(frame, 0, 0, 1, 2)
        self.param_grid = Gtk.Grid()
        frame.add(self.param_grid)
        

#        
#        spacer_label = Gtk.Label('=')
#        spacer_label.set_justify(Gtk.Justification.CENTER)
#        self.attach(spacer_label, 1, 0, 1, 2)

        self.param_widgets = []
#        
        for i, param_type in enumerate(signal_query.param_types):
            param_label = Gtk.Label(str(param_type))
            param_value = ElementUISignalParam(param_type)
            
            self.param_grid.attach(param_label, i, 0, 1, 1)
            self.param_grid.attach(param_value, i, 1, 1, 1)
            
            self.param_widgets.append(param_value)

        call_button = Gtk.Button()
        call_button.set_image(Gtk.Image.new_from_icon_name("go-jump", Gtk.IconSize.BUTTON))

        
        self.attach(call_button, i+1, 0, 1, 2)
        call_button.set_tooltip_text(_("call action signal: ") + signal_query.signal_name)

        
        
        return_label = Gtk.Label(str(signal_query.return_type))
        self.return_value = ElementUISignalParam(signal_query.return_type)
        
        self.attach(return_label, i+2, 0, 1, 1)
        self.attach(self.return_value, i+2, 1, 1, 1)
        
        
        call_button.connect('clicked', self.on_call_action)
        self.show_all()
        

    def on_call_action(self, button):
        
        func_args = [param.value for param in self.param_widgets]
        
        retval = self.element.emit(self.signal_query.signal_name, *func_args)
        self.return_value.value = retval
 

class ElementUI(Gtk.ScrolledWindow):

   
    (VIEW_MODE_COMPACT, VIEW_MODE_FULL) = range(2)
    
    
    def __init__(self, element, view_mode=VIEW_MODE_FULL):
        super().__init__() 

        self.view_mode = view_mode

        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        prop_box = Gtk.VBox(False, 5)
        self.add(prop_box)
            
        self.name = Gtk.Label()
        self.name.set_justify(Gtk.Justification.LEFT)
        self.name.set_margin_bottom(14)
        self.name.set_alignment(Gtk.Align.START, Gtk.Align.CENTER)

        self.optionmenu = Gtk.ComboBoxText()
        hpane = Gtk.HPaned()
        prop_box.pack_start(self.name, expand=True, fill=True, padding=6)
#        hpane.add1(self.name)
#        hpane.add2(self.optionmenu)
#        hpane.show()

        self.name.show();
        self.name.set_use_markup(True)
        self.set_page_title(element.get_name())

        #self.optionmenu.set_visible(self.view_mode is ElementUI.VIEW_MODE_COMPACT)

        spacing = 10;
        margin = 10;
        
        #TODO: move these to separate functions
        
        if len(GObject.list_properties(element)) > 0:
            
            #TODO: hide expanders when there's nothing to fill them with
            property_expander = Gtk.Expander.new(_("Properties"))
            property_expander.set_expanded(True)
            self.propertygrid = Gtk.Grid()
            property_expander.add(self.propertygrid)
            prop_box.pack_start(property_expander, expand=True, fill=True, padding=6)      

            self.propertygrid.set_column_spacing(spacing)
            self.propertygrid.set_row_spacing(spacing)


            self.propertygrid.set_margin_top(margin)
            self.propertygrid.set_margin_bottom(margin)
            self.propertygrid.set_margin_left(margin)
            self.propertygrid.set_margin_right(margin)
            
                 
            
            for i, prop in enumerate(GObject.list_properties(element)):
                prop_view = ElementUIPropertyView.create(element, prop)
                
                if not prop_view: continue

                prop_label = Gtk.Label(prop.name)
                prop_label.set_justify(Gtk.Justification.LEFT)
                prop_label.set_alignment(Gtk.Align.START, Gtk.Align.CENTER)
                prop_label.show()
                
                prop_label.set_tooltip_text(prop.blurb)
                self.propertygrid.attach(prop_label, 0, i+2, 1, 1)
        #        m_param_labels.push_back(param_label);

                #prop_view.disable_construct_only(playing);
                prop_view.show()
                self.propertygrid.attach(prop_view, 1, i+2, 1, 1);
        #        m_param_views.push_back(param_view);

        
        
        if len(GObject.signal_list_ids(element)) > 0:
            
            signal_expander = Gtk.Expander.new(_("Signals"))
            signal_expander.set_expanded(True)
            self.signalgrid = Gtk.Grid()
            signal_expander.add(self.signalgrid)
            prop_box.pack_start(signal_expander, expand=True, fill=True, padding=6)

            
            self.signalgrid.set_column_spacing(spacing)
            self.signalgrid.set_row_spacing(spacing)

            self.signalgrid.set_margin_top(margin)
            self.signalgrid.set_margin_bottom(margin)
            self.signalgrid.set_margin_left(margin)
            self.signalgrid.set_margin_right(margin)
            
            
            i = 0
            for sigid in GObject.signal_list_ids(element):
            
                sig_query = GObject.signal_query(sigid)
                
                #only show action signals
                if not sig_query.signal_flags & GObject.SignalFlags.ACTION:
                    continue
            
                sig_view = ElementUISignalView(element, sig_query)
                
                sig_label = Gtk.Label(sig_query.signal_name)
                sig_label.set_justify(Gtk.Justification.LEFT)
                sig_label.set_alignment(Gtk.Align.START, Gtk.Align.CENTER)
                sig_label.show()
                
                #prop_label.set_tooltip_text(prop.blurb)
                self.signalgrid.attach(sig_label, 0, i+2, 1, 1)
        #        m_param_labels.push_back(param_label);

                #prop_view.disable_construct_only(playing);
                sig_view.show()
                self.signalgrid.attach(sig_view, 1, i+2, 1, 1);

                i+=1
            

        self.show_all()
        self.connect('destroy', self.on_destroy)

    
    def set_page_title(self, title):
        self.name.set_markup("<span weight='bold' size='larger'>%s</span>"%title)



    def on_destroy(self, widget):
        #TODO: disconnect all signals and stuff
        pass






