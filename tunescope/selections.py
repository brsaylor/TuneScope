from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty


class Selection(EventDispatcher):
    number = NumericProperty()    # user-visible auto-incrementing selection number
    name = StringProperty('')     # user-entered selection name
    start = NumericProperty(0.0)  # start time in seconds
    end = NumericProperty(0.0)    # end time in seconds

    def __init__(self, **kwargs):
        super(Selection, self).__init__(**kwargs)


class SelectionList(EventDispatcher):
    selections = ListProperty([])
    current = ObjectProperty(None, rebind=True)  # current Selection
    
    def __init__(self, **kwargs):
        super(SelectionList, self).__init__(**kwargs)
        self.selections.append(Selection(number=1))
        self.current = self.selections[0]

    def add(self):
        """ Make a new selection based on the current one and set it as current """

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

    def sort(self, sort_property, reverse=False):
        if sort_property not in self.current.properties().keys():
            raise ValueError()
        self.selections = sorted(
            self.selections,
            key=lambda s: getattr(s, sort_property),
            reverse=reverse)

    @property
    def state(self):
        """ Return a dictionary representing the persistable state of this SelectionList """

        return {
            'selections': [
                {
                    'number': s.number,
                    'name': s.name,
                    'start': s.start,
                    'end': s.end,
                }
                for s in self.selections
            ],
            'current_index': self.selections.index(self.current),
        }

    @state.setter
    def state(self, values):
        """ Initialize this SelectionList from a persisted state dictionary """
        # FIXME: validate

        self.selections = [Selection(**s) for s in values.get('selections', [])]
        if len(self.selections) == 0:
            self.selections.append(Selection(number=1))

        self.current = self.selections[values.get('current_index', 0)]
