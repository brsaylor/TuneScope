import json
import os

from kivy.core.text import LabelBase
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget

from .util import get_data_dir


class Icon(ButtonBehavior, Label):
    """ A pressable vector icon from the Ionicons icon set. Use `font_size` to
    set the size. See see tunescope/data/ionicons/ionicons.json or
    http://ionicons.com/ for the available icons. """

    name = StringProperty('')
    """ Name of the Ionicons icon (exclude the 'ion-' prefix) """

    _icons_loaded = False
    _icon_codes = {}

    def __init__(self, name='', **kwargs):
        super(Icon, self).__init__(**kwargs)
        self._load_icons()
        self.font_name = 'Ionicons'
        self.name = name

    @classmethod
    def _load_icons(cls):
        if cls._icons_loaded:
            return

        LabelBase.register(
            name='Ionicons',
            fn_regular=os.path.join(get_data_dir(), 'ionicons/ionicons.ttf'))
        with open(os.path.join(get_data_dir(), 'ionicons/ionicons.json')) as f:
            ionicons_data = json.load(f)

        for icon_info in ionicons_data['icons']:
            cls._icon_codes[icon_info['name']] = int(icon_info['code'], base=16)

        cls._icons_loaded = True

    def on_name(self, *args):
        self.text = unichr(self._icon_codes[self.name])


class TextButton(ButtonBehavior, Label):
    pass


class PlayerPositionSlider(Slider):
    """ A slider that dispatches 'on_drag_begin' and 'on_drag_end' events """

    def __init__(self, **kwargs):
        super(PlayerPositionSlider, self).__init__(**kwargs)
        self.register_event_type('on_drag_begin')
        self.register_event_type('on_drag_end')

    def on_touch_down(self, touch):
        if super(PlayerPositionSlider, self).on_touch_down(touch):
            self.dispatch('on_drag_begin')

    def on_touch_up(self, touch):
        if super(PlayerPositionSlider, self).on_touch_up(touch):
            self.dispatch('on_drag_end')

    def on_drag_begin(self):
        pass

    def on_drag_end(self):
        pass


class SelectionMarker(Widget):

    is_end_marker = BooleanProperty(False)

    drag_x = NumericProperty()
    """ This is what the x position of this widget would be if dragging actually
    caused it to move. """

    def __init__(self, **kwargs):
        super(SelectionMarker, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.ids.triangle.collide_point(*touch.pos):
            touch.grab(self)
            self._touch_offset = touch.x - self.x
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.drag_x = touch.x - self._touch_offset
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
