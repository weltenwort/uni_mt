import logging

import pyglet
import pyglet.gl as gl

class GameWindow(pyglet.window.Window):
    background_color = (0, 0, 0, 1)
    alpha_size = 8

    def __init__(self, application, configuration={}):
        self.application   = application
        self.configuration = configuration

        self.log = logging.getLogger("GameWindow")

        platform = pyglet.window.get_platform()
        display  = platform.get_default_display()
        screen   = display.get_default_screen()
        screens  = display.get_screens()
        config   = screen.get_best_config(pyglet.gl.Config(
            #                alpha_size = self.alpha_size,
                ))
        context  = config.create_context(None)

        pyglet.window.Window.__init__(self, 
                vsync = False,
                context = context,
                )

        self.log.debug(u"Found %s screens: %s", len(screens), str(screens))

        self.set_fullscreen(
                self.configuration.get('fullscreen', False), 
                screens[self.configuration.get('screen', 0)],
                )
        if not self.fullscreen:
            self.set_size(
                    self.application.state.window_width, 
                    self.application.state.window_height
                    )

        gl.glClearColor(*self.background_color)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glEnable(gl.GL_LINE_SMOOTH)

    def on_resize(self, width, height):
        pyglet.window.Window.on_resize(self, width, height)
        self.application.state.window_width = self.width
        self.application.state.window_height = self.height

    def on_draw(self):
        self.clear()
        if self.mode:
            self.mode.render()

    @property
    def mode(self):
        return self.application.mode
