import unittest

import mockito

from multiblob import input

class InputTest(unittest.TestCase):
    def test_packet_parser(self):
        """Test the packet parser with valid data."""
        data_1 = "ObjectType:1 ID:0 ObjectState:2 PosX:0.5 PosY:0.6 Area:0.0004 Width:0.0005 Height:0.003 Orientation:68.34"
        
        event = input.MultitouchEvent.from_packet(data_1)
        self.failUnlessEqual(event.object_type, "ONE_FINGER_TOUCH")

    def test_packet_parser_invalid(self):
        """Test the packet parser with invalid data."""
        invalid_data_1 = "ObjectType:1a ID:0 ObjectState:2 PosX:0.5 PosY:0.6 Area:0.0004 Width:0.0005 Height:0.003 Orientation:68.34"
        invalid_data_2 = "ObjectType:1 ID:0 ObjectState:2 PosX:0.5.0 PosY:0.6 Area:0.0004 Width:0.0005 Height:0.003 Orientation:68.34"
        invalid_data_3 = "ObjectType:9 ID:0 ObjectState:2 PosX:0.5.0 PosY:0.6 Area:0.0004 Width:0.0005 Height:0.003 Orientation:68.34"

        self.failUnlessRaises(
                input.InvalidEventDataError, 
                input.MultitouchEvent.from_packet,
                invalid_data_1
                )

        self.failUnlessRaises(
                input.InvalidEventDataError, 
                input.MultitouchEvent.from_packet,
                invalid_data_2
                )

        self.failUnlessRaises(
                input.InvalidEventDataError, 
                input.MultitouchEvent.from_packet,
                invalid_data_3
                )

    def test_dispatch(self):
        data_1 = r"chunkID:4//ObjectType:1 ID:0 ObjectState:2 PosX:0.5 PosY:0.6 Area:0.0004 Width:0.0005 Height:0.003 Orientation:68.34//ObjectType:1 ID:1 ObjectState:0 PosX:0.4 PosY:0.3 Area:0.0004 Width:0.0002 Height:0.005 Orientation:20.34//"
        window = mockito.Mock()
        window.width = 800
        window.height = 600

        dispatcher = input.InputSystem(window)
        mockito.when(dispatcher).dispatch_event(mockito.any(), mockito.any()).thenReturn(True)

        dispatcher.parse_packet(data_1)

        mockito.verify(dispatcher, times=1).dispatch_event("on_multitouch_down", mockito.any())
        mockito.verify(dispatcher, times=1).dispatch_event("on_multitouch_moved", mockito.any())

    def test_scale(self):
        """Test event coordinate scaling."""
        width, height = 800, 600

        event = input.MultitouchEvent(
            object_type  = "ONE_FINGER_TOUCH",
            object_id    = 0,
            object_state = "DOWN",
            pos_x        = 1.0,
            pos_y        = 1.0,
            area         = 1.0,
            height       = 1.0,
            width        = 1.0,
            orientation  = 1.0,
            )
        event.scale_to_dimensions(width, height)

        self.failUnlessEqual(event.pos_x, width)
        self.failUnlessEqual(event.pos_y, height)
        self.failUnlessEqual(event.area, width*height)
        self.failUnlessEqual(event.width, width)
        self.failUnlessEqual(event.height, height)

