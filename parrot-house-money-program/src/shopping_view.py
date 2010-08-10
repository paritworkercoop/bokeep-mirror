# gtk imports
import gtk
from gtk import TreeViewColumn, CellRendererText, CellRendererPixbuf

# imports from this project
from members import member_list, MEMBER_NAME
from trans_view import TransView
from widgets import \
     CellRendererTextEditable, CellRendererToggleEditable, \
     CellRendererNumberEditable
     

class ShoppingView(TransView):
    window_name = "shopping_view"

    def __init__(self, mainwindow, glade_file):
        TransView.__init__(self, mainwindow, glade_file)

        (DESC_COL, COST_COL, NAN_COL) = range(3)
        USEDBY_COL_OFFSET = NAN_COL+1
        GST_COL = USEDBY_COL_OFFSET + len(member_list)
        PST_COL = GST_COL + 1
        # Create a list of the TreeViewColumns that will appear in the
        # TreeView. The first two columns have only one CellRenderer and
        # can be set up fully here in initialization.
        # The third column is going to have multiple CellRenderers, which we
        # have to add later.
        columns = [
            TreeViewColumn('Description', CellRendererTextEditable(DESC_COL),
                           text=DESC_COL),
            TreeViewColumn('Cost', CellRendererNumberEditable(COST_COL),
                           text=COST_COL),
            TreeViewColumn('Used by'),
            TreeViewColumn('GST',
                           CellRendererToggleEditable(GST_COL),
                           active=GST_COL ),
            TreeViewColumn('PST',
                           CellRendererToggleEditable(PST_COL),
                           active=PST_COL )
            ]

        cost_column = columns[COST_COL]
        NAN_cell = CellRendererPixbuf()
        NAN_cell.set_property("stock-id", gtk.STOCK_DIALOG_ERROR)
        cost_column.pack_start(NAN_cell)
        cost_column.add_attribute( NAN_cell, 'visible', NAN_COL )

        # Add all the cells in the third column,
        # For each pair of label cell and toggle cell, set the label to
        # the member name, and tie the toggle to the model
        usedby_column = columns[COST_COL+1]
        for i, member in enumerate(member_list):
            member_name_cell = CellRendererText()
            toggle_cell = CellRendererToggleEditable(USEDBY_COL_OFFSET + i )
            usedby_column.pack_start(member_name_cell)
            usedby_column.pack_start(toggle_cell)

            toggle_cell.set_property("xalign", 0.0)
            member_name_cell.set_property("xalign", 1.0)
            member_name_cell.set_property('text', member[MEMBER_NAME] )
            usedby_column.add_attribute( toggle_cell, 'active',
                                         USEDBY_COL_OFFSET + i )
            
        for column in columns:
            self.item_list_tree_view.append_column( column )
            column.set_resizable(True)

        self.item_list_tree_view.columns_autosize()
        self.item_list_tree_view.show_all()

    def set_transaction(self, transaction):
        TransView.set_transaction(self, transaction)
        
        # give the model to each toggle cell, it needs it in the event
        # handler
        for col in self.item_list_tree_view.get_columns():
            for cell in col.get_cell_renderers():
                if isinstance(cell, CellRendererToggleEditable) or \
                   isinstance(cell, CellRendererTextEditable):
                    cell.model = self.transaction.item_list
        
        self.item_list_tree_view.set_model(self.transaction.item_list)

        self.item_list_tree_view.columns_autosize()

    def add_button_clicked(self, *args):
        list_to_append = ['', '0' ]
        list_to_append.extend( [False] * (1+len(member_list)+2) )
        self.transaction.item_list.append( list_to_append )

        self.item_list_tree_view.columns_autosize()

    def remove_button_clicked(self, *args):
        print args
