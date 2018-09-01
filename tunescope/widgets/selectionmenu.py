import os.path

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
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
        num_rows = len(self.cells)
        if num_selections > num_rows:
            for i in range(num_rows, num_selections):
                cells_row = [Cell() for j in range(5)]
                icon = TrashIcon(name='ios-trash', selection_index=i)
                cells_row[-1].add_widget(icon)
                icon.bind(on_release=self.delete)
                self.cells.append(cells_row)
                for cell in cells_row:
                    self.ids.grid.add_widget(cell)

        elif num_selections < num_rows:
            for i in range(num_rows - num_selections):
                cells_row = self.cells.pop()
                self.ids.grid.clear_widgets(children=cells_row)

        for i, s in enumerate(self.selection_list.selections):
            self.cells[i][0].text = str(s.number)
            self.cells[i][1].text = s.name or 'untitled'
            self.cells[i][2].text = str(s.start)
            self.cells[i][3].text = str(s.end)

    def on_header_press(self, header):
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
        # pdb.set_trace()
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
