import os.path
import json

from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from kivy.utils import get_color_from_hex

from .util import get_data_dir

theme_dir = os.path.join(get_data_dir(), 'themes')


class Theme(EventDispatcher):
    """ Contains properties for colors, etc. used by themed widgets """

    background_color            = ListProperty([0, 0, 0, 1])
    background_alt_color        = ListProperty([0.2, 0.2, 0.2, 1])
    text_color                  = ListProperty([1, 1, 1, 1])
    button_background_color     = ListProperty([0.5, 0.5, 0.5, 1])
    button_text_color           = ListProperty([1, 1, 1, 1])
    icon_color                  = ListProperty([1, 1, 1, 1])
    pitch_plot_background_color = ListProperty([0, 0, 0, 1])
    pitch_plot_line_color       = ListProperty([1, 1, 1, 1])
    progress_background_color   = ListProperty([0, 0, 0, 1])
    progress_text_color         = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(EventDispatcher, self).__init__(**kwargs)
        self.load_theme(os.path.join(theme_dir, 'solarized-dark.json'))

    def load_theme(self, file_path):
        with open(file_path) as f:
            theme = json.load(f)
        for prop_name in self.properties().keys():
            if prop_name in theme:
                setattr(self, prop_name, get_color_from_hex(theme[prop_name]))
