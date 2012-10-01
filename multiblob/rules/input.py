"""Input rules go here."""
import math

import pyglet
import pyglet.gl as gl

from multiblob import rule, state, euclid, timing, renderer

unit_y = euclid.Vector2(0.0, 1.0)
unit_x = euclid.Vector2(1.0, 0.0)

class TouchInteraction(timing.TTLMixin, list):
    SIZE_SPLIT_THRESHOLD = 10.0
    MOVEMENT_THRESHOLD = 15.0
    SPLIT_AREA_FACTOR = 0.5

    # ttl mixin
    DEFAULT_TTL = 3.0

    def __init__(self, blob, inital_event=None):
        timing.TTLMixin.__init__(self)
        self.blob = blob
        self.is_inside = True
        if inital_event:
            self.append(inital_event)

    def is_past_threshold(self, next_event):
        if len(self) > 0:
            return next_event.position.distance(self[-1].position) > \
                    self.MOVEMENT_THRESHOLD
        else:
            return True

    def just_left_blob(self):
        if self.is_inside and len(self) > 1 and (not self.blob is None):
            if self.blob.position.distance(self[-1].position) * \
                    (1.0-self.get_blob_fraction()*1.1) > self.blob.radius:
                self.is_inside = False
                return True
        return False

    def get_leaving_angle(self):
        intersection = self[-1].position.connect(self.blob.circle).p1
        diff = intersection - self.blob.position
        if diff.normalized().dot(unit_x) >= 0:
            offset = 0.0
        else:
            offset = 360.0
        return abs(offset - \
                math.degrees(math.acos(diff.normalized().dot(unit_y))))

    def get_blob_fraction(self, area=None):
        if area is None and len(self) > 0:
            area = self[-1].area
        if area * self.SPLIT_AREA_FACTOR > self.blob.size:
            return 1
        else:
            return area * self.SPLIT_AREA_FACTOR / float(self.blob.size)

    def split_blob(self, fraction=None):
        if fraction is None:
            fraction = self.get_blob_fraction()

        new_blob = state.Blob(
                self.blob.player,
                self[-1].pos_x,
                self[-1].pos_y,
                fraction * self.blob.size,
                )
        self.blob.size -= new_blob.size
        new_blob.position = self[-1].position
        new_blob.just_splitted_from = self.blob
        self.blob = new_blob

    def __hash__(self):
        return id(self)

    def __str__(self):
        return "<TouchInteraction object_id='%s'>" % self.object_id

    @property
    def object_id(self):
        if len(self) > 0:
            return self[0].object_id
        else:
            return None

class InputInterpreterRule(rule.Rule):
    """Performs the interpretation of input events."""
    
    MIN_INTERVAL = 1.0

    def __init__(self, input_system):
        rule.Rule.__init__(self)
        self.state = None
        self.touch_objects = {}
        self.debug_batch = renderer.ManagedBatch()
        self.input_system = input_system

    def activate(self):
        self.input_system.push_handlers(self)

    def deactivate(self):
        self.input_system.remove_handlers(self)

    def on_multitouch_down(self, event):
        self.log.debug("Multitouch down")
        blob = self.get_touched_blob(event.pos_x, event.pos_y)
        ti = self.touch_objects[event.object_id] = TouchInteraction(
                blob,
                event
                )
        self.debug_batch.set(
                ti,
                1,
                pyglet.gl.GL_POINTS,
                InputEventDebugGroup(event),
                ('v2f', (event.pos_x, event.pos_y)),
                )
        if ti.blob:
            ti.blob.movement = []
        self.log.debug(u"Touched blob %s.", str(ti.blob))

    def on_multitouch_up(self, event):
        self.log.debug("Multitouch up")
        try:
            self.debug_batch.remove(self.touch_objects[event.object_id])
            del self.touch_objects[event.object_id]
        except KeyError:
            self.log.error(u"Multitouch 'UP' without prior 'DOWN': %s" % event)

    def on_multitouch_moved(self, event):
        #self.log.debug("Multitouch moved")
        try:
            touch_object = self.touch_objects[event.object_id]
            touch_object.reset_ttl()
            if touch_object.is_past_threshold(event):
                self.debug_batch.get(touch_object)[0].vertices = (event.pos_x, event.pos_y)
                touch_object.append(event)
                if not touch_object.blob is None:
                    fraction = touch_object.get_blob_fraction()
                    if fraction < 1 and fraction * touch_object.blob.size > 10.0:
                        # split if just left the circle
                        if touch_object.just_left_blob():
                            angle = touch_object.get_leaving_angle()
                            touch_object.split_blob()
                            self.log.debug(u"Just left blob %s at angle %f.", touch_object.blob, angle)
                    else:
                        # move blob
                        touch_object.blob.movement.append(touch_object[-1].position)
                else:
                    blob = self.get_touched_blob(event.pos_x, event.pos_y)
                    if blob:
                        blob.movement = []
                        touch_object.blob = blob

        except KeyError:
            self.log.error(u"Multitouch 'MOVED' without prior 'DOWN': %s" % event)

    def update(self, dt, state):
        self.state = state
        if not state.debug_objects.has_key("input_interpreter"):
            state.debug_objects['input_interpreter'] = self.debug_batch

        for touch_object in self.touch_objects.values():
            touch_object.decrease_ttl(self.MIN_INTERVAL + dt)
            if touch_object.should_die():
                self.log.debug(u"Removing %s due to timeout...", str(touch_object))
                self.on_multitouch_up(touch_object[-1])

    def get_touched_blob(self, x, y):
        """Return the blob at position (x, y), if the touch is unambiguous,
        None otherwise."""
        if self.state:
            touch_point = euclid.Point2(x, y)
            blobs = []
            for player in self.state.players:
                for blob in player.blobs:
                    if blob.position == touch_point or blob.position.distance(touch_point) < blob.radius:
                        blobs.append(blob)
            if len(blobs) == 1:
                return blobs[0]
        return None

class IntroInputInterpreterRule(rule.Rule):
    def __init__(self, input_system, hotspots):
        rule.Rule.__init__(self)
        self.state = None
        self.hotspots = hotspots
        self.input_system = input_system

    def activate(self):
        self.input_system.push_handlers(self)

    def deactivate(self):
        self.input_system.remove_handlers(self)

    def on_multitouch_down(self, event):
        if self.state:
            hotspot = self.get_touched_hotspot(event.pos_x, event.pos_y)
            if hotspot:
                if callable(hotspot.callback):
                    hotspot.callback(event)
            else:
                facet = self.state.facet_tree.get_nearest(event.pos_x, event.pos_y)

                if facet.is_border_facet:
                    if facet.home_facet_of:
                        self.state.remove_player(facet.home_facet_of)
                    else:
                        if self.state.players_free() > 0:
                            self.state.add_player(facet)

    def update(self, dt, state):
        self.state = state

    def get_touched_hotspot(self, x, y):
        p = euclid.Point2(x, y)
        for hotspot in self.hotspots:
            if hotspot.c.distance(p) <= hotspot.r:
                return hotspot
        return None

class InputEventDebugGroup(pyglet.graphics.Group):
    def __init__(self, event):
        pyglet.graphics.Group.__init__(self)
        self.event = event

    def set_state(self):
        gl.glPointSize(self.event.width + self.event.height)

class Hotspot(euclid.Circle):
    def __init__(self, point, radius, colour, callback=None):
        euclid.Circle.__init__(self, point, radius)
        self.colour = colour
        self.callback = callback
