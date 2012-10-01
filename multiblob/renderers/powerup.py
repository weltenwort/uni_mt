import math

from multiblob import renderer, state
import pyglet
import pyglet.gl as gl

class PowerupRenderer(renderer.Renderer):
    """Renders powerups."""

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
        self._powerup_batch = renderer.ManagedBatch()
        #self._powerup_outline_batch = renderer.ManagedBatch()

    def render(self, game_state):
        self._powerup_batch.clear(keep_keys=game_state.powerups)
        for powerup in game_state.powerups:
            if not powerup in self._powerup_batch:
                circle = self._circle(powerup.position, powerup.radius)
                self._powerup_batch.set(
                    powerup, 
                    36, 
                    gl.GL_POLYGON, 
                    PowerupFillGroup(powerup),
                    ('v2f', circle)
                    )
                self._powerup_batch.set(
                    powerup, 
                    36, 
                    gl.GL_LINE_LOOP, 
                    PowerupOutlineGroup(powerup),
                    ('v2f', circle)
                    )
                if powerup.label:
                    with self._powerup_batch.use_key(powerup):
                        pyglet.text.Label(
                                text      = powerup.label,
                                font_size = powerup.label_font_size,
                                x         = powerup.position.x,
                                y         = powerup.position.y,
                                anchor_x  = 'center',
                                anchor_y  = 'center',
                                color     = (0, 0, 0, 255),
                                batch     = self._powerup_batch,
                                )

        self._powerup_batch.draw()
        #self._powerup_outline_batch.draw()

class PowerupFillGroup(pyglet.graphics.Group):
    def __init__(self, powerup):
        pyglet.graphics.Group.__init__(self)
        self.powerup = powerup

    def set_state(self):
        gl.glPushAttrib(gl.GL_CURRENT_BIT)
        gl.glColor4f(*self.powerup.colour)

    def unset_state(self):
        gl.glPopAttrib()

class PowerupOutlineGroup(pyglet.graphics.Group):
    def __init__(self, powerup):
        pyglet.graphics.Group.__init__(self)
        self.powerup = powerup

    def set_state(self):
        gl.glPushAttrib(gl.GL_CURRENT_BIT | gl.GL_LINE_BIT)
        gl.glLineWidth(1.5)
        gl.glColor4f(1, 1, 1, 1)

    def unset_state(self):
        gl.glPopAttrib()
