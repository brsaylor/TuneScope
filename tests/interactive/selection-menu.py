from kivy.uix.boxlayout import BoxLayout
from kivy.base import runTouchApp
from kivy.uix.label import Label

from tunescope.widgets.selectionmenu import SelectionMenu
from tunescope.selections import SelectionList

class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(orientation='vertical')
        sl = SelectionList()
        sl.current.name = 'zz_first'
        sl.current.start = 1.0
        sl.current.end = 2.0

        sl.add()
        sl.current.name = 'aa_second'
        sl.current.start = 3.0
        sl.current.end = 4.0

        sl.add()
        sl.current.name = 'third'
        sl.current.start = 5.0
        sl.current.end = 6.0
        self.add_widget(SelectionMenu(selection_list=sl))


root_widget = RootWidget()
runTouchApp(root_widget)
