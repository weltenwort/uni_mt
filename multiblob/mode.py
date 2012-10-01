import logging

from multiblob import rule

class Mode(object):
    def __init__(self, state, renderers=[], rules=[]):
        self.state = state
        self.rules = rule.GameRuleSystem(
                state = self.state, 
                rules = rules,
                )
        self.renderers = renderers

        self.log = logging.getLogger(self.__class__.__name__)

    def update_rules(self, dt):
        if self.rules:
            self.rules.update(dt)

    def render(self):
        for renderer in self.renderers:
            renderer.render(self.state)

    def activate(self):
        self.log.info(u"Activating mode '%s'...", self.__class__.__name__)
        self.rules.activate()

    def deactivate(self):
        self.log.info(u"Deactivating mode '%s'...", self.__class__.__name__)
        self.rules.deactivate()

