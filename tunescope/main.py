from __future__ import division
import sys
import os.path
import platform
import datetime
import math

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from kivy.animation import Animation
import plyer
from async_gui.engine import Task
from async_gui.toolkits.kivy import KivyEngine

from tunescope.player import Player
from tunescope.audio import AudioDecoder, DecoderBuffer
from tunescope.analysis import analyze
from tunescope.util import bind_properties
from tunescope.selections import SelectionList
from tunescope.filehistory import FileHistory
from tunescope.theme import Theme


_async_engine = KivyEngine()

if platform.system() == 'Darwin':
    _DATA_DIR = os.path.expanduser('~/Library/Application Support/TuneScope/')
else:
    _DATA_DIR = os.path.expanduser('~/.local/share/TuneScope')


# TODO: Enable vsync:
# https://github.com/missionpinball/mpf-mc/issues/289
# https://kivy.org/docs/api-kivy.config.html#module-kivy.config


class MainWindow(Widget):
    """ Main application window """

    loading_progress = NumericProperty()
    selection_list = ObjectProperty(SelectionList(), rebind=True)
    editing_selection_name = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_dropfile=self.on_dropfile)
        self.selection_list = SelectionList()
        self.player.bind(on_itunes_library_found=self.on_itunes_library_found)
        self.player.bind(selection_start=self.on_player_selection_start)
        self.player.bind(selection_end=self.on_player_selection_end)
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

        yield Task(self._analyze_file)

    def _analyze_file(self):
        self.loading_progress = 0
        self.ids.loading_progress_indicator.opacity = 1

        window_size = 4096
        hop_size = window_size // 4
        audio_source = DecoderBuffer(AudioDecoder(self.player.file_path), 4096)
        duration_frames = int(math.ceil(self.player.duration * audio_source.samplerate))
        data_length = int(math.ceil(duration_frames / hop_size))
        self.ids.spectrogram.prepare(data_length)
        self.ids.pitch_plot.prepare(data_length)

        self.__hops_analyzed = 0

        def on_progress():
            self.__hops_analyzed += 1
            self.loading_progress = int(round(self.__hops_analyzed / data_length * 100))

        for page in analyze(audio_source,
                            window_size=window_size,
                            hop_size=hop_size,
                            on_progress=on_progress):
            # self.ids.pitch_plot.add_data(page['pitch'])
            self.ids.spectrogram.add_data(page['spectrum'])

        fadeout = Animation(opacity=0, duration=1)
        fadeout.start(self.ids.loading_progress_indicator)

    def show_recent_files_menu(self):
        dropdown = Factory.RecentFilesDropDown()
        records = self._file_history.recent(10)

        for i, record in enumerate(records):
            btn = Factory.RecentFileItem()
            btn.title = record['title']
            btn.artist = record['artist']
            btn.album = record['album']
            btn.file_path = record['file_path']
            btn.last = i == len(records) - 1
            btn.bind(on_press=lambda btn: dropdown.select(btn.file_path))
            dropdown.add_widget(btn)

            def on_mouse_pos(window, pos, btn=btn):
                btn.hover = btn.collide_point(*btn.to_widget(*pos))
            Window.bind(mouse_pos=on_mouse_pos)  # FIXME: unbind on dismiss?

        mainbutton = self.ids.recent_files_button
        mainbutton.bind(on_release=dropdown.open)

        def on_select(instance, file_path):
            mainbutton.unbind(on_release=dropdown.open)
            dropdown.dismiss()
            Clock.schedule_once(lambda dt: self.open_file(file_path), 0)

        dropdown.bind(on_select=on_select)

    def show_selection_menu(self):
        modal = ModalView(size_hint=(0.5, 1))
        menu = BoxLayout(orientation='vertical')

        def select_item(item):
            selection = self.selection_list.selections[item.index]
            self.selection_list.current = selection
            self.player.selection_start = selection.start
            self.player.selection_end = selection.end
            modal.dismiss()

        def add_selection(button):
            self.selection_list.add()
            modal.dismiss()

        for i, selection in enumerate(self.selection_list.selections):
            item = Factory.SelectionMenuItem()
            item.index = i
            item.number = selection.number
            item.name = selection.name
            item.last = False
            item.bind(on_release=select_item)
            menu.add_widget(item)

        add_button = Factory.MenuItem()
        add_button.text = "Add selection"
        add_button.last = True
        add_button.bind(on_press=add_selection)
        menu.add_widget(add_button)

        modal.add_widget(menu)
        modal.open()

    @property
    def state(self):
        """ Return the persistable app state as a dict """
        return dict(
            player=self.player.state,
            selection_list=self.selection_list.state,
        )

    @state.setter
    def state(self, values):
        """ Restore app state from a dict """

        try:
            self.selection_list.state = values['selection_list']
        except (KeyError, TypeError):
            self.selection_list.state = {}

        try:
            self.player.state = values['player']
        except (KeyError, TypeError):
            self.player.state = {}

    def _load_state(self):
        record = self._file_history.get(self.player.file_path)
        self.state = record['state']

    def _save_state(self):
        self._file_history.update(
            file_path=self.player.file_path,
            last_opened=self._file_opened_time,
            title=self.player.title,
            artist=self.player.artist,
            album=self.player.album,
            state=self.state,
        )

    def on_dropfile(self, window, filename):
        self.open_file(filename)

    def on_itunes_library_found(self, window):
        popup = Factory.ITunesConfirmationPopup()
        self.itunes_confirmation_popup = popup
        popup.ids.no_button.bind(on_press=popup.dismiss)
        popup.ids.yes_button.bind(on_press=self._grant_itunes_library_permission)
        popup.open()

    def on_selection_index(self, instance, value):
        selection = self.selections[self.selection_index]
        self.selection_name = selection['name']
        self.player.selection_start = selection['start']
        self.player.selection_end = selection['end']

    def on_player_selection_start(self, instance, value):
        self.selection_list.current.start = value

    def on_player_selection_end(self, instance, value):
        self.selection_list.current.end = value

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
