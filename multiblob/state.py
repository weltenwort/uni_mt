from multiblob import euclid
import math
import random
import logging

def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)

PLAYER_COLOURS = [
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 1.0),
        (0.0, 0.0, 1.0, 1.0),
        (1.0, 1.0, 0.0, 1.0),
        (0.0, 1.0, 1.0, 1.0),
        (1.0, 0.0, 1.0, 1.0),
        ]

class OldGlobalState(object):
    def __init__(self, game_state=None, application_state=None):
        self.game        = game_state or GameState()
        self.application = application_state or ApplicationState()
        self.facet_grid_size = (4, 3)

    def reset_simple(self):
        self.application.reset()
        self.game.reset_simple(
                self.application.window_width, 
                self.application.window_height
                )

class OldApplicationState(object):
    def __init__(self, window_width=1024, window_height=768):
        self.window_width  = window_width
        self.window_height = window_height

    def reset(self):
        pass

class GameState(object):
    """Basic game state class."""

    def __init__(self, players=[], window_width=1024, window_height=768):
        self.players       = players
        self.window_width  = window_width
        self.window_height = window_height
        self.facets        = []
        self.hotspots      = []
        self.powerups      = []
        self.debug_objects = {}

        self.facet_grid_size = (64, 48)
        self.border_ratio    = 0.0 #1.0/60.0

        self.colours_free = PLAYER_COLOURS[:]

        self.log = logging.getLogger("multiblob.game_state")

    def reset_simple(self):
        self.colours_free = PLAYER_COLOURS[:]
        self.players = []
        self.facets = []
        self.debug_objects = {}
        self.generate_facets()

    def players_free(self):
        return len(self.colours_free)

    def add_player(self, facet):
        player = Player(
                #PLAYER_COLOURS[self.colour_counter % len(PLAYER_COLOURS)],
            self.colours_free.pop(0),
            []
            )
        self.players.append(player)
        facet.occupation[player] = 1.0
        facet.home_facet_of = player

    def remove_player(self, player):
        self.players.remove(player)
        self.colours_free.append(player.colour)
        for facet in self.facets:
            if player in facet.occupation:
                del facet.occupation[player]
            if facet.home_facet_of is player:
                facet.home_facet_of = None

    def generate_facets_2(self, facet_count):
        sites = [ euclid.Point2(
            random.randint(0, self.window_width),
            random.randint(0, self.window_height)
            ) for i in range(facet_count) ]

        self.log.debug(u"Using sites %s to generate board...", str(sites))

        context = voronoi.MultiblobContext()
        voronoi.voronoi(voronoi.SiteList(sites), context)

        self.log.debug(u"Voronoi vertices: %s", str(context.vertices))
        #self.log.debug(u"Voronoi lines: %s", str(lines))
        self.log.debug(u"Voronoi edges: %s", str(context.edges))

    def generate_facets(self):
        """ generates some random facets """
        random.seed()
        FACET_COUNT_X = 6
        FACET_COUNT_Y = 4
        facet_width = float(self.window_width/FACET_COUNT_X)
        facet_height = float(self.window_height/FACET_COUNT_Y)
        facet_coords = []
        for x in range(FACET_COUNT_X):
            for y in range(FACET_COUNT_Y):
                facet_coords.append((
                    x * facet_width + facet_width*0.5*random.uniform(0.7, 1.3),
                    y * facet_height + facet_height*0.5*random.uniform(0.7, 1.3)
                    ))

        random.shuffle(facet_coords)
        self.log.debug(u"Inserting facets at: %s", facet_coords)
        self.facet_tree = None
        for x, y in facet_coords:
            self.put_one_facet_in_facet_tree_at(x, y)

        # create the facets in facet tree
        #self.facet_tree = None
        #num_facets = 0
        #while num_facets < 16:
        #    if self.put_one_facet_in_facet_tree():
        #        num_facets +=1

        # put facets from tree in list
        self.facets = self.facet_tree.get_facets()
        self.check_border_facets()
        self.calculate_generation_coords()

    def put_one_facet_in_facet_tree(self):
        x = random.randint(0, self.window_width)
        y = random.randint(0, self.window_height)
        if self.facet_tree == None:
            # create root element
            self.facet_tree = FacetTreeElem(x, y)
            self.facet_tree.coords = [
                    0, 0,
                    self.window_width, 0,
                    self.window_width, self.window_height,
                    0, self.window_height]
            return self.facet_tree
        else:
            return self.facet_tree.insert_facet(x, y)

    def put_one_facet_in_facet_tree_at(self, x, y):
        if self.facet_tree == None:
            # create root element
            self.facet_tree = FacetTreeElem(x, y)
            self.facet_tree.coords = [
                    0, 0,
                    self.window_width, 0,
                    self.window_width, self.window_height,
                    0, self.window_height]
            return self.facet_tree
        else:
            return self.facet_tree.insert_facet(x, y)

    def check_border_facets(self):
        for f in self.facets:
            for (x,y) in zip(f.coords[::2], f.coords[1::2]):
                if x == 0 or x == self.window_width or\
                        y == 0 or y == self.window_height:
                    f.is_border_facet = True

    def calculate_generation_coords(self):
        for f in self.facets:
            f.gen_x = float(sum(f.coords[::2])) / float(len(f.coords)/2)
            f.gen_y = float(sum(f.coords[1::2])) / float(len(f.coords)/2)

    @property
    def facet_map(self):
        if not hasattr(self, '_facet_map'):
            border_width = self.border_ratio * self.window_width
            _facet_map = {}
            _facet_grid = []
            grid_coords = self._facet_grid_coords
            for index, coords in enumerate(zip(grid_coords[::2], grid_coords[1::2])):
                pos = euclid.Point2(coords[0], coords[1])
                #closest_facet = min(self.facets, key=lambda f: f.position.distance(pos))
                facets_by_distance = sorted(self.facets, key=lambda f: f.position.distance(pos))
                if len(facets_by_distance) > 1:
                    closest_facet = facets_by_distance[0]
                    closest_facet_2 = facets_by_distance[1]
                    if abs(pos.distance(closest_facet.position) - pos.distance(closest_facet_2.position)) < border_width:
                        closest_facet.border_indices.add(index)
                        closest_facet_2.border_indices.add(index)
                else:
                    closest_facet = facets_by_distance[0]
                _facet_map.setdefault(closest_facet, []).append((index, pos))
                _facet_grid.append(closest_facet)
            self._facet_map = _facet_map
            self._facet_grid = _facet_grid
        return self._facet_map

    @property
    def facet_grid(self):
        if not hasattr(self, '_facet_grid'):
            self.facet_map # this should generate the facet grid as well
        return self._facet_grid

    @property
    def facet_grid_coords(self):
        if not hasattr(self, '_facet_grid_coords'):
            coords = []
            max_x = self.facet_grid_size[0]
            max_y = self.facet_grid_size[1]
            for y in range(max_y):
                for x in range(max_x):
                    pos_x = float(x) / float(max_x-1) * self.window_width
                    pos_y = float(y) / float(max_y-1) * self.window_height
                    coords.append(pos_x)
                    coords.append(pos_y)
            self._facet_grid_coords = coords
        return self._facet_grid_coords

    @property
    def facet_grid_indices(self):
        if not hasattr(self, '_facet_grid_indices'):
            indices = []
            max_x = self.facet_grid_size[0]
            max_y = self.facet_grid_size[1]
            for y in range(max_y-1):
                for x in range(max_x-1):
                    indices.append( x    +  y*max_x)
                    indices.append((x+1) +  y*max_x)
                    indices.append((x+1) + (y+1)*max_x)
                    indices.append( x    + (y+1)*max_x)
            self._facet_grid_indices = indices
        return self._facet_grid_indices

