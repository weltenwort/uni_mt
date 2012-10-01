from multiblob import euclid, mode, renderers, rules

class IntroMode(mode.Mode):
    HOTSPOT_RADIUS = 75.0
    RESET_HOTSPOT_OFFSET = 100
    START_HOTSPOT_OFFSET = -100

    def __init__(self, application):
        mode.Mode.__init__(self, application.state,
                rules = [
                    rules.IntroInputInterpreterRule(application.input_system, application.state.hotspots),
                    ],
                renderers = [
                    renderers.IntroFacetRenderer(),
                    renderers.HotspotRenderer()
                    ]
                )

        self.application = application

    def activate(self):
        mode.Mode.activate(self)
        self.application.state.hotspots.append(rules.Hotspot(
            point = euclid.Point2(
                self.state.window_width/2 + self.START_HOTSPOT_OFFSET,
                self.state.window_height/2
                ),
            radius = self.HOTSPOT_RADIUS,
            colour = (0.0, 1.0, 0.0, 1.0),
            callback = self.start
            ))
        self.application.state.hotspots.append(rules.Hotspot(
            point = euclid.Point2(
                self.state.window_width/2 + self.RESET_HOTSPOT_OFFSET,
                self.state.window_height/2
                ),
            radius = self.HOTSPOT_RADIUS,
            colour = (1.0, 0.0, 0.0, 1.0),
            callback = self.reset
            ))

    def deactivate(self):
        mode.Mode.deactivate(self)
        self.application.state.hotspots.pop()
        self.application.state.hotspots.pop()

    def start(self, event):
        self.log.debug(u"Start hotspot touched.")
        self.application.set_mode('main')

    def reset(self, event):
        self.log.debug(u"Reset hotspot touched.")
        self.application.state.reset_simple()

