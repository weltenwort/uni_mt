from multiblob import mode, renderers, rules

class MainMode(mode.Mode):
    def __init__(self, application):
        mode.Mode.__init__(self, 
                state = application.state,
                renderers = [
                    renderers.FacetRenderer(),
                    renderers.BlobsRenderer(),
                    renderers.DebugRenderer(),
                    renderers.PowerupRenderer(),
                    ],
                rules = [
                    rules.InputInterpreterRule(application.input_system),
                    rules.BlobMovementRule(),
                    rules.BlobGenerationRule(),
                    rules.BlobCombat(),
                    rules.FacetOwnershipRule(),
                    rules.LastBlobStandingVictoyRule(application),
                    rules.PowerupCollectionRule(),
                    rules.PowerupGenerationRule(),
                    ]
                )

        self.application = application