class Facet(object):
    """Basic facet on the gaming board."""

    BASE_COLOUR = (0.1, 0.1, 0.1, 1.0)

    MIN_OCCUPATION = 0.0
    MAX_OCCUPATION = 1.0
    DEFAULT_OCCUPATION = 0.0

    def __init__(self, pos_x, pos_y, occupation=None):
        """Create a new facet.

        Paramters
        ---------
        pos_x : float
            the x coordinate of the facet center
        pos_y : float
            the y coordinate of the facet center
        occupation : dict of player -> [0..1] (optional, defaults to None)
            the initial occupation
        """
        self.pos_x      = pos_x
        self.pos_y      = pos_y
        self.occupation = occupation or {} # mapping of player -> [0..1]
        self.coords     = [] # coordinates of facet polygon
        self.border_indices = set()
        self.is_border_facet = False
        self.home_facet_of = None

    def set_occupation(self, player, value):
        self.occupation[player] = clamp(
                value,
                self.MIN_OCCUPATION,
                self.MAX_OCCUPATION,
                )
    
    def add_occupation(self, player, value):
        self.occupation[player] = clamp(
                self.occupation.get(player, self.DEFAULT_OCCUPATION) + \
                        value,
                self.MIN_OCCUPATION,
                self.MAX_OCCUPATION,
                )

    def has_coord(self, x, y):
        return (x, y) in zip(
                self.coords[::2],
                self.coords[1::2]
                )

    @property
    def position(self):
        return euclid.Point2(self.pos_x, self.pos_y)

    @position.setter
    def position(self, value):
        self.pos_x = value.x
        self.pos_y = value.y

    @property
    def owner(self):
        if self.occupation:
            return max(self.occupation.items(), key=lambda i: i[1])[0]
        return None

    def get_colour(self, for_index=None):
        owner = self.owner
        if owner:
            occupation_factor = float(self.occupation[owner]) * 0.8
            if for_index and for_index in self.border_indices:
                occupation_factor *= 0.0
            return tuple( 
                    base_colour_comp * (1-occupation_factor) + \
                            owner_colour_comp * occupation_factor
                    for base_colour_comp, owner_colour_comp
                    in zip(self.BASE_COLOUR, owner.colour) )
        else:
            return self.BASE_COLOUR

    @property
    def colour(self):
        return self.get_colour()

    @property
    def blob_generation(self):
        if self.home_facet_of and self.home_facet_of is self.owner:
            return 5.0
        else:
            return 0.0

    @property
    def area(self):
        area = 0.0
        last_x = self.coords[-2]
        last_y = self.coords[-1]
        for (cur_x, cur_y) in zip(self.coords[::2], self.coords[1::2]):
            area += (last_x - cur_x) * (last_y + cur_y) / 2
            last_x = cur_x
            last_y = cur_y
        return area

    @property
    def bounding_box(self):
        """ the axis parallel bounding box of the facet """
        minX = float("infinity")
        maxX = float("-infinity")
        for x in self.coords[::2]:
            if (x < minX):
                minX = x
            if (x > maxX):
                maxX = x
        minY = float("infinity")
        maxY = float("-infinity")
        for y in self.coords[1::2]:
            if (y < minY):
                minY = y
            if (y > maxY):
                maxY = y
        return (euclid.Point2(minX, minY), euclid.Point2(maxX, maxY))

    @property
    def proportion1(self):
        """ proportion of the bounding box of the facet
        (between 0 and infitity) (1 means square) """
        bb = self.bounding_box
        lenX = bb[1].x - bb[0].x
        lenY = bb[1].y - bb[0].y
        return lenX / lenY

    @property
    def proportion2(self):
        """ proportion of bounding box area to facet area (between 0 and 1)
        (1 means facet=bb; 0 means facet is a diagional 'line' in bb) """
        bb = self.bounding_box
        bba = (bb[1].x - bb[0].x) * (bb[1].y - bb[0].y)
        return self.area / bba        

