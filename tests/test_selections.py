import pytest

from tunescope.selections import SelectionList, Selection


class TestSelection(object):
    def test_constructor(self):
        s = Selection()
        assert s.number == 1
        assert s.name == ''
        assert s.start == 0.0
        assert s.end == 0.0


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
        pass

    def test_delete(self):
        # should refuse to delete last selection
        pass

    def test_set_current(self):
        # should reject if the value being set is not a selection in the list
        pass

    def test_sort(self):
        pass

    def test_set_state(self):
        pass

    def test_get_state(self):
        pass
