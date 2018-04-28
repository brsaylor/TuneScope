from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout


class SelectionMenu(ModalView):
    def __init__(self, selections, selection_index, on_confirm, **kwargs):
        super(SelectionMenu, self).__init__(**kwargs)

        
