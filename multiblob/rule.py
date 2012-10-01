import logging

class GameRuleSystem(object):
    """A class to encapsulate the game rules."""

    def __init__(self, rules=[], state=None):
        self.rules = rules
        self.state = state

        self.log = logging.getLogger(self.__class__.__name__)

    def update(self, dt):
        """Update the game state.

        Parameters
        ----------
        dt : float
            the time that has passed since the last update
        """
        if self.state:
            for rule in self.rules:
                if rule.should_update(dt, self.state):
                    rule.update(dt, self.state)

    def activate(self):
        """Activate the rules."""
        for rule in self.rules:
            rule.activate()

    def deactivate(self):
        """Deactivate the rules."""
        for rule in self.rules:
            rule.deactivate()

class Rule(object):
    """A class representing a game rule."""
    MIN_INTERVAL = 0.0

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self._time_since = 0.0

    def should_update(self, dt, state):
        """Return True, if the rule's update method should be run given dt and
        state."""
        self._time_since += dt
        if self._time_since >= self.MIN_INTERVAL:
            self._time_since = 0.0
            return True
        else:
            return False

    def update(self, dt, state):
        """Update the global state to conform to the rule. Override this in
        subclasses.

        Parameters
        ----------
        dt : float
            the time that has passed since the last update
        state : GameState
            the global state
        """
        pass

    def activate(self):
        """Activate the rule."""
        pass

    def deactivate(self):
        """Deactivate the rule."""
        pass
