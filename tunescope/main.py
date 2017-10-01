from __future__ import division
import sys
import os.path

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.factory import Factory
import plyer
from async_gui.engine import Task
from async_gui.toolkits.kivy import KivyEngine

from tunescope.player import Player
from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.analysis import Analyzer


_async_engine = KivyEngine()


class MainWindow(Widget):
    """ Main application window """

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_dropfile=self.on_dropfile)
        self.player.bind(on_itunes_library_found=self.on_itunes_library_found)

    @property
    def player(self):
        return App.get_running_app().player

    def show_open_dialog(self):
        selected_files = plyer.filechooser.open_file(
            path=os.path.join(os.path.expanduser('~'), 'Music'),
            multiple=False,
            preview=True,
            title="Open media file")
        if selected_files is not None:
            self.open_file(selected_files[0])

    @_async_engine.async
    def open_file(self, filename):
        filename = os.path.abspath(filename)
        self.player.open_file(filename)

        # FIXME: Refactor
        decoder = AudioDecoder(filename)
        buf = DecoderBuffer(decoder, 4096)
        analyzer = Analyzer(buf, self.player.duration)

        yield Task(analyzer.analyze)
        yield Task(self.ids.pitch_plot.plot, analyzer.pitch)

    def on_dropfile(self, window, filename):
        self.open_file(filename)

    def on_itunes_library_found(self, window):
        popup = Factory.ITunesConfirmationPopup()
        self.itunes_confirmation_popup = popup
        popup.ids.no_button.bind(on_press=popup.dismiss)
        popup.ids.yes_button.bind(on_press=self._grant_itunes_library_permission)
        popup.open()

    def _grant_itunes_library_permission(self, instance):
        self.itunes_confirmation_popup.dismiss()
        self.player.load_itunes_library()
        self.player.load_metadata()

    def on_request_close(self, window):
        self.player.close_audio_device()
        return False  # False means go ahead and close the window



class TuneScopeApp(App):
    """ Kivy application class """

    def __init__(self, **kwargs):
        super(TuneScopeApp, self).__init__(**kwargs)
        self.player = None

    def build(self):
        self.player = Player()
        return MainWindow()

    @staticmethod
    def format_time(t):
        minutes = int(t) // 60
        seconds = t - 60 * minutes
        return "{}:{:05.2f}".format(minutes, seconds)


if __name__ == '__main__':
    tunescope_app = TuneScopeApp()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        Clock.schedule_once(lambda dt: tunescope_app.root.open_file(filename), 0)
    tunescope_app.run()
