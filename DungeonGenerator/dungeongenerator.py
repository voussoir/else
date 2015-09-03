import time
import random

class Room:
    def __init__(self):
        self.entrances = []

    def __eq__(self, other):
        return self.bbox == other.bbox

    @property
    def bbox(self):
        return (self.ulx, self.uly, self.lrx, self.lry)

    def create_entrance(self, direction):
        if direction == 'north':
            x = random.randint(self.ulx, self.lrx)
            y = self.uly - 1
        elif direction == 'south':
            x = random.randint(self.ulx, self.lrx)
            y = self.lry + 1
        elif direction == 'west':
            x = self.ulx - 1
            y = random.randint(self.uly, self.lry)
        else:
            x = self.lrx + 1
            y = random.randint(self.uly, self.lry)

        e = {'direction': direction, 'x': x, 'y': y, 'nearest': None, 'painted': False, 'owner':self}
        self.entrances.append(e)

    def contains(self, x, y, padding=0):
        return (self.ulx-padding <= x <= self.lrx+padding) and (self.uly-padding <= y <= self.lry+padding)

    def does_collide(self, bbox, padding=0):
        '''
        Check whether this Room's bounding box collides with another.
        If padding is provided, rooms will be considered collided if
        they are this close to each other, even if not touching.

        bbbox may be another Room object, or a tuple of the form
        (ulx, uly, lrx, lry)
        '''
        if isinstance(bbox, Room):
            bbox = ulx.bbox

        ulx = bbox[0] - padding
        uly = bbox[1] - padding
        lrx = bbox[2] + padding
        lry = bbox[3] + padding

        return not (ulx > self.lrx or
                    lrx < self.ulx or
                    uly > self.lry or
                    lry < self.uly)


def choose_room_size(minw, maxw, minh, maxh, msquareness):
    if msquareness == 0:
        w = random.randint(minw, maxw)
        h = random.randint(minh, maxh)

    osquareness = 1 + (1-msquareness)

    if random.getrandbits(1):
        # In order to keep the rooms from being stupdly narrow,
        # we decide one dimension freely and then the other one based
        # on the minimum squareness and the first dimension
        # This chooses whether W or H should be the free dimension.
        w = random.randint(minw, maxw)
        h = random.randint(max(minh, int(w * msquareness)), min(maxh, int(w * osquareness)))
    else:
        h = random.randint(minh, maxh)
        w = random.randint(max(minw, int(h * msquareness)), min(maxw, int(h * osquareness)))
    #print('dim', w,h)
    return (w, h)

def push_into_world_bounds(ulx, uly, lrx, lry, worldw, worldh):
    if (lry - uly) > (worldh-2) or (lrx - ulx) > (worldw-2):
        raise ValueError('Cannot fit on world!')
    if ulx < 1:
        #print('Push right')
        diff = 1 - ulx
        ulx += diff
        lrx += diff
    if uly < 1:
        #print('Push down')
        diff = 1 - uly
        uly += diff
        lry += diff
    if lrx > (worldw-2):
        #print('Push left')
        diff = lrx - (worldw-2)
        ulx -= diff
        lrx -= diff
    if lry > (worldh-2):
        #print('Stick em\' up')
        diff = lry - (worldh-2)
        uly -= diff
        lry -= diff

    return (ulx, uly, lrx, lry)

def distance(x1, x2, y1, y2):
    d = (x1 - x2) ** 2
    d += (y1 - y2) ** 2
    return d ** 0.5

def paint(world, character, x, y):
    world[y][x] = character

