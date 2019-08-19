from __future__ import division
import datetime
import math
import os.path
import platform
import sys

from async_gui.engine import Task
from async_gui.toolkits.kivy import KivyEngine
from kivy import Logger
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
import plyer

from tunescope.analysis import analyze
from tunescope.audio import AudioDecoder, DecoderBuffer
from tunescope.filehistory import FileHistory
from tunescope.keyboardshortcuts import keyboard_action
from tunescope.player import Player
from tunescope.selections import SelectionList
from tunescope.theme import Theme
from tunescope.util import bind_properties, decode_file_path
from tunescope.widgets.aboutpage import AboutPage
from tunescope.widgets.selectionmenu import SelectionMenu


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

        self._setup_keyboard()

        self.selection_list = SelectionList()
        self.selection_list.bind(current=self.on_current_selection)
        self.player.bind(on_itunes_library_found=self.on_itunes_library_found)
        self.player.bind(selection_start=self.on_player_selection_start)
        self.player.bind(selection_end=self.on_player_selection_end)
        self._bind_selection_marker('selection_start')
        self._bind_selection_marker('selection_end')

        db_path = os.path.join(_DATA_DIR, 'file_history.sqlite3')
        self._file_history = FileHistory(db_path)

        self._open_dialog_path = os.path.join(os.path.expanduser('~'), 'Music')

    def _setup_keyboard(self):
        def keyboard_closed():
            pass

        keyboard = Window.request_keyboard(keyboard_closed, self, 'text')

        def on_key_down(keyboard, keycode, text, modifiers):
            if self.editing_selection_name:
                return
            action = keyboard_action(text, modifiers)
            if action == 'play_pause':
                self.player.playing = not self.player.playing
            elif action == 'open_file':
                self.show_open_dialog()
            elif action == 'show_recent_files':
                self.ids.recent_files_button.trigger_action()

        keyboard.bind(on_key_down=on_key_down)

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
            path=self._open_dialog_path,
            multiple=False,
            preview=True,
            title="Open media file")
        Window.raise_window()
        if selected_files is not None:
            self.open_file(selected_files[0])

    @_async_engine.async
    def open_file(self, file_path):
        if self.player.file_path is not None:
            self._save_state()
        file_path = os.path.abspath(decode_file_path(file_path))
        self._open_dialog_path = os.path.dirname(file_path)

        try:
            self.player.open_file(file_path)
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
            btn.file_path = os.path.join(record['directory'], record['filename'])
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
        padding = dp(10)
        modal = ModalView(
            size_hint=(0.7, None),
            anchor_x='left',
            anchor_y='top',
            padding=padding,
        )
        menu = SelectionMenu(
            dismiss=modal.dismiss,
            selection_list=self.selection_list
        )

        def on_menu_min_height(menu_, min_height):
            modal.height = min_height + 2 * padding

        menu.bind(min_height=on_menu_min_height)

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
        directory, filename = os.path.split(self.player.file_path)
        record = self._file_history.get(directory, filename)

        if record is None:
            self.state = {}
            return

        self.state = record.get('state', {})

        if record['directory'] != directory or record['filename'] != filename:
            Logger.info("_load_state: file moved:")
            Logger.info(u"  {} => {}".format(
                os.path.join(record['directory'], record['filename']),
                os.path.join(directory, filename)))
            self._file_history.delete(record['directory'], record['filename'])

    def _save_state(self):
        directory, filename = os.path.split(self.player.file_path)
        self._file_history.update(
            directory=directory,
            filename=filename,
            last_opened=self._file_opened_time,
            title=self.player.title,
            artist=self.player.artist,
            album=self.player.album,
            state=self.state,
        )

    def on_dropfile(self, window, file_path):
        self.open_file(file_path)

    def on_itunes_library_found(self, window):
        popup = Factory.ITunesConfirmationPopup()
        self.itunes_confirmation_popup = popup
        popup.ids.no_button.bind(on_press=popup.dismiss)
        popup.ids.yes_button.bind(on_press=self._grant_itunes_library_permission)
        popup.open()

    def on_player_selection_start(self, instance, value):
        self.selection_list.current.start = value

    def on_player_selection_end(self, instance, value):
        self.selection_list.current.end = value

    def on_current_selection(self, instance, value):
        selection = value
        self.player.selection_start = selection.start
        self.player.selection_end = selection.end

    def _grant_itunes_library_permission(self, instance):
        self.itunes_confirmation_popup.dismiss()
        self.player.load_itunes_library()
        self.player.load_metadata(self.player.file_path)

    def on_request_close(self, window):
        if self.player.file_path is not None:
            self._save_state()
        self.player.close_audio_device()
        return False  # False means go ahead and close the window

    def show_about_page(self):
        padding = dp(10)
        modal = ModalView(
            size_hint=(0.7, 0.7),
            anchor_x='center',
            anchor_y='center',
            padding=padding,
        )
        modal.add_widget(AboutPage(dismiss=modal.dismiss))
        modal.open()


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


if __name__ == '__main__':
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR)
    tunescope_app = TuneScopeApp()
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        Clock.schedule_once(lambda dt: tunescope_app.root.open_file(file_path), 0)
    tunescope_app.run()
