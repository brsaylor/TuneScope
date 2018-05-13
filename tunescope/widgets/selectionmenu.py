import os.path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty

from ..selections import SelectionList


class SelectionMenu(BoxLayout):
    selection_list = ObjectProperty(SelectionList(), rebind=True)
    def __init__(self, **kwargs):
        super(SelectionMenu, self).__init__(**kwargs)
        add = self.ids.grid.add_widget
        for s in self.selection_list.selections:
            add(Cell(text=str(s.number)))
            add(Cell(text=s.name))
            add(Cell(text=str(s.start)))
            add(Cell(text=str(s.end)))
            add(Cell(text='Trash'))

    def on_header_press(self, *args):
        print(args)


class Header(ButtonBehavior, BoxLayout):
    pass

class Cell(BoxLayout):
    pass

Builder.load_file(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'selectionmenu.kv'))
