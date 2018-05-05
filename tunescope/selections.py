from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty


class Selection(EventDispatcher):
    number = NumericProperty(1)
    name = StringProperty('')
    start = NumericProperty(0.0)
    end = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(Selection, self).__init__(**kwargs)


class SelectionList(EventDispatcher):
    selections = ListProperty([])
    current = ObjectProperty(None, rebind=True)

    def __init__(self, **kwargs):
        super(SelectionList, self).__init__(**kwargs)
        self.current = Selection(number=1)
        self.selections.append(self.current)
        self.next_selection_number = 2
