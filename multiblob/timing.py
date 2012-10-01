class TTLMixin(object):
    DEFAULT_TTL = 3.0

    def __init__(self):
        self.reset_ttl()

    def decrease_ttl(self, amount=1.0):
        self.ttl -= amount

    def reset_ttl(self, amount=None):
        if amount is None:
            amount = self.DEFAULT_TTL
        self.ttl = amount

    def should_die(self):
        return self.ttl <= 0.0
