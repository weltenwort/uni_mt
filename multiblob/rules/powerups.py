"""Blob rules go here."""
import pyglet

import random

from multiblob import euclid, rule, state as game_state

def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)

class PowerupGenerationRule(rule.Rule):
    """Places powerups on the game board"""
    
    MIN_INTERVAL = 15.0

    MAX_POWERUPS = 2

    powerups = [
            game_state.DoubleSizePowerup,
            game_state.IncreaseOccupationPowerup,
            ]

    def __init__(self):
        rule.Rule.__init__(self)
        self._powerup_gen_source = pyglet.resource.media("772__vitriolix__kick_wump.wav",
                streaming = False)
        self._powerup_gen_player = pyglet.media.Player()
#        self._powerup_gen_player.queue(self._powerup_gen_source)
#        self._powerup_gen_player.eos_action = pyglet.media.Player.EOS_PAUSE

    def update(self, dt, state):
        if random.random() > 0.5:
            if len(state.powerups) < self.MAX_POWERUPS:
                if state.facets:
                    powerup_positions = [ (p.position.x, p.position.y) for p in state.powerups ]
                    facets = [ f for f in state.facets if (f.gen_x, f.gen_y) not in powerup_positions ]
                    min_occupation = min([ sum(f.occupation.values()) for f in facets ])
                    facet = random.choice([ f for f in facets if sum(f.occupation.values()) == min_occupation ])
                    powerup = random.choice(self.powerups)(euclid.Point2(facet.gen_x, facet.gen_y))

                    self.log.debug(u"Placing powerup %s...", powerup)
                    state.powerups.append(powerup)
                    self._powerup_gen_player.queue(self._powerup_gen_source)
                    self._powerup_gen_player.play()

class PowerupCollectionRule(rule.Rule):
    """Checks for blob-powerup interaction"""

    MIN_INTERVAL = 0.5

    OCCUPATION_INCREMENT = 0.1
    MIN_OCCUPATION = 0.0
    MAX_OCCUPATION = 1.0
    DEFAULT_OCCUPATION = 0.0

    def __init__(self):
        rule.Rule.__init__(self)
        self._powerup_col_source = pyglet.resource.media("958__Anton__groter.wav",
                streaming = False)
        self._powerup_col_player = pyglet.media.Player()
#        self._powerup_col_player.queue(self._powerup_col_source)
#        self._powerup_col_player.eos_action = pyglet.media.Player.EOS_PAUSE

    def update(self, dt, state):
        for powerup in state.powerups:
            relevant_blobs = []
            for player in state.players:
                for blob in player.blobs:
                    if powerup.position.distance(blob.position) < blob.radius + powerup.radius:
                        relevant_blobs.append(blob)
            relevant_players = set([ blob.player for blob in relevant_blobs ])
            if len(relevant_blobs) == 1:
                player = relevant_blobs[0].player
                powerup.occupation[player] = current_occupation = clamp(
                        powerup.occupation.get(player, self.DEFAULT_OCCUPATION) +\
                                self.OCCUPATION_INCREMENT,
                        self.MIN_OCCUPATION,
                        self.MAX_OCCUPATION,
                        )
                if current_occupation == self.MAX_OCCUPATION:
                    self.log.debug(u"Applying %s for player %s...", powerup, player)
                    powerup.apply(relevant_blobs[0], state)
                    self._powerup_col_player.queue(self._powerup_col_source)
                    self._powerup_col_player.play()
                    state.powerups.remove(powerup)
            for player in state.players:
                if player not in relevant_players and player in powerup.occupation:
                    del powerup.occupation[player]

