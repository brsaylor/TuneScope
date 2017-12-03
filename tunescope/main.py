from __future__ import division
import sys
import os.path
import platform
import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.animation import Animation
import plyer
from async_gui.engine import Task
from async_gui.toolkits.kivy import KivyEngine

from tunescope.player import Player
from tunescope.audio import AudioDecoder, DecoderBuffer
from tunescope.analysis import Analyzer
from tunescope.util import bind_properties
from tunescope.filehistory import FileHistory
from tunescope.theme import Theme


_async_engine = KivyEngine()

if platform.system() == 'Darwin':
    _DATA_DIR = os.path.expanduser('~/Library/Application Support/TuneScope/')
else:
    _DATA_DIR = os.path.expanduser('~/.local/share/TuneScope')


class MainWindow(Widget):
    """ Main application window """

    loading = BooleanProperty(False)
    loading_progress = NumericProperty(0)

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_dropfile=self.on_dropfile)
        self.player.bind(on_itunes_library_found=self.on_itunes_library_found)
        self._bind_selection_marker('selection_start')
        self._bind_selection_marker('selection_end')

        db_path = os.path.join(_DATA_DIR, 'file_history.sqlite3')
        self._file_history = FileHistory(db_path)

    def _bind_selection_marker(self, property_name):
        """ Connect the selection marker with the corresponding selection bound property """
        marker = self.ids[property_name + '_marker']
        player = self.player
        pitch_plot = self.ids.pitch_plot
        scroll_view = self.ids.scroll_view
        root = self

        def update_marker_x(root, player, pitch_plot):
            if player.duration == 0:
                return
            marker.x = (
                root.width / 2
                - (player.position - getattr(player, property_name))
                / player.duration * pitch_plot.width)

        def update_selection_bound(marker, drag_x):
            if pitch_plot.width == 0:
                return
            bound = ((drag_x + (scroll_view.scroll_x * pitch_plot.width) - root.width / 2)
                     / pitch_plot.width * player.duration)
            setattr(player, property_name, bound)

        bind_properties([
            (self, 'width'),
            (self.player, 'position', property_name, 'duration'),
            (self.ids.pitch_plot, 'width'),
        ], update_marker_x)

        marker.bind(drag_x=update_selection_bound)

    @property
    def player(self):
        return App.get_running_app().player

    def show_open_dialog(self):
        selected_files = plyer.filechooser.open_file(
            path=os.path.join(os.path.expanduser('~'), 'Music'),
            multiple=False,
            preview=True,
            title="Open media file")
        Window.raise_window()
        if selected_files is not None:
            self.open_file(selected_files[0])

    @_async_engine.async
    def open_file(self, filename):
        if self.player.file_path is not None:
            self._save_state()
        filename = os.path.abspath(filename)

        try:
            self.player.open_file(filename)
        except IOError as e:
            popup = Factory.ErrorDialog(title='Error opening file')
            popup.message = e.message
            popup.open()
            return

        self._load_state()
        self._file_opened_time = datetime.datetime.now()
        self._save_state()

        self.ids.pitch_plot.clear()
        self.loading = True
        self.loading_progress = 0
        self.ids.loading_progress_indicator.opacity = 1

        # FIXME: Refactor
        decoder = AudioDecoder(filename)
        buf = DecoderBuffer(decoder, 4096)
        analyzer = Analyzer(buf, self.player.duration,
                            on_progress=self._update_loading_progress)
        yield Task(analyzer.analyze)
        yield Task(self.ids.pitch_plot.plot, analyzer.pitch)
        self.loading = False
        fadeout = Animation(opacity=0, duration=1)
        fadeout.start(self.ids.loading_progress_indicator)

    def show_recent_files_menu(self):
        dropdown = Factory.RecentFilesDropDown()
        records = self._file_history.recent(10)
        for record in records:
            btn = Factory.RecentFileItem()
            btn.title = record['title']
            btn.artist = record['artist']
            btn.album = record['album']
            btn.file_path = record['file_path']
            btn.bind(on_press=lambda btn: dropdown.select(btn.file_path))
            dropdown.add_widget(btn)
        mainbutton = self.ids.recent_files_button
        mainbutton.bind(on_release=dropdown.open)

        def on_select(instance, file_path):
            mainbutton.unbind(on_release=dropdown.open)
            Clock.schedule_once(lambda dt: self.open_file(file_path), 0)

        dropdown.bind(on_select=on_select)

    def _load_state(self):
        record = self._file_history.get(self.player.file_path)
        try:
            self.player.state = record['state']['player']
        except (KeyError, TypeError):
            self.player.state = {}

    def _save_state(self):
        state = dict(
            player=self.player.state,
        )
        self._file_history.update(
            file_path=self.player.file_path,
            last_opened=self._file_opened_time,
            title=self.player.title,
            artist=self.player.artist,
            album=self.player.album,
            state=state,
        )

    def _update_loading_progress(self, progress):
        self.loading_progress = int(round(progress * 100))

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
        if self.player.file_path is not None:
            self._save_state()
        self.player.close_audio_device()
        return False  # False means go ahead and close the window


class TuneScopeApp(App):
    """ Kivy application class """

    def __init__(self, **kwargs):
        super(TuneScopeApp, self).__init__(**kwargs)
        self.player = None
        self.theme = None

    def build(self):
        self.player = Player()
        self.theme = Theme()
        return MainWindow()

    @staticmethod
    def format_time(t):
        minutes = int(t) // 60
        seconds = t - 60 * minutes
        return "{}:{:05.2f}".format(minutes, seconds)


if __name__ == '__main__':
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR)
    tunescope_app = TuneScopeApp()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        Clock.schedule_once(lambda dt: tunescope_app.root.open_file(filename), 0)
    tunescope_app.run()
