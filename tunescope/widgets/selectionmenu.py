import os.path

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty

from ..selections import SelectionList
from ..widgets import Icon

class SelectionMenu(BoxLayout):
    selection_list = ObjectProperty(SelectionList(), rebind=True)
    sorted_by = StringProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.cells = []
        super(SelectionMenu, self).__init__(**kwargs)
        Clock.schedule_once(self.render_cells)

    def render_cells(self, *args):
        num_selections = len(self.selection_list.selections)
        rows_to_add = num_selections - len(self.cells)
        if rows_to_add > 0:
            for i in range(rows_to_add):
                cells_row = [Cell() for i in range(5)]
                icon = TrashIcon(name='ios-trash', selection_index=num_selections + i)
                cells_row[-1].add_widget(icon)
                icon.bind(on_release=self.delete)
                self.cells.append(cells_row)
                for cell in cells_row:
                    self.ids.grid.add_widget(cell)

        elif rows_to_add < 0:
            for i in range(-rows_to_add):
                cells_row = self.cells[i]
                self.ids.grid.clear_widgets(children=cells_row)

        for i, s in enumerate(self.selection_list.selections):
            self.cells[i][0].text = str(s.number)
            self.cells[i][1].text = str(s.name)
            self.cells[i][2].text = str(s.start)
            self.cells[i][3].text = str(s.end)


    def on_header_press(self, header):
        print(header.sort_by)
        if not header.sort_by:
            return

        if not header.is_sorted or header.reverse_sort:
            reverse = False
        else:
            reverse = True
        self.selection_list.sort(header.sort_by, reverse=reverse)
        self.sorted_by = header.sort_by
        header.reverse_sort = reverse
        self.render_cells()

    def delete(self, icon):
        selection = self.selection_list.selections[icon.selection_index]
        self.selection_list.delete(selection)
        self.render_cells()

class Header(ButtonBehavior, BoxLayout):
    pass


class Cell(BoxLayout):
    pass

class TrashIcon(Icon):
    selection_index = NumericProperty()


Builder.load_file(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'selectionmenu.kv'))
