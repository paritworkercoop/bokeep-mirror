from gtk.glade import XML, get_widget_name

def load_glade_file_get_widgets_and_connect_signals(
    glade_file, root_widget, widget_holder=None, signal_recipiant=None ):
    glade_xml = XML(glade_file, root_widget)

    if signal_recipiant != None:
        glade_xml.signal_autoconnect( signal_recipiant )

    for widget in glade_xml.get_widget_prefix(""):
        setattr( widget_holder, get_widget_name(widget), widget )

