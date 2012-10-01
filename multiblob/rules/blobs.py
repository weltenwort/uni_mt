"""Blob rules go here."""

import lepton
from multiblob import rule, state as game_state

class BlobMovementRule(rule.Rule):
    """Performs the blob movement."""

    MERGE_IMMUNITY_TIME = 100
    
    def update(self, dt, state):
        for player in state.players:
            for blob in player.blobs:
                if blob.movement:
                    current_movement = blob.movement[0]
                    diff = (current_movement - blob.position)
                    movement_step = diff.normalized() * blob.speed
                    
                    # remove movement if complete with this step
                    if abs(movement_step) >= abs(diff):
                        blob.movement.pop(0)
                    
                    blob.position += movement_step
                    if blob.movement_flag == 0:                       
                        blob.movement_flag = 1
                else:
                    blob.movement_flag = 0
                    
                if blob.just_splitted_from:
                    # when the blob gets once out of the blob it came from
                    # it will be mergable with it again
                    dist = blob.position.distance(blob.just_splitted_from.position)
                    blob.just_splitted_time += 1
                    if dist > blob.radius + blob.just_splitted_from.radius or\
                            blob.just_splitted_time > self.MERGE_IMMUNITY_TIME:
                        blob.just_splitted_from = None
                        blob.just_splitted_time = 0
        
        lepton.default_system.update(dt)

class BlobGenerationRule(rule.Rule):
    """Generates new blobs on certain facets."""

    MIN_INTERVAL = 1.0
    MAX_BLOB_SIZE = 200.0

    def update(self, dt, state):
        for facet in state.facets:
            if facet.blob_generation != 0.0:
                if facet.owner:
                    present_blob_sizes = [
                            blob.size
                            for blob in facet.owner.blobs
                            if state.facet_tree.get_nearest(blob.pos_x, blob.pos_y) is facet
                            ]

                    blob_gen_size =  facet.blob_generation +\
                            self._blob_gen_bonus_by_owned_facets(state, facet)

                    if not present_blob_sizes or sum(present_blob_sizes) < self.MAX_BLOB_SIZE:
                        if hasattr(facet, 'gen_x') and hasattr(facet, 'gen_y'):
                            game_state.Blob(
                                    facet.owner, 
                                    facet.gen_x,
                                    facet.gen_y,
                                    blob_gen_size,
                                    )
                        else:
                            game_state.Blob(
                                    facet.owner, 
                                    facet.pos_x,
                                    facet.pos_y,
                                    blob_gen_size,
                                    )

    def _blob_gen_bonus_by_owned_facets(self, state, home_facet):
        bonus_size = 0.0
        for facet in state.facets:
            if facet.owner is home_facet.owner and not facet is home_facet:
                distance = facet.position.distance(home_facet.position)
                bonus_size += 0.005 * distance * facet.occupation[facet.owner]
        return bonus_size
