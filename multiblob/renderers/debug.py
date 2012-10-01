from multiblob import renderer
import pyglet

class DebugRenderer(renderer.Renderer):
    """Renders debug information."""

    def __init__(self):
        renderer.Renderer.__init__(self)

    def render(self, game_state):
        pyglet.gl.glPointSize(3)
        for debug_object in game_state.debug_objects.itervalues():
            debug_object.draw()
