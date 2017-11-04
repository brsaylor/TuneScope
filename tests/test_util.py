from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

from tunescope.util import bind_properties


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
