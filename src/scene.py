class Scene:

    wants_mouse_grab = False
    render_below = False

    def __init__(self, app):
        self.app = app

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass
