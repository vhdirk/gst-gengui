
import argparse

from gettext import gettext as _, ngettext

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import GLib, GObject, Gtk, Gdk, GdkPixbuf, Gio, Gst


class CollapsedHelpAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None,
                 action_group=None):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.action_group=action_group

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help(file=None, action_group=self.action_group)
        parser.exit()


class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        
        self.collapse_groups = False
        if 'collapse_groups' in kwargs:
            self.collapse_groups = kwargs['collapse_groups']
            del kwargs['collapse_groups']
        
        add_help = True
        if 'add_help' in kwargs:
            add_help = kwargs['add_help']
            kwargs['add_help'] = False
        
        super().__init__(*args, **kwargs)
        self.add_help = add_help
        
        self._collapsed_groups = {}
        self._help_options = None
        
        if self.add_help and self.collapse_groups:
            self._help_options = self.add_argument_group(_('help options'))
            self._action_groups.insert(0, self._action_groups.pop())

        self.register('action', 'collapsed_help', CollapsedHelpAction)
        
        # add help argument if necessary
        # (using explicit default to override global argument_default)
        default_prefix = '-' if '-' in self.prefix_chars else self.prefix_chars[0]
        if self.add_help:
            group = self._help_options if self.collapse_groups else self._optionals
            group.add_argument(
                default_prefix+'h', default_prefix*2+'help',
                action='help', default=argparse.SUPPRESS,
                help=_('show this help message and exit'))
            if self.collapse_groups:
                group.add_argument(
                    default_prefix*2+'help-all',
                    action='collapsed_help', action_group='__all__',
                    default=argparse.SUPPRESS,
                    help=_('show all help options'))

    def add_argument_group(self, title=None, description=None, **kwargs):
        group = super().add_argument_group(title, description, **kwargs)


        # actually, no title.
        if title and description and self.add_help and self.collapse_groups:
            default_prefix = '-' if '-' in self.prefix_chars else self.prefix_chars[0]
            self._help_options.add_argument(
                default_prefix*2+'help-'+title,
                action='collapsed_help', action_group=group,
                default=argparse.SUPPRESS,
                help=_('show ')+description)
        return group


    def format_usage(self):
        formatter = self._get_formatter()
        
        if self.collapse_groups:
            usage_actions = []
            for group in self._action_groups:
                if group in [self._optionals, self._positionals]:
                    usage_actions.extend(group._group_actions)
        else:
            usage_actions = self._actions
       
        formatter.add_usage(self.usage, usage_actions,
                            self._mutually_exclusive_groups)
        return formatter.format_help()
        

    def format_help(self, action_group=None):
        formatter = self._get_formatter()

        # usage
        if self.collapse_groups:
            usage_actions = []
            for group in self._action_groups:
                if group in [self._optionals, self._positionals]:
                    usage_actions.extend(group._group_actions)
        else:
            usage_actions = self._actions
       
        formatter.add_usage(self.usage, usage_actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        if not self.collapse_groups:
            action_group = "__all__"

        # positionals, optionals and user-defined groups
        if action_group and action_group != "__all__":
            formatter.start_section(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        else:
            for group in self._action_groups:
                if action_group != "__all__":
                    if group not in [self._optionals, self._positionals, self._help_options]:
                        continue
                
                if not group.description:
                    formatter.start_section(group.title)
                    formatter.add_text(group.description)
                else:
                    formatter.start_section(group.description)
                formatter.add_arguments(group._group_actions)
                formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


    def print_help(self, file=None, action_group=None):
        if file is None:
            file = sys.stdout
        self._print_message(self.format_help(action_group), file)



def add_gtk_option_group(parser):
    group = parser.add_argument_group("gtk", _("GTK+ Options"))
    group.add_argument("--class", metavar=_("CLASS"),
                                 help=_("Program class as used by the window manager"))
    group.add_argument("--name", metavar=_("NAME"),
                                 help=_("Program name as used by the window manager"))
    group.add_argument("--display", metavar=_("DISPLAY"),
                                 help=_("X display to use"))
    group.add_argument("--gdk-debug", metavar=_("FLAGS"),
                                 help=_("GDK debugging flags to set"))
    group.add_argument("--gdk-no-debug", metavar=_("FLAGS"),
                                 help=_("GDK debugging flags to unset"))
                                 
    group.add_argument("--gtk-module", metavar="MODULES",
                                 help=_("Load additional GTK+ modules"))
    group.add_argument("--g-fatal-warnings", action="store_true", default="",
                                 help=_("Make all warnings fatal"))
    group.add_argument("--gtk-debug", metavar=_("FLAGS"),
                                 help=_("GTK+ debugging flags to set"))
    group.add_argument("--gtk-no-debug", metavar=_("FLAGS"),
                                 help=_("GTK+ debugging flags to set"))

    return group


def add_gst_option_group(parser):
    group = parser.add_argument_group("gst", "GStreamer Options")
    group.add_argument("--gst-version", action="store_true",
                                 help=_("Print the GStreamer version"))
    group.add_argument("--gst-fatal-warnings", action="store_true",
                                 help=_("Make all warnings fatal"))
    group.add_argument("--gst-debug-help", action="store_true",
                                 help=_("Print available debug categories and exit"))
    group.add_argument("--gst-debug-level", metavar=_("LEVEL"),
                                 help=_("Default debug level from 1 (only error) to 9 (anything) or 0 for no output"))
    group.add_argument("--gst-debug", metavar=_("LIST"),
                                 help=_("Comma-separated list of category_name:level pairs to set "
                                      "specific levels for the individual categories. Example: "
                                      "GST_AUTOPLUG:5,GST_ELEMENT_*:3"))
    group.add_argument("--gst-debug-no-color", action="store_true",
                                 help=_("Disable colored debugging output"))
    group.add_argument("--gst-debug-color-mode", metavar=_("MODE"),
                                 help=_("Changes coloring mode of the debug log. "
                                      "Possible modes: off, on, disable, auto, unix"))
    group.add_argument("--gst-debug-disable", action="store_true",
                                 help=_("Disable debugging"))
    group.add_argument("--gst-plugin-spew", action="store_true",
                                 help=_("Enable verbose plugin loading diagnostics"))
    group.add_argument("--gst-plugin-path", metavar=_("PATHS"),
                                 help=_("Colon-separated paths containing plugins"))
    group.add_argument("--gst-plugin-load", metavar=_("PLUGINS"),
                                 help=_("Comma-separated list of plugins to preload in addition to the "
                                      "list stored in environment variable GST_PLUGIN_PATH"))
    group.add_argument("--gst-disable-segtrap", action="store_true",
                                 help=_("Disable trapping of segmentation faults during plugin loading"))  
    group.add_argument("--gst-disable-registry-update", action="store_true",
                                 help=_("Disable updating the registry"))
    group.add_argument("--gst-disable-registry-fork", action="store_true",
                                 help=_("Disable spawning a helper process while scanning the registry")) 

    return group
    
    
    


class Notebook(Gtk.Notebook):

    __gsignals__ = {
        "page-remove-requested": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (int,)),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    
    def _tab_close_cb(self, button, index):
        self.emit("page-remove-requested", index)
    
    def append_page(self, child, tab_label, tab_icon=None, closable=True):

        tab_header = Gtk.HBox()
        
        if isinstance(tab_label, str):
            title_label = Gtk.Label(tab_label)
        else:
            title_label = tab_label
        
        image = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        close_button = Gtk.Button()
        close_button.set_image(image)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        
        tab_header.pack_start(title_label, expand=True, fill=True, padding=0)
        tab_header.pack_end(close_button, expand=False, fill=False, padding=0)
        tab_header.show_all()
        
        if not closable:
            close_button.hide()
        
        index = super().append_page(child, tab_header)
        
        if index >= -1:
            close_button.connect('clicked', self._tab_close_cb, index)
        
        return index
    
