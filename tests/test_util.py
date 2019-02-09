# encoding: utf-8

import sys

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty
import pytest

from tunescope.util import bind_properties, decode_file_path


def test_bind_properties_single():

    class Dispatcher(EventDispatcher):
        x = NumericProperty(0)
        y = NumericProperty(0)

    dispatcher = Dispatcher()

    def callback(_dispatcher):
        _dispatcher.y = _dispatcher.x * 2

    bind_properties([(dispatcher, 'x')], callback)
    dispatcher.x = 1
    assert dispatcher.y == 2


def test_bind_properties_one_dispatcher_two_properties():

    class Dispatcher(EventDispatcher):
        x = NumericProperty(0)
        y = NumericProperty(0)
        z = NumericProperty(0)

    dispatcher = Dispatcher()

    def callback(_dispatcher):
        _dispatcher.z = _dispatcher.x + _dispatcher.y

    bind_properties([(dispatcher, 'x', 'y')], callback)
    dispatcher.x = 1
    assert dispatcher.z == 1
    dispatcher.y = 2
    assert dispatcher.z == 3


def test_bind_properties_two_dispatchers():

    class Dispatcher(EventDispatcher):
        x = NumericProperty(0)
        y = NumericProperty(0)
        z = NumericProperty(0)

    dispatcher1 = Dispatcher()
    dispatcher2 = Dispatcher()

    def callback(_dispatcher1, _dispatcher2):
        _dispatcher2.z = _dispatcher1.x + _dispatcher1.y + _dispatcher2.x + _dispatcher2.y

    bind_properties([(dispatcher1, 'x', 'y'), (dispatcher2, 'x')], callback)
    dispatcher1.x = 1
    dispatcher1.y = 2
    dispatcher2.x = 3
    dispatcher2.y = 4  # Should be ignored, because it is not bound
    assert dispatcher2.z == 6


class TestDecodeFilePath:
    """ Note: this assumes Python 2 """

    def test_str_input(self):
        s1 = 'test'
        assert type(s1) == str
        s2 = decode_file_path(s1)
        assert s2 == s1
        assert type(s2) == unicode
    
    def test_unicode_input(self):
        s1 = u'A Bhean Uda\u00ed Thall'
        assert s1 == u'A Bhean Udaí Thall'
        s2 = decode_file_path(s1)
        assert s2 == s1
        assert type(s2) == unicode

    def test_encoded_input(self):
        original_unicode = u'A Bhean Uda\u00ed Thall'
        assert original_unicode == u'A Bhean Udaí Thall'

        encoded = original_unicode.encode(sys.getfilesystemencoding())
        assert type(encoded) == str

        decoded = decode_file_path(encoded)
        assert type(decoded) == unicode
        assert decoded == original_unicode

    def test_invalid_input(self, monkeypatch):
        # We fail on decode error because we need to be able to retrieve the
        # file by its decoded path later
        monkeypatch.setattr(sys, 'getfilesystemencoding', lambda: 'utf-8')
        bad_string = '\xff'
        with pytest.raises(UnicodeDecodeError):
            decode_file_path(bad_string)