class FacetTreeElem(Facet):
    def __init__(self, pos_x, pos_y):
        Facet.__init__(self, pos_x, pos_y)
        self.left = None
        self.right = None

    def get_nearest(self, x, y):
        if self.left == None and self.right == None:
            return self
        else:
            pos = euclid.Point2(x, y)
            dist_left = pos.distance(self.left.position)
            dist_right = pos.distance(self.right.position)
            if dist_left < dist_right:
                return self.left.get_nearest(x, y)
            else:
                return self.right.get_nearest(x, y)

    def insert_facet(self, new_x, new_y):
        """ Tries to create a new facet in the tree at position (pos_x, pos_y)
        and returns it. No new facet will be created, if the existing facet
        which would be split, is too small. In this case None is returned. """
        return self.get_nearest(new_x, new_y)._split_node(new_x, new_y)

    def _split_node(self, new_x, new_y):
        # create new child facets
        self.left = FacetTreeElem(self.pos_x, self.pos_y)
        self.right = FacetTreeElem(new_x, new_y)

        # calculate middle line
        l_point = self.left.position
        r_point = self.right.position
        con_dir_vec = r_point - l_point
        m_point = l_point + 0.5 * con_dir_vec
        m_dir_vec = con_dir_vec.cross()
        bisector = euclid.Line2(m_point, m_point + m_dir_vec)

        # calculate intersections and update polygon coordinates
        #print("Splitting %s into %s with new coords %s" % (self, self.right, self.coords))
        for cur_x, cur_y, prev_x, prev_y in zip(
                self.coords[::2], 
                self.coords[1::2],
                self.coords[-2:-1] + self.coords[:-2:2],
                self.coords[-1:]   + self.coords[1:-1:2],
                ):
            #print("cur_x: %s, cur_y: %s, prev_x: %s, prev_y: %s" % (cur_x, cur_y, prev_x, prev_y))
            current_edge = euclid.LineSegment2(
                    euclid.Point2(prev_x, prev_y), 
                    euclid.Point2(cur_x, cur_y),
                    )
            intersection = bisector.intersect(current_edge)
            if intersection:
                # intersection -> add intersection point to both facet polygons
                if not self.left.has_coord(*list(intersection)):
                    #print("left: adding %s to %s" % (intersection, self.left.coords))
                    self.left.coords.extend(list(intersection))
                if not self.right.has_coord(*list(intersection)):
                    #print("right: adding %s to %s" % (intersection, self.right.coords))
                    self.right.coords.extend(list(intersection))

            # put current point in facet which is nearer
            nearest_facet = self.get_nearest(cur_x, cur_y)
            if not nearest_facet.has_coord(cur_x, cur_y):
                #print("(%s, %s) not in %s" % (cur_x, cur_y, nearest_facet.coords))
                nearest_facet.coords.extend([cur_x, cur_y])
            #else:
                #print("(%s, %s) in %s" % (cur_x, cur_y, nearest_facet.coords))

        self.left.occupation = self.occupation
        self.occupation = None
        # check new facets
        #if self.left._is_good_facet() and self.right._is_good_facet():
            #self.left.occupation = self.occupation
            #self.occupation = None
        #else:
            ## undo the new facets
            #self.left = None
            #self.right = None

        # return the facet generated from new point or None when no good facets
        return self.right

    def _is_good_facet(self):
        #        # facets should have a minimum area
        #        if (self.area < 34000):
        #            return False
        #        # facet should have good proportions
        #        if (self.proportion1 < 0.5 or self.proportion1 > 2):
        #            return False
        #        if (self.proportion2 < 0.4):
        #            return False
        return True


    def get_facets(self):
        """ traverses the tree and returns all contained facets """
        if self.left == None and self.right == None:
            return [self]
        else:
            facets = self.left.get_facets()
            facets.extend(self.right.get_facets())
            return facets

