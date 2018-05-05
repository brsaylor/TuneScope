from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty


class Selection(EventDispatcher):
    number = NumericProperty()
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

    def add(self):
        selection = Selection(
            number=max([s.number for s in self.selections]) + 1,
            start=self.current.start,
            end=self.current.end)
        self.selections.append(selection)
        self.current = selection

    def delete(self, selection):
        if selection not in self.selections:
            return

        if len(self.selections) == 1:
            self.current.number = 1
            self.current.name = ''
            self.current.start = 0.0
            self.current.end = 0.0
            return

        if selection == self.current:
            current_index = self.selections.index(self.current)
            if current_index == len(self.selections) - 1:
                new_current_index = current_index - 1
            else:
                new_current_index = current_index + 1
            self.current = self.selections[new_current_index]

        self.selections.remove(selection)

    def on_current(self, instance, value):
        if value not in self.selections:
            raise ValueError()