def generate_dungeon(
             world_width=128,
             world_height=64,
             min_room_width=12,
             min_room_height=12,
             max_room_width=30,
             max_room_height=30,
             min_room_squareness=0.5,
             min_room_count=12,
             max_room_count=25,
             character_wall='#',
             character_floor=' ',
             character_spawnpoint=None,
             character_exitpoint=None,
             include_metadata=False,
             room_replace_attempts=6,
             force_random_seed=None,
             ):
    '''
    Returns a list of lists of characters.
    Each primary list represents a row of the map, and each
    entry character in that list represents the tile at that column.

    : PARAMETERS :
              world_width = the width of the map in characters.
             world_height = the height of the map in characters.
           min_room_width = the mininumum horizontal width of any room in characters.
           max_room_width = the maximum horizontal width of any room in characters.
          min_room_height = the mininumum vertical height of any room in characters.
          max_room_height = the maximum vertical height of any room in characters.
      min_room_squareness = a number between 0 and 1. this helps prevent any
                            rooms from becoming stupidly narrow. a value of 1
                            means that every room must be perfectly square.
                            A value of 0 means the walls behave independently.
                            0.5 means that a room can be at most 2x1. etc.
           min_room_count = the minimum number of rooms. This may not
                            necessarily be met if the world is so tightly packed
                            that the function repeatedly fails to place rooms.
                            *see room_replace_attemps*.
           max_room_count = the maximum number of rooms.
           character_wall = the character to represent unwalkable space
          character_floor = the character to represent walkable space
     character_spawnpoint = if not None, the character to represent a suggested
                            spawnpoint into the level
      character_exitpoint = if not None, the character to represent a suggested
                            exitpoint from the level. It might end up in the
                            same room as the spawnpoint
         include_metadata = append an additional string to the end of the world
                            list containing some additional information about
                            the world you have generated.
    room_replace_attempts = if the world is tightly packed and the function is
                            having trouble placing a room, how many times should
                            it reroll. Higher numbers means more loops
        force_random_seed = if not None, set the random seed manually. Good for
                            testing and demonstration.
    '''
    # originally, I had something more like:
    # world = [[wall] * width] * height
    # but apparently this does not create unique list objects
    # and tile assignment was happening to all lines at once.
    if force_random_seed:
        random.seed(force_random_seed)
    world = [[character_wall for x in range(world_width)] for y in range(world_height)]

    rooms = []
    room_count = random.randint(min_room_count, max_room_count) 
    for roomnumber in range(room_count):
        room = Room()
        for attempt in range(room_replace_attempts):
            ulx = random.randint(1, world_width-1)
            uly = random.randint(1, world_height-1)
            dimensions = choose_room_size(min_room_width, max_room_width, min_room_height, max_room_height, min_room_squareness)
            lrx = ulx + dimensions[0]
            lry = uly + dimensions[1]

            ulx, uly, lrx, lry = push_into_world_bounds(ulx, uly, lrx, lry, world_width, world_height)
            collided = False
            for otherroom in rooms:
                if otherroom.does_collide((ulx, uly, lrx, lry), padding=4):
                    collided = True
                    break
            if not collided:
                # Now we can finalize coordinates
                room.ulx = ulx
                room.uly = uly
                room.lrx = lrx
                room.lry = lry
                rooms.append(room)
                break

    for room in rooms:
        # Paint the floors
        for x in range(room.ulx, room.lrx+1):
            for y in range(room.uly, room.lry+1):
                world[y][x] = character_floor

        if len(room.entrances) > 0:
            break

        north, south, east, west = (True, True, True, True)
        for otherroom in rooms:
            if otherroom.bbox == room.bbox:
                continue
            if north and room.ulx > 2 and otherroom.lry < room.uly:
                room.create_entrance('north')
                north = False
            elif south and room.lry < (world_height -2) and otherroom.uly > room.lry:
                room.create_entrance('south')
                south = False
            elif east and room.lry < (world_width - 2) and otherroom.lrx > (room.lrx+5):
                room.create_entrance('east')
                east = False
            elif west and room.ulx > 2 and otherroom.ulx < (room.ulx-5):
                room.create_entrance('west')
                west = False

    entrances = [room.entrances for room in rooms]
    entrances = [entrance for sublist in entrances for entrance in sublist]
    
    # Match nearest entrances
    for entrance in entrances:

        nearest = None
        x = entrance['x']
        y = entrance['y']
        for otherentrance in entrances:
            if entrance['direction'] == otherentrance['direction']:
                continue
            # Compare the x and y coordinates, not the dicts directly
            # because the dicts are interlinked and cause recur depth
            if x == otherentrance['x'] and y == otherentrance['y']:
                continue
            if entrance['owner'] == otherentrance['owner']:
                continue

            # Let's try to prevent any stupid connections.
            if entrance['direction'] == 'north' and otherentrance['y'] > entrance['y']:
                continue
            if entrance['direction'] == 'south' and otherentrance['y'] < entrance['y']:
                continue
            if entrance['direction'] == 'west' and otherentrance['x'] > entrance['x']:
                continue
            if entrance['direction'] == 'east' and otherentrance['x'] < entrance['x']:
                continue
            if otherentrance['direction'] == 'north' and otherentrance['y'] < entrance['y']:
                continue
            if otherentrance['direction'] == 'south' and otherentrance['y'] > entrance['y']:
                continue
            if otherentrance['direction'] == 'west' and otherentrance['x'] < entrance['x']:
                continue
            if otherentrance['direction'] == 'east' and otherentrance['x'] > entrance['x']:
                continue

            ox = otherentrance['x']
            oy = otherentrance['y']
            distanceto = distance(x, ox, y, oy)
            if nearest is None or distanceto < nearest:
                nearest = distanceto
                # Can assign both at once because they are each other's closest.
                entrance['nearest'] = otherentrance

    # Paint the tunnels
    for entrance in entrances:
        if entrance['painted'] is True:
            continue

        nearest = entrance['nearest']
        if nearest is None:
            # This happens when there wasn't a suitable nearby entrance
            continue
        direction = entrance['direction']
        odirection = nearest['direction']
        if {direction, odirection} == {'north', 'south'}:
            major = 'y'
            minor = 'x'
        elif {direction, odirection} == {'east', 'west'}:
            major = 'x'
            minor = 'y'
        else:
            # 90 degree bends require their own handling.
            boostsx = {'west':-1, 'east':1}
            boostsy = {'north':-1, 'south':1}
            x = entrance['x'] + boostsx.get(direction, 0)
            y = entrance['y'] + boostsy.get(direction, 0)
            ox = nearest['x'] + boostsx.get(odirection, 0)
            oy = nearest['y'] + boostsy.get(odirection, 0)

            paint(world, character_floor, entrance['x'], entrance['y'])
            paint(world, character_floor, nearest['x'], nearest['y'])
            #paint(world, character_floor, x, y)
            #paint(world, character_floor, ox, oy)
            corner = (ox, y)
            if entrance['owner'].contains(*corner, padding=1) or nearest['owner'].contains(*corner, padding=1):
                corner = (x, oy)

            for xx in range(min(ox, x), max(ox, x)+1):
                paint(world, character_floor, xx, corner[1])
                pass
            for yy in range(min(oy, y), max(oy, y)+1):
                paint(world, character_floor, corner[0], yy)
                pass
            entrance['painted'] = True
            nearest['painted'] = True
            continue


        paint(world, character_floor, entrance['x'], entrance['y'])

        # This controls the step of the range() that controls the
        # upcoming for-loops.
        # Count up for things at higher coordinates, etc.
        # Restricts the difference to -1 or 1
        major_direction = max(min(nearest[major] - entrance[major], 1), -1)
        minor_direction = max(min(nearest[minor] - entrance[minor], 1), -1)

        major_length = abs(entrance[major] - nearest[major]) // 2
        minor_length = abs(entrance[minor] - nearest[minor])
        boost = (major_length * major_direction) + major_direction

        # From the current entrance halfway to the other
        for m in range(major_length):
            m += 1
            m = entrance[major] + (major_direction * m)
            paint(world, character_floor, **{major: m, minor: entrance[minor]})
        
        # From the halfway point to the other entrance
        for m in range(major_length):
            m = nearest[major] - (major_direction * m)
            paint(world, character_floor, **{major: m, minor: nearest[minor]})
            pass
        
        # Connect these two half-lengths with the minor axis
        if minor_direction == 0:
            paint(world, character_floor, **{minor: entrance[minor], major: entrance[major]+boost})
        else:
            for m in range(entrance[minor], nearest[minor]+minor_direction, minor_direction):
                paint(world, character_floor, **{minor: m, major: entrance[major]+boost})
                pass

        entrance['painted'] = True
        nearest['painted'] = True

    # Suggest a spawn point and exit point
    for suggestion in [character_spawnpoint, character_exitpoint]:
        if suggestion is None:
            continue
        room = random.choice(rooms)
        x = random.randint(room.ulx, room.lrx)
        y = random.randint(room.uly, room.lry)
        paint(world, suggestion, x, y)

    if include_metadata:
        meta = 'rooms: %d, entrances: %d' % (len(rooms), len(entrances))
        world.append(meta)
    
    return world