class BorderFacet(Facet):
    @property
    def colour(self):
        return (1.0, 1.0, 1.0, 1.0)

class Player(object):
    """Basic player object."""

    def __init__(self, colour, blobs):
        """Create a new player.
        
        Parameters
        ----------
        colour : colour tuple
            the color of the player
        blobs : list of Blob instances
            the player's initial blobs
        """
        self.colour = colour
        self.blobs = blobs
        self.score = 0

    @property
    def overall_size(self):
        return sum([ blob.size for blob in self.blobs ])

class Blob(object):
    """Basic blob of colour."""

    def __init__(self, player, pos_x, pos_y, size):
        """Create a new blob.

        Parameters
        ----------
        player : Player instance
            the player that owns the blob
        pos_x : float
            the x coordinate of the "center" of the blob
        pos_y : float
            the y coordinate of the "center" of the blob
        size : float
            the size (=strength) of the blob
        """
        self.player = player
        self.pos_x = float(pos_x)
        self.pos_y = float(pos_y)
        self.size = size
        self.movement = [] # list of coordinates
        self.movement_flag = 0
        self.speed = 3.0
        
        self.combat_index = [] # 

        # when the blob was just splitted it should not get merged instantly
        # so remember the blob it came from for some time
        self.just_splitted_from = None
        self.just_splitted_time = 0

        if not self in player.blobs:
            player.blobs.append(self)

    @property
    def position(self):
        return euclid.Point2(float(self.pos_x), float(self.pos_y))

    @position.setter
    def position(self, value):
        self.pos_x = float(value.x)
        self.pos_y = float(value.y)

    @property
    def radius(self):
        return math.sqrt(float(self.size)) * 5

    @property
    def circle(self):
        return euclid.Circle(self.position, self.radius)

