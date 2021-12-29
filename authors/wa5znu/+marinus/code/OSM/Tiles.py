#-*-Python-*-

# Copyright 2012 Leigh L. Klotz, Jr. WA5ZNU
# Thanks to Ben Elliott for explaining OSM tiling:
# http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
# AUP for tile servers
# http://wiki.openstreetmap.org/wiki/Tile_usage_policy
# MapQuest Tile Serers
# http://wiki.openstreetmap.org/wiki/Mapquest#MapQuest-hosted_map_tiles

import random
from math import cos, tan, log, pi, radians, atan, sinh, degrees

OSM_TILE_WIDTH = 256
OSM_TILE_HEIGHT = 256

SERVERS = {
'mapquest': ['http://otile1.mqcdn.com/tiles/1.0.0/osm',
             'http://otile2.mqcdn.com/tiles/1.0.0/osm',
             'http://otile3.mqcdn.com/tiles/1.0.0/osm',
             'http://otile4.mqcdn.com/tiles/1.0.0/osm'],
'mapquest_open_aerial': ['http://oatile1.mqcdn.com/naip',
                         'http://oatile2.mqcdn.com/naip',
                         'http://oatile3.mqcdn.com/naip',
                         'http://oatile4.mqcdn.com/naip'],
# OSM says you can't use their servers directly.
#'osm': ['http://a.tile.openstreetmap.org',
#        'http://b.tile.openstreetmap.org',
#        'http://c.tile.openstreetmap.org']
}

SERVER_TYPE = 'mapquest'
SERVER_URL_PREFIX = random.choice(SERVERS[SERVER_TYPE])


# From http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
def lonlat_tile(lon_deg, lat_deg, zoom):
  lat_rad = radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
  return (xtile, ytile)


def tile_lonlat(xytile, zoom):
  (xtile,ytile) = xytile
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
  lat_deg = degrees(lat_rad)
  return (lon_deg, lat_deg)

def tile_width_in_degrees(xytile, zoom):
  return abs(tile_top_right_corner_lonlat(xytile, zoom)[0]
             -
             tile_top_left_corner_lonlat(xytile, zoom)[0])

def tile_height_in_degrees(xytile, zoom):
  return abs(tile_top_left_corner_lonlat(xytile, zoom)[1]
             -
             tile_bottom_left_corner_lonlat(xytile, zoom)[1])

# lon width in degrees, lat height in degrees, gives x,y
def tile_size_in_degrees(xytile, zoom):
  return (tile_width_in_degrees(xytile, zoom),
          tile_height_in_degrees(xytile, zoom))
          

def tile_top_left_corner_lonlat(xytile, zoom):
  return tile_lonlat(xytile, zoom)

def tile_top_right_corner_lonlat(xytile, zoom):
  return tile_lonlat(vadd(xytile, (1,0)), zoom)

def tile_bottom_left_corner_lonlat(xytile, zoom):
  return tile_lonlat(vadd(xytile, (0,1)), zoom)

def tile_bottom_right_corner_lonlat(xytile, zoom):
  return tile_lonlat(vadd(xytile, (1,1)), zoom)

def qra_lonlat(qra):
  c1 = int(qra[0:1], 36) - 10            # C
  c2 = int(qra[1:2], 36) - 10            # M
  c3 = int(qra[2:3], 10)                 # 8
  c4 = int(qra[3:4], 10)                 # 7
  c5 = int(qra[4:5], 36) - 10            # w
  c6 = int(qra[5:6], 36) - 10            # k
  c7 = 0
  c8 = 0
  c9 = 0
  c10 = 0

  try:
      c7 = int(qra[6:7], 10)             # 6
      c8 = int(qra[7:8], 10)             # 2
      try:
          c9 = int(qra[8:9], 36) - 10    # e
          c10 = int(qra[9:10], 36) - 10  # w
          #c9 = c9 + 0.5
          #c10 = c10 + 0.5
      except:
          pass
          #c7 = c7 + 0.5
          #c8 = c8 + 0.5
  except:
      pass

  lon = (c1 * 10) + (c3 * 1) + (c5 / 24.0) + (c7 / 240.0) + (c9 / 5760.0)
  lat = (c2 * 10) + (c4 * 1) + (c6 / 24.0) + (c8 / 240.0) + (c10 / 5760.0)
  lat = lat - 90
  lon = (lon * 2) - 180
  return (lon, lat)

# vector addition of (x1,y1) + (x2,y2)
def vadd(xy1, xy2):
  return ((xy1[0] + xy2[0]), (xy1[1] + xy2[1]))

# vector subtraction of (x,y) - (x2,y2)
def vsub(xy1, xy2):
  return ((xy1[0] - xy2[0]), (xy1[1] - xy2[1]))

# vector multiplication of (x,y) * (x2,y2)
def vmul(xy1, xy2):
  return ((xy1[0] * xy2[0]), (xy1[1] * xy2[1]))

# vector division of (x,y) / (x2,y2)
def vdiv(xy1, xy2):
  return ((xy1[0] / xy2[0]), (xy1[1] / xy2[1]))

# vector integer truncation of (x,y)
def vint(xy):
  return (int(xy[0]), int(xy[1]))

# vector integer division of (x,y) / (x2,y2)
def vidiv(xy1, xy2):
  return ((xy1[0] // xy2[0]), (xy1[1] // xy2[1]))

# vector mod of (x,y)
def vmod(xy, m):
  return ((xy[0] % m[0]), (xy[1] % m[1]))

# vector swap of (x,y)
def vswap(xy):
  return (xy[1], xy[0])

def rose(offsets, dx, dy):
    #mapnnnn.png
    return "%02d%02d" % (offsets[0]+dx, offsets[1]+dy)

def drawCircle(draw, x, y, r, fill):
  draw.ellipse((x - r, y - r, x + r, y + r), fill)

