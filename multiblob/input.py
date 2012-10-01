import logging
import re

import pyglet

from multiblob import euclid

class InvalidEventDataError(Exception):
    pass

class MultitouchEvent(object):
    packet_re = re.compile(r"ObjectType:([0-5]) ID:(\d+) ObjectState:([0-3]) PosX:([0-9\.e\-]+) PosY:([0-9\.e\-]+) Area:([0-9\.e\-]+) Width:([0-9\.e\-]+) Height:([0-9\.e\-]+) Orientation:([0-9\.e\-]+)")

    object_types = {
            0 : "NO_TYPE",
            1 : "ONE_FINGER_TOUCH",
            2 : "IPOD",
            3 : "IPAD",
            4 : "MARKER",
            5 : "HAND",
            }

    object_states = {
            0 : "DOWN",
            1 : "UP",
            2 : "MOVED",
            3 : "NO_TYPE",
            }

    def __init__(self, object_type, object_id, object_state, pos_x, pos_y, area,
            height, width, orientation):
        self.object_type  = object_type
        self.object_id    = object_id
        self.object_state = object_state
        self.pos_x        = pos_x
        self.pos_y        = pos_y
        self.area         = area
        self.height       = height
        self.width        = width
        self.orientation  = orientation

    @classmethod
    def from_packet(cls, packet_data):
        result = cls.packet_re.match(packet_data)
        if result:
            try:
                return cls(
                        object_type  = cls.object_types[int(result.group(1))],
                        object_id    = int(result.group(2)),
                        object_state = cls.object_states[int(result.group(3))],
                        pos_x        = float(result.group(4)),
                        pos_y        = 1.0 - float(result.group(5)),
                        area         = float(result.group(6)),
                        height       = float(result.group(7)),
                        width        = float(result.group(8)),
                        orientation  = float(result.group(9))
                        )
            except ValueError:
                pass
        raise InvalidEventDataError("Could not parse data: '%s'" % packet_data)
    
    def scale_to_dimensions(self, width, height):
        """Multiply all spacial parameters with the width and height factors."""
        self.pos_x *= float(width)
        self.pos_y *= float(height)
        self.area  *= float(width) * float(height)
        self.width *= float(width)
        self.height*= float(height)

    def update_position(self, event):
        """Updates spacial parameters from given event."""
        self.pos_x  = event.pos_x
        self.pos_y  = event.pos_y
        self.area   = event.area
        self.width  = event.width
        self.height = event.height

    def __str__(self):
        return "<MultitouchEvent object_type=%s object_id=%d object_state=%s pos_x=%f pos_y=%f>" % (
                self.object_type,
                self.object_id,
                self.object_state,
                self.pos_x,
                self.pos_y
                )

    @property
    def position(self):
        return euclid.Point2(self.pos_x, self.pos_y)

class InputSystem(pyglet.event.EventDispatcher):
    def __init__(self, application):
        pyglet.event.EventDispatcher.__init__(self)
        self.log = logging.getLogger("multiblob.input")

        self.application = application

    def parse_packet(self, data):
        input_objects = [ x for x in data.split(r'//') if x ]
        if len(input_objects) > 1:
            chunk_id = int(input_objects[0][8:])
            #self.log.debug(u"Received chunk %d with %d input objects.", 
            #        chunk_id, 
            #        len(input_objects) - 1
            #        )
            for input_object in input_objects[1:]:
                event = MultitouchEvent.from_packet(input_object)
                self.log.debug(u"Parsed event: %s" % str(event))
                event.scale_to_dimensions(
                        self.application.state.window_width, 
                        self.application.state.window_height
                        )
                if event.object_state == "DOWN":
                    self.dispatch_event('on_multitouch_down', event)
                elif event.object_state == "UP":
                    self.dispatch_event('on_multitouch_up', event)
                elif event.object_state == "MOVED":
                    self.dispatch_event('on_multitouch_moved', event)
        else:
            # we get many empty chunks when all touches stay on their positions
            pass
#            raise InvalidEventDataError("No input objects found in: '%s'" % data)

InputSystem.register_event_type('on_multitouch_down')
InputSystem.register_event_type('on_multitouch_up')
InputSystem.register_event_type('on_multitouch_moved')

class MouseMultitouchSimulator(object):
    def __init__(self, input_system):
        self._input_system = input_system
        self._last_id = 0

        self.log = logging.getLogger("multiblob.mousesimulator")

    def _get_area(self, button):

        if button & pyglet.window.mouse.LEFT:
            area = 1.0
        elif button & pyglet.window.mouse.MIDDLE:
            area = 0.00005
        else:
            area = 0.0001

        area *= self._input_system.application.state.window_width * self._input_system.application.state.window_height

        return area

    def on_mouse_press(self, x, y, button, modifiers):
        self._input_system.dispatch_event('on_multitouch_down', MultitouchEvent(
            object_type  = "ONE_FINGER_TOUCH",
            object_id    = self._last_id,
            object_state = "DOWN",
            pos_x        = float(x),
            pos_y        = float(y),
            area         = self._get_area(button),
            height       = 1.0,
            width        = 1.0,
            orientation  = 0.0,
            ))
        self._last_id += 1

    def on_mouse_release(self, x, y, button, modifiers):
        self._input_system.dispatch_event('on_multitouch_up', MultitouchEvent(
            object_type  = "ONE_FINGER_TOUCH",
            object_id    = self._last_id - 1,
            object_state = "UP",
            pos_x        = float(x),
            pos_y        = float(y),
            area         = self._get_area(button),
            height       = 1.0,
            width        = 1.0,
            orientation  = 0.0,
            ))

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._input_system.dispatch_event('on_multitouch_moved', MultitouchEvent(
            object_type  = "ONE_FINGER_TOUCH",
            object_id    = self._last_id - 1,
            object_state = "MOVED",
            pos_x        = float(x),
            pos_y        = float(y),
            area         = self._get_area(buttons),
            height       = 1.0,
            width        = 1.0,
            orientation  = 0.0,
            ))


