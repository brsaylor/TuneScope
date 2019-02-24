import json
import os
import sys
import webbrowser

from kivy.lang.builder import Builder
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout

from tunescope.util import get_data_dir


urls = {
    'aubio': 'https://aubio.org/',
    'github': 'https://github.com/brsaylor/TuneScope',
    'gpl': 'https://www.gnu.org/licenses/',
    'gstreamer': 'https://gstreamer.freedesktop.org/',
    'kivy': 'https://kivy.org/',
    'rubberband': 'https://breakfastquay.com/rubberband/',
}


class AboutPage(FloatLayout):
    text = StringProperty()

    def __init__(self, dismiss=None, **kwargs):
        super(AboutPage, self).__init__(**kwargs)

        self.dismiss = dismiss

        version = ''
        with open(os.path.join(get_data_dir(), 'config.json')) as f:
            config = json.load(f)
            version = config['version']

        main_text = ''
        with open(os.path.join(get_data_dir(), 'about.txt')) as f:
            main_text = f.read().format(version=version)

        self.text = main_text + self.get_licenses_as_string()
    
    def open_link(self, ref):
        url = ref if ref.startswith('http') else urls.get(ref)
        if url:
            webbrowser.open(url)

    def get_licenses_as_string(self):
        pip_licenses = []
        with open(os.path.join(get_data_dir(), 'licenses', 'pip-licenses.json')) as f:
            pip_licenses = json.load(f, 'utf-8')
        return '\n'.join([
            (
                u"[b]{Name}[/b] {Version}\n" +
                u"Author: {Author}\n" +
                u"License: {License}\n" +
                u"[u][ref={URL}]{URL}[/ref][/u]\n"
            ).format(**pkg)
            for pkg in pip_licenses
        ])


if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    kv_dir = os.path.join(sys._MEIPASS, 'widgets')
else:
    kv_dir = os.path.dirname(os.path.realpath(__file__))

Builder.load_file(os.path.join(kv_dir, 'aboutpage.kv'))