def PNG_example(filename, **kwargs):
    from PIL import Image
    world = generate_dungeon(**kwargs)
    if kwargs.get('include_metadata', False):
        world = world[:-1]
    height = len(world)
    width = len(world[0])
    i = Image.new('RGBA', (width, height))
    for (yindex, yline) in enumerate(world):
        for (xindex, character) in enumerate(yline):
            if character == '#':
                value = (0, 0, 0)
            elif character == ' ':
                value= (255, 255, 255)
            elif character == 'I':
                value= (255, 0, 0)
            elif character == 'O':
                value= (0, 255, 0)
            i.putpixel((xindex, yindex), value)
    
    #i = i.resize((width * 2, height * 2))
    i.save(filename)

def TXT_example(filename, **kwargs):
    world = generate_dungeon(**kwargs)
    world = [''.join(yline) for yline in world]
    world = '\n'.join(world)
    if not filename.endswith('.txt'):
        filename += '.txt'
    out = open(filename, 'w')
    out.write(world)
    out.close()

PNG_example('example001.png',
    world_width=512,
    world_height=64,
    min_room_width=12,
    min_room_height=12,
    max_room_width=30,
    max_room_height=30,
    min_room_squareness=0.5,
    min_room_count=12,
    max_room_count=25,
    character_wall='#',
    character_floor=' ',
    include_metadata=False,
    character_spawnpoint='I',
    character_exitpoint='O',
    room_replace_attempts=6,
    force_random_seed=8,
    )
