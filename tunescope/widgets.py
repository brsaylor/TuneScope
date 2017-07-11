from kivy.uix.slider import Slider


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
