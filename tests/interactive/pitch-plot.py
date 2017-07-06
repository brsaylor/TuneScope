import numpy as np
from kivy.uix.boxlayout import BoxLayout
from kivy.lang.builder import Builder
from kivy.base import runTouchApp

from tunescope.visualization import PitchPlot


class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

    def plot_random_pitches(self, pitch_plot):
        duration = 10
        samplerate = 44100
        hop_size = 512
        num_pitches = samplerate * duration / hop_size

        pitch_delta = (np.random.random(num_pitches) - 0.5)
        pitch_delta[0] = 60
        pitches = pitch_delta.cumsum()
        print(pitches)

        pitch_plot.plot(pitches)


root_widget = Builder.load_string("""
#:import PitchPlot tunescope.visualization.PitchPlot

RootWidget:
    orientation: 'vertical'
    Button:
        text: 'Plot random pitches'
        on_release: root.plot_random_pitches(pitch_plot)
    Slider:
        min: 1
        max: 10
        value: pitch_plot.xscale
        on_value: pitch_plot.xscale = self.value
    Slider:
        min: 1
        max: 10
        value: pitch_plot.yscale
        on_value: pitch_plot.yscale = self.value
    PitchPlot:
        id: pitch_plot
""")

runTouchApp(root_widget)
