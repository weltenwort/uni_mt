"""Facet and ownership rules go here."""

from multiblob import rule

def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)

class FacetOwnershipRule(rule.Rule):
    MIN_INTERVAL = 0.1

    OCCUPATION_INCREMENT = 0.025
    OCCUPATION_DECREMENT = 0.025
    MIN_OCCUPATION = 0.0
    MAX_OCCUPATION = 1.0
    DEFAULT_OCCUPATION = 0.0
    BLOB_SIZE_OCCUPATION_FACTOR = 0.01

    def __init__(self):
        rule.Rule.__init__(self)
        self.facet_map = {}

    def update(self, dt, state):
        self.facet_map.clear()

        for player in state.players:
            for blob in player.blobs:
                facet = state.facet_tree.get_nearest(blob.pos_x, blob.pos_y)
                self.facet_map.setdefault(facet, []).append(blob)

        for facet, blob_list in self.facet_map.iteritems():
            players = set([ blob.player for blob in blob_list ])
            if len(players) == 1:
                player = blob_list[0].player
                facet.add_occupation(
                        player, 
                        self.OCCUPATION_INCREMENT * \
                                self.BLOB_SIZE_OCCUPATION_FACTOR * \
                                blob_list[0].size
                        )
                #facet.occupation[player] = clamp(
                        #facet.occupation.get(player, self.DEFAULT_OCCUPATION) +\
                                #self.OCCUPATION_INCREMENT * \
                                #self.BLOB_SIZE_OCCUPATION_FACTOR * \
                                #blob_list[0].size,
                        #self.MIN_OCCUPATION,
                        #self.MAX_OCCUPATION,
                        #)

            if len(players) >= 1:
                for player in facet.occupation.iterkeys():
                    if not player in players:
                        facet.add_occupation(
                                player, 
                                -1 * self.OCCUPATION_DECREMENT
                                )
                        #facet.occupation[player] = clamp(
                                #facet.occupation.get(player, self.DEFAULT_OCCUPATION) -\
                                        #self.OCCUPATION_DECREMENT,
                                #self.MIN_OCCUPATION,
                                #self.MAX_OCCUPATION,
                                #)