TXT_example('example002.txt',
    world_width=128,
    world_height=64,
    min_room_width=12,
    min_room_height=12,
    max_room_width=30,
    max_room_height=30,
    min_room_squareness=0.5,
    min_room_count=12,
    max_room_count=25,
    character_wall='#',
    character_floor=' ',
    include_metadata=True,
    character_spawnpoint='I',
    character_exitpoint='O',
    room_replace_attempts=6,
    force_random_seed=8,
    )
PNG_example('example003.png',
    world_width=512,
    world_height=512,
    min_room_width=12,
    min_room_height=12,
    max_room_width=30,
    max_room_height=30,
    min_room_squareness=1,
    min_room_count=12,
    max_room_count=25,
    character_wall='#',
    character_floor=' ',
    include_metadata=True,
    character_spawnpoint='I',
    character_exitpoint='O',
    room_replace_attempts=6,
    force_random_seed=88,
    )
PNG_example('example004.png',
    world_width=512,
    world_height=512,
    min_room_width=6,
    min_room_height=6,
    max_room_width=80,
    max_room_height=80,
    min_room_squareness=0,
    min_room_count=12,
    max_room_count=25,
    character_wall='#',
    character_floor=' ',
    include_metadata=True,
    character_spawnpoint='I',
    character_exitpoint='O',
    room_replace_attempts=6,
    force_random_seed=7777,
    )
TXT_example('example005.txt',
    world_width=256,
    world_height=256,
    min_room_width=6,
    min_room_height=6,
    max_room_width=30,
    max_room_height=30,
    min_room_squareness=1,
    min_room_count=3,
    max_room_count=8,
    character_wall='#',
    character_floor=' ',
    include_metadata=True,
    character_spawnpoint='I',
    character_exitpoint='O',
    room_replace_attempts=6,
    force_random_seed=1212,
    )