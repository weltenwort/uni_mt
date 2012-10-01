import math

from multiblob import renderer
import pyglet
import pyglet.gl as gl

class HotspotRenderer(renderer.Renderer):
    """Renders hotspots."""

    UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
            for a in range(0, 360, 10)]

    @classmethod
    def _circle(cls, center, radius):
        result = []
        for x, y in cls.UNIT_CIRCLE:
            result.append(center[0] + x*radius)
            result.append(center[1] + y*radius)
        return result

    def __init__(self):
        renderer.Renderer.__init__(self)
        self._hotspot_batch = renderer.ManagedBatch()

    def render(self, game_state):
        self._hotspot_batch.clear(keep_keys=game_state.hotspots)
        for hotspot in game_state.hotspots:
            if not hotspot in self._hotspot_batch:
                self._hotspot_batch.set(
                    hotspot, 
                    36, 
                    gl.GL_POLYGON, 
                    HotSpotGroup(hotspot),
                    ('v2f', self._circle(hotspot.c, hotspot.r))
                    )

        self._hotspot_batch.draw()

class HotSpotGroup(pyglet.graphics.Group):
    def __init__(self, hotspot):
        pyglet.graphics.Group.__init__(self)
        self.hotspot = hotspot

    def set_state(self):
        gl.glPushAttrib(gl.GL_CURRENT_BIT)
        gl.glColor4f(*self.hotspot.colour)

    def unset_state(self):
        gl.glPopAttrib()

