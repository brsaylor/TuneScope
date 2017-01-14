import sys

from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup

from tunescope.player import Player


class MainWindow(Widget):
    """ Main application window """

    @property
    def player(self):
        return App.get_running_app().player

    def show_open_dialog(self):
        dialog = OpenDialog(open=self.open_file, cancel=self.dismiss_popup)
        self._popup = Popup(title="Open File", content=dialog, size_hint=(0.9, 0.9))
        self._popup.open()

    def open_file(self, path, filenames):
        """ Open the first filename in `filenames` with the player """
        if len(filenames) > 0:
            self.player.open_file(filenames[0])
        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()


class OpenDialog(FloatLayout):
    """ Open file dialog"""

    open = ObjectProperty(None)    # function bound to Open button
    cancel = ObjectProperty(None)  # function bound to Cancel button


class TuneScopeApp(App):
    """ Kivy application class """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None

    def build(self):
        self.player = Player()
        return MainWindow()

    @staticmethod
    def format_time(t):
        seconds = int(t)
        return "{}:{:02d}".format(seconds // 60, seconds % 60)


if __name__ == '__main__':
    tunescope_app = TuneScopeApp()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        Clock.schedule_once(lambda dt: tunescope_app.player.open_file(filename), 0)
    tunescope_app.run()