class Powerup(object):
    """Generic powerup class"""

    BASE_COLOUR = (1.0, 1.0, 1.0, 1.0)

    label = ""
    label_font_size = 24.0

    def __init__(self, position):
        """Initialize a new powerup.

        Parameters
        ----------
        position : Point2
            the center position of the powerup
        """
        self.position   = position
        self.occupation = {}
        self.radius     = 30

    def apply(self, blob, state):
        """Apply the powerup. Override this in subclasses.
        
        Parameters
        ----------
        blob : Blob
            the blob, that collected the powerup
        state : GameState
            the current game state
        """
        pass

    def __str__(self):
        return "%s(position=%s)" % (self.__class__.__name__, self.position)

    @property
    def owner(self):
        if self.occupation:
            return max(self.occupation.items(), key=lambda i: i[1])[0]
        return None

    def get_colour(self, for_index=None):
        owner = self.owner
        if owner:
            occupation_factor = float(self.occupation[owner])
            if for_index and for_index in self.border_indices:
                occupation_factor *= 0.0
            return tuple( 
                    base_colour_comp * (1-occupation_factor) + \
                            owner_colour_comp * occupation_factor
                    for base_colour_comp, owner_colour_comp
                    in zip(self.BASE_COLOUR, owner.colour) )
        else:
            return self.BASE_COLOUR

    @property
    def colour(self):
        return self.get_colour()

class DoubleSizePowerup(Powerup):
    """A powerup, that doubles the size of the blob collecting it."""

    label = "x2"

    def apply(self, blob, state):
        blob.size *= 2.0

class IncreaseOccupationPowerup(Powerup):
    """A powerup, that slightly adds to the occupation of a player on all facets."""

    label_font_size = 16.0

    def __init__(self, position, factor=0.1):
        Powerup.__init__(self, position)
        self.factor = factor

    def apply(self, blob, state):
        for facet in state.facets:
            if facet.owner is blob.player:
                facet.add_occupation(blob.player, self.factor)

    @property
    def label(self):
        return "+%d%%" % (self.factor*100)
