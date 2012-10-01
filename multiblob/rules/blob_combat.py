"""Blob combat go here."""
import pyglet

from multiblob import rule
 
class BlobCombat(rule.Rule):
    """Performs the blob combat."""  
    MIN_INTERVAL = 0.2

    REDUCE_FACTOR = 0.4
    KILL_THRESHOLD = 5.0

    def __init__(self):
        rule.Rule.__init__(self)
        self._combat_source = pyglet.resource.media('blub3.wav', streaming=False)
        self._combat_player = pyglet.media.Player()
        self._combat_player.queue(self._combat_source)
        self._combat_player.eos_action = pyglet.media.Player.EOS_LOOP
   
    def update(self, dt, state):
        is_combat = False

        for player in state.players:
            for other_player  in state.players:
                for blob in player.blobs:
                    for other_blob in other_player.blobs:
                        if blob != other_blob and blob.size > 0 and other_blob.size > 0:
                            distance_between_blobs = blob.position.distance(other_blob.position)
                            if player != other_player:
                                # combat
                                #########################################
                                #check the collision and reduce the size#
                                #########################################
                                
                                if blob.size > 0 and other_blob.size > 0:
                                    # difference between blobs
                                    dif_size = abs(blob.size - other_blob.size)
                                    if distance_between_blobs <= blob.radius + other_blob.radius:
                                        
                                        # reduce the size of blobs which crash others
                                        blob.size = blob.size - self.REDUCE_FACTOR * (2 + self.REDUCE_FACTOR * dif_size/blob.size)
                                        other_blob.size = other_blob.size - self.REDUCE_FACTOR * (2 + self.REDUCE_FACTOR * dif_size/other_blob.size)
                                        is_combat = True;
                     
                            else:
                                # merging
                                if (blob.just_splitted_from != other_blob and
                                        other_blob.just_splitted_from != blob and
                                        distance_between_blobs <= blob.radius + other_blob.radius):
                                    if blob.size >= other_blob.size:
                                        blob.size += other_blob.size
                                        other_blob.size = 0
                                    else:
                                        other_blob.size += blob.size
                                        blob.size = 0

                        if blob.size < self.KILL_THRESHOLD:
                            blob.size = 0
                            try:
                                blob.player.blobs.remove(blob)
                            except ValueError:
                                pass
                        if other_blob.size < self.KILL_THRESHOLD:
                            other_blob.size = 0
                            try:
                                other_blob.player.blobs.remove(other_blob)
                            except ValueError:
                                pass
        
        if is_combat:
            self._combat_player.play()
        else:
            self._combat_player.pause()
