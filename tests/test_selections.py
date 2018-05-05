import copy

import pytest

from tunescope.selections import SelectionList, Selection


class TestSelection(object):
    def test_constructor(self):
        s = Selection()
        assert s.name == ''
        assert s.start == 0.0
        assert s.end == 0.0


def make_three_selection_list():
    sl = SelectionList()
    sl.current.name = 'first'
    sl.current.start = 1.0
    sl.current.end = 2.0

    sl.add()
    sl.current.name = 'second'
    sl.current.start = 3.0
    sl.current.end = 4.0

    sl.add()
    sl.current.name = 'third'
    sl.current.start = 5.0
    sl.current.end = 6.0

    return sl


three_selection_list_state = {
    'selections': [
        {
            'number': 1,
            'name': 'first',
            'start': 1.0,
            'end': 2.0,
        },
        {
            'number': 2,
            'name': 'second',
            'start': 3.0,
            'end': 4.0,
        },
        {
            'number': 3,
            'name': 'third',
            'start': 5.0,
            'end': 6.0,
        },
    ],
    'current_index': 0,
}


class TestSelectionList(object):
    def test_constructor(self):
        sl = SelectionList()
        assert len(sl.selections) == 1
        assert sl.selections[0] == sl.current
        assert sl.current.number == 1
        assert sl.current.name == ''
        assert sl.current.start == 0.0
        assert sl.current.end == 0.0

    def test_add(self):
        # should append new with incremented number (be sure to account for
        # deleted selections), blank name, same start and end as current; new
        # should become current
        sl = SelectionList()
        sl.current.name = 'first'
        sl.current.start = 1.0
        sl.current.end = 2.0

        sl.add()

        assert len(sl.selections) == 2
        assert sl.selections[1] == sl.current
        assert sl.current.number == 2
        assert sl.current.name == ''
        assert sl.current.start == 1.0
        assert sl.current.end == 2.0

    def test_delete_last_remaining_selection(self):
        sl = SelectionList()
        sl.current.number = 2
        sl.current.name = 'second'
        sl.current.start = 1.0
        sl.current.end = 2.0

        sl.delete(sl.current)

        assert len(sl.selections) == 1
        assert sl.selections[0] == sl.current
        assert sl.current.number == 1
        assert sl.current.name == ''
        assert sl.current.start == 0.0
        assert sl.current.end == 0.0

    def test_delete_nonexistent_selection(self):
        sl = SelectionList()
        sl.current.number = 2

        s = Selection(number=99)
        sl.delete(s)

        assert len(sl.selections) == 1
        assert sl.current.number == 2

    def test_delete_not_current(self):
        sl = make_three_selection_list()
        sl.current = sl.selections[0]
        selection_to_delete = sl.selections[2]
        sl.delete(selection_to_delete)

        assert selection_to_delete not in sl.selections
        assert len(sl.selections) == 2

    def test_delete_current_when_current_not_last(self):
        sl = make_three_selection_list()
        sl.current = sl.selections[1]
        sl.delete(sl.current)

        assert len(sl.selections) == 2
        assert sl.current == sl.selections[1]

    def test_delete_current_when_current_is_last(self):
        sl = make_three_selection_list()
        sl.current = sl.selections[-1]
        sl.delete(sl.current)

        assert len(sl.selections) == 2
        assert sl.current == sl.selections[1]

    def test_set_current_to_nonexistent_selection(self):
        # should reject if the value being set is not a selection in the list
        sl = SelectionList()
        s = Selection()
        with pytest.raises(ValueError):
            sl.current = s

    def test_sort_by_nonexistent_property(self):
        sl = make_three_selection_list()
        with pytest.raises(ValueError):
            sl.sort('badprop')

    def test_sort(self):
        sl = make_three_selection_list()
        sl.selections[0].start = 10.0

        sl.sort('start')

        assert [s.start for s in sl.selections] == [3.0, 5.0, 10.0]

        sl.sort('name', reverse=True)

        assert [s.name for s in sl.selections] == ['third', 'second', 'first']

    def test_get_state(self):
        sl = make_three_selection_list()
        sl.current = sl.selections[1]
        expected_state = copy.copy(three_selection_list_state)
        expected_state['current_index'] = 1

        assert sl.state == expected_state

    def test_set_state(self):
        sl = SelectionList()
        state_to_set = copy.copy(three_selection_list_state)
        state_to_set['current_index'] = 1
        sl.state = three_selection_list_state
        sl.current = sl.selections[1]

        assert sl.state == state_to_set
