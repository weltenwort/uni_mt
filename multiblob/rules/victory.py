"""Victory rules go here."""

from multiblob import rule

class LastBlobStandingVictoyRule(rule.Rule):
    """Determines victory, if all except one players have been destroyed."""

    MIN_INTERVAL = 1.0

    def __init__(self, application):
        rule.Rule.__init__(self)
        self.application = application

    def update(self, dt, state):
        for player in state.players:
            if len(player.blobs) == 0:
                has_facets = False
                for facet in state.facets:
                    if facet.owner is player:
                        has_facets = True
                if not has_facets:
                    self.log.info(u"Player %s has been defeated.", player)
                    state.remove_player(player)

        if len(state.players) <= 1:
            self.log.info(u"Last players alive: %s", state.players)
            self.application.set_mode('outro')
