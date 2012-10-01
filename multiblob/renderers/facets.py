import pyglet.graphics
from multiblob import renderer
import pyglet.gl as gl

#
# Groups
#

class FacetFillGroup(pyglet.graphics.Group):
    def __init__(self, facet):
        pyglet.graphics.Group.__init__(self)
        self.facet = facet

    def set_state(self):
        gl.glPushAttrib(gl.GL_CURRENT_BIT)
        gl.glColor4f(*self.facet.colour)

    def unset_state(self):
        gl.glPopAttrib()

class FacetOutlineGroup(pyglet.graphics.Group):
    def __init__(self, facet):
        pyglet.graphics.Group.__init__(self)
        self.facet = facet

    def set_state(self):
        gl.glPushAttrib(gl.GL_LINE_BIT | gl.GL_CURRENT_BIT)
        gl.glLineWidth(2)
        gl.glColor3f(1,1,1)

    def unset_state(self):
        gl.glPopAttrib()

class IntroFacetFillGroup(pyglet.graphics.Group):
    BORDER_FACET_COLOUR = (.3, .3, .3, 1.0)
    INNER_FACET_COLOUR = (.0, .0, .0, 1.0)

    def __init__(self, facet):
        pyglet.graphics.Group.__init__(self)
        self.facet = facet

    def set_state(self):
        gl.glPushAttrib(gl.GL_CURRENT_BIT)
        if self.facet.home_facet_of:
            colour = self.facet.colour
        else:
            if self.facet.is_border_facet:
                colour = self.BORDER_FACET_COLOUR
            else:
                colour = self.INNER_FACET_COLOUR
        gl.glColor4f(*colour)

    def unset_state(self):
        gl.glPopAttrib()

class IntroFacetOutlineGroup(pyglet.graphics.Group):
    BORDER_FACET_COLOUR = (1.0, 1.0, 1.0, 1.0)
    INNER_FACET_COLOUR  = (0.0, 0.0, 0.0, 0.0)

    def __init__(self, facet):
        pyglet.graphics.Group.__init__(self)
        self.facet = facet

    def set_state(self):
        gl.glPushAttrib(gl.GL_LINE_BIT | gl.GL_CURRENT_BIT)
        gl.glLineWidth(2)
        if self.facet.is_border_facet:
            colour = self.BORDER_FACET_COLOUR
        else:
            colour = self.INNER_FACET_COLOUR
        gl.glColor4f(*colour)

    def unset_state(self):
        gl.glPopAttrib()

#
# Renderers
#

class FacetRenderer(renderer.Renderer):
    """Renders facets."""

    FILL_GROUP = FacetFillGroup
    OUTLINE_GROUP = FacetOutlineGroup

    def __init__(self):
        renderer.Renderer.__init__(self)
        self._facet_fill_batch = renderer.ManagedBatch()
        self._facet_outline_batch = renderer.ManagedBatch()

    def render(self, game_state):
        self._facet_outline_batch.clear(keep_keys=game_state.facets)
        self._facet_fill_batch.clear(keep_keys=game_state.facets)
        for facet in game_state.facets:
            num_vertices = len(facet.coords) / 2
            if self.FILL_GROUP and not facet in self._facet_fill_batch:
                self._facet_fill_batch.set(
                    facet, num_vertices, gl.GL_POLYGON, self.FILL_GROUP(facet),
                    ('v2f', facet.coords))
            if self.OUTLINE_GROUP and not facet in self._facet_outline_batch:
                self._facet_outline_batch.set(
                    facet, num_vertices, gl.GL_LINE_LOOP, self.OUTLINE_GROUP(facet),
                    ('v2f', facet.coords))
        self._facet_fill_batch.draw()
        self._facet_outline_batch.draw()

class IntroFacetRenderer(FacetRenderer):
    """Renders facets during intro."""

    FILL_GROUP = IntroFacetFillGroup
    OUTLINE_GROUP = IntroFacetOutlineGroup

class OutroFacetRenderer(FacetRenderer):
    """Renders facets during intro."""

    FILL_GROUP = FacetFillGroup
    OUTLINE_GROUP = None


