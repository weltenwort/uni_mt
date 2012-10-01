from multiblob import rule

class ScoreRule(rule.Rule):
    SCORE_INCREMENT = 1.0

    def update(self, dt, state):
        for facet in state.facets:
            if not getattr(facet, 'protected', False):
                if facet.owner:
                    facet.owner.score += SCORE_INCREMENT
