import math
import random
import weakref

import lepton
import lepton.controller
import lepton.domain
import lepton.emitter
import lepton.renderer
import lepton.texturizer
import lepton.particle_struct
import pyglet
from pyglet import gl

from multiblob import renderer

class BlobMagnetDomain(lepton.domain.Point):
    def __init__(self, blob):
        self.blob = blob

    @property
    def point(self):
        return lepton.particle_struct.Vec3(self.blob.pos_x, self.blob.pos_y, 0.0)

class BlobTrackerController(object):
    def __init__(self, blob):
        self.blob = blob

    def __call__(self, dt, group):
        # set velocity
        dev = self.blob.radius*2
        for particle in group:
            diff = lepton.particle_struct.Vec3(self.blob.pos_x + random.uniform(-dev, dev), self.blob.pos_y + random.uniform(-dev, dev), 0.0) - particle.position
            particle.velocity = lepton.particle_struct.Vec3(*particle.velocity) * 0.9 + diff * 0.1 #.normalize() * 20
            particle.size = (
                    self.blob.radius * BlobsRenderer.PARTICLE_SIZE_FACTOR, 
                    self.blob.radius * BlobsRenderer.PARTICLE_SIZE_FACTOR, 
                    0
                    )

        # set particle number
        BlobsRenderer._adjust_particle_count(self.blob, group)

class BlobsRenderer(renderer.Renderer):
    """Renders blobs."""

    UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
            for a in range(0, 360, 10)]
    PARTICLE_RATIO = 1.0/10.0
    PARTICLE_SIZE_FACTOR = 4.5/3.0

    def __init__(self):
        renderer.Renderer.__init__(self)
        self._blob_batch = renderer.ManagedBatch()
        self._blob_groups = {}
        self._blob_texture = pyglet.resource.texture('blob_1.png')

    @staticmethod
    def _random_velocity_controller(dt, group):
        for particle in group:
            particle.velocity.x += random.uniform(-50, 50)
            particle.velocity.y += random.uniform(-50, 50)

    @classmethod
    def _circle(cls, center, radius):
        result = []
        for x, y in cls.UNIT_CIRCLE:
            result.append(center[0] + x*radius)
            result.append(center[1] + y*radius)
        return result

    @classmethod
    def _adjust_particle_count(cls, blob, group):
        size_difference = int(blob.radius * cls.PARTICLE_RATIO) - len(group)
        if size_difference > 0:
            emitter = lepton.emitter.StaticEmitter(
                    template = lepton.Particle(
                        position = (
                            blob.pos_x,
                            blob.pos_y,
                            0,
                            ),
                        size = (blob.size, blob.size, 0),
                        color = blob.player.colour
                        ),
                    #deviation = lepton.Particle(
                        #position = (blob.size/5, blob.size/5, 0),
                        #size = (32, 32, 0),
                        #),
                    )
            emitter.emit(size_difference, group)
        elif size_difference < 0:
            for particle in list(group)[-size_difference:]:
                group.kill(particle)

    def render(self, game_state):
        blobs = [ blob for player in game_state.players for blob in player.blobs ]
        deleted_blobs = self._blob_batch.clear(keep_keys=blobs)
        for blob in deleted_blobs:
            lepton.default_system.remove_group(self._blob_groups[blob])
            del self._blob_groups[blob]

        for blob in blobs:
            if blob in self._blob_batch:
                group = self._blob_groups[blob]
                vertex_list = self._blob_batch.get(blob)
            else:
                group = self._blob_groups[blob] = lepton.ParticleGroup(
                        controllers = [
                            #lepton.controller.Magnet(BlobMagnetDomain(blob), 30, 1, 1),
                            BlobTrackerController(blob),
                            #self._random_velocity_controller,
                            lepton.controller.Movement(),
                            ],
                        renderer = lepton.renderer.BillboardRenderer(
                            lepton.texturizer.SpriteTexturizer(
                                self._blob_texture.id
                                #lepton.texturizer.create_point_texture(64, 0.2)
                                )
                            ),
                        )

                self._adjust_particle_count(blob, group)
                
                vertex_list = self._blob_batch.set(
                        blob,
                        36,
                        gl.GL_LINE_LOOP,
                        pyglet.graphics.Group(),
                        ('v2f', (0.0, )*72)
                        )

                #vertex_list.vertices = self._circle((blob.pos_x, blob.pos_y), blob.radius)
                
        lepton.default_system.draw()
        self._blob_batch.draw()

