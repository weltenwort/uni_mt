import pyglet

from multiblob import euclid, mode, renderers, rules

class OutroMode(mode.Mode):
    HOTSPOT_RADIUS = 75.0
    QUIT_HOTSPOT_OFFSET = 100
    RESTART_HOTSPOT_OFFSET = -100

    def __init__(self, application):
        mode.Mode.__init__(self, application.state,
                rules = [
                    rules.IntroInputInterpreterRule(application.input_system, application.state.hotspots),
                    ],
                renderers = [
                    renderers.OutroFacetRenderer(),
                    renderers.HotspotRenderer()
                    ]
                )

        self.application = application

    def activate(self):
        mode.Mode.activate(self)
        self.application.state.hotspots.append(rules.Hotspot(
            point = euclid.Point2(
                self.state.window_width/2 + self.RESTART_HOTSPOT_OFFSET,
                self.state.window_height/2
                ),
            radius = self.HOTSPOT_RADIUS,
            colour = (0.0, 1.0, 0.0, 1.0),
            callback = self.restart
            ))
        self.application.state.hotspots.append(rules.Hotspot(
            point = euclid.Point2(
                self.state.window_width/2 + self.QUIT_HOTSPOT_OFFSET,
                self.state.window_height/2
                ),
            radius = self.HOTSPOT_RADIUS,
            colour = (1.0, 0.0, 0.0, 1.0),
            callback = self.quit
            ))

    def deactivate(self):
        mode.Mode.deactivate(self)
        self.application.state.hotspots.pop()
        self.application.state.hotspots.pop()

    def restart(self, event):
        self.log.debug(u"Restart hotspot touched.")
        self.application.state.reset_simple()
        self.application.set_mode('intro')

    def quit(self, event):
        self.log.debug(u"Quit hotspot touched.")
        pyglet.app.exit()

