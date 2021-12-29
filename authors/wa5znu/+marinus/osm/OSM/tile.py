#!/usr/bin/python

# Copyright 2012 Leigh L. Klotz, Jr. WA5ZNU
# Thanks to Ben Elliott for explaining OSM tiling:
# http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
# Python PIL tutorial:
# http://www.raywenderlich.com/1223/how-to-generate-game-tiles-with-python-imaging-library
# AUP for tile servers
# http://wiki.openstreetmap.org/wiki/Tile_usage_policy
# MapQuest Tile Servers
# http://wiki.openstreetmap.org/wiki/Mapquest#MapQuest-hosted_map_tiles

import urllib, sys, os, random, tempfile, zipfile, shutil, StringIO
from PIL import Image, ImageDraw
import Tiles
from Tiles import vadd, vsub, vmul, vdiv, vint, vidiv, vmod

DEBUG = False

class Config(object):
    def __init__(self, qra, zoom, ntiles, server_type):
	QRA = qra
	ZOOM = zoom
	# 'mapquest' or 'mapquest_open_aerial'
	SERVER_TYPE = server_type
	# Create up to NxN LCD tiles from within the OSM tiles
	LCD_TILES_SQUARE = ntiles
	LCD_TILES_DELTAS = range(-(LCD_TILES_SQUARE//2), 1+(LCD_TILES_SQUARE//2))
	LCD_TILES_OFFSETS = ((-LCD_TILES_DELTAS[0],) * 2)

	OSM_TILE_WIDTH = 256
	OSM_TILE_HEIGHT = 256
	OSM_TILE_SIZE = (OSM_TILE_WIDTH, OSM_TILE_HEIGHT)
	LCD_TILE_WIDTH = 128
	LCD_TILE_HEIGHT = 160
	LCD_TILE_SIZE = (LCD_TILE_WIDTH, LCD_TILE_HEIGHT)

	MIN_RATIO = min(float(OSM_TILE_HEIGHT)/LCD_TILE_HEIGHT, float(OSM_TILE_WIDTH)/LCD_TILE_WIDTH)
	# Fetch (up to) this many OSM tiles on demand
	OSM_TILES_SQUARE = int(2+((LCD_TILES_SQUARE)/MIN_RATIO))
	OSM_TILES_DELTAS = range(-(OSM_TILES_SQUARE//2), 1+(OSM_TILES_SQUARE//2))
	# Add this to OSM_TILE_DELTAS (dx,dy) to convert to zero-based.
	# i.e. for 3x3 tiles it is (1,1); for 5x5 it is (3,3).
	OSM_TILES_OFFSETS = ((-OSM_TILES_DELTAS[0],) * 2)

	TILE_CACHE_DIR = "/tmp/tilecache"

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

	SERVER_URL_PREFIX = random.choice(SERVERS[SERVER_TYPE])

	# For finding poi.csv.template, etc.
	SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) + os.sep

	# Store all the above variables in this config object
	self.__dict__.update(locals())

class POI(object):
  def __init__(self, config):
    self.config = config
    self.qra = config.QRA
    self.zoom = config.ZOOM
    self.lonlat = Tiles.qra_lonlat(self.qra)
    (self.lon, self.lat) = self.lonlat
    xytile = Tiles.lonlat_tile(self.lon, self.lat, self.zoom)
    self.osm_tile = OSM_Tile(self.config, "(POI)", xytile, (0, 0), self.zoom)

  def lonlat_xy_in_composite_osm_tile(self):
    return self.osm_tile.lonlat_xy_in_composite_osm_tile(self.lon, self.lat)


class OSM_Tile(object):
  def __init__(self, config, name, xytile, tile_delta, zoom):
    self.config = config
    self.name = name
    self.xytile = xytile
    self.tile_delta = tile_delta
    self.zoom = zoom
    self.osm_tile_image = None
    self.size_in_degrees = Tiles.tile_size_in_degrees(self.xytile, self.zoom)
    self.top_left_lonlat = Tiles.tile_top_left_corner_lonlat(self.xytile, self.zoom)
    (self.top_left_lon, self.top_left_lat) = self.top_left_lonlat
    self.pixels_per_degree = vdiv(self.config.OSM_TILE_SIZE, self.size_in_degrees) # lon,lat order
    if DEBUG:
	print >> sys.stderr, "%s size in degrees dlon=%f dlat=%f" % ((self.name,) + self.size_in_degrees)
	print >> sys.stderr, "%s pixels_per_degree = don=%f dlat%f" % ((self.name,) + self.pixels_per_degree)

  def retrieve(self):
    if self.osm_tile_image == None:
      dirname = "%s/%s/%d/%d" % (self.config.TILE_CACHE_DIR, self.config.SERVER_TYPE, self.zoom, self.xytile[0])
      fn = "%s/%d.png" % (dirname, self.xytile[1])
      if (not os.path.isdir(dirname)):
	  print >> sys.stderr, "make dirs "+ dirname
	  os.makedirs(dirname);
      if (not os.path.isfile(fn)):
	  resource = "%s/%d/%d/%d.png" % ((self.config.SERVER_URL_PREFIX, self.zoom) + self.xytile)
	  print >> sys.stderr, "fetching %s to %s" % (resource, fn)
	  urllib.urlretrieve(resource, fn)
      else:
	  if DEBUG: print >> sys.stderr, "cached %s" % (fn)
      try:
        self.osm_tile_image = Image.open(fn)
      except:
        print >> sys.stderr, "fn = " + fn
        raise
    return self.osm_tile_image

  # Note that lon,lat input results in x,y output
  def lonlat_xy(self, lon, lat):
    # lon increases left->right, but lat increases bottom->top
    #print >> sys.stderr, "osm_tile %s self.top_left_lon lat %f %f finding lonlat %f %f" % (self.name, self.top_left_lon, self.top_left_lat, lon, lat)
    delta_degrees = vsub((lon, self.top_left_lat), (self.top_left_lon, lat))
    return vint(vmul(delta_degrees, self.pixels_per_degree))

  def xy_lonlat(self, xy):
    # lon increases left->right, but lat increases bottom->top
    return(self.top_left_lon + (xy[0] / self.pixels_per_degree[0]),
           self.top_left_lat - (xy[1] / self.pixels_per_degree[1]))

class Composite_Tile(object):
  def __init__(self, config, poi):
    self.config = config
    self.poi = poi
    self.poi_lonlat = poi.lonlat
    self.zoom = poi.zoom
    self.qra = poi.qra
    self.composite_image = None
    self.xy = poi.osm_tile.xytile       # xy is osm tile xy of tile containing POI; rename somehow
    self.x = self.xy[0]
    self.y = self.xy[1]
    self.osm_tiles_by_xytile = {}
    self.osm_tiles_by_dxdy = {}         # dxdy is (-1,-1), (0,1) etc.

  # We know the POI(lat, lon) of the POI and the center tile's upper left(lat, lon).
  # Subtract POI(lat,lon) from center tile's upper left to find delta degrees (lat,lon)
  # Calculate the pixels/degree in X and Y dimensions and multiply by deltadegrees.
  # Add that to pixel position of tile's top_left_pixel,
  # which is (OSM_TILE_WIDTH, OSM_TILE_HEIGHT) for the center tile.
  # Note that lat,lon input results in x,y output even though lat is Y and lon is X.
  def lonlat_xy_in_composite_osm_tile(self, lonlat):
    osm_tile = self.osm_tiles_by_xytile[Tiles.lonlat_tile(lonlat[0], lonlat[1], self.zoom)]
    #print >> sys.stderr, "OSM tile is '%s' tile_delta %d %d" % ((osm_tile.name,)+ osm_tile.tile_delta)
    top_left_pixel_xy = vmul(self.config.OSM_TILE_SIZE, vadd(osm_tile.tile_delta, self.config.OSM_TILES_OFFSETS))
    #print >> sys.stderr, "top_left_pixel_xy is %d %d" % top_left_pixel_xy
    return vadd(top_left_pixel_xy, osm_tile.lonlat_xy(lonlat[0], lonlat[1]))

  def retrieve(self):
    if self.composite_image == None:
      self.composite_image = Image.new("RGB", (self.config.OSM_TILE_WIDTH * self.config.OSM_TILES_SQUARE, self.config.OSM_TILE_HEIGHT * self.config.OSM_TILES_SQUARE), (0, 0, 0))

      for dy in self.config.OSM_TILES_DELTAS:
        for dx in self.config.OSM_TILES_DELTAS:
          dxdy = (dx, dy)
          osm_tile = OSM_Tile(self.config, Tiles.rose(self.config.OSM_TILES_OFFSETS, dx, dy), vadd((self.x, self.y), dxdy), dxdy, self.config.zoom)
          self.osm_tiles_by_xytile[osm_tile.xytile] = osm_tile
	  if DEBUG:
	      print >> sys.stderr, "Adding self.osm_tiles_by_dxdy[%s] = osm_tile" % (dxdy,)
          self.osm_tiles_by_dxdy[dxdy] = osm_tile
          osm_tile_image = osm_tile.retrieve()
          box = (vmul(self.config.OSM_TILE_SIZE, vadd((dx, dy), self.config.OSM_TILES_OFFSETS)) +
                 vmul(self.config.OSM_TILE_SIZE, vadd((dx, dy), vadd(self.config.OSM_TILES_OFFSETS, (1, 1)))))
          self.composite_image.paste(osm_tile_image, box)
      fn = "%s-%s-%dx%dx%d.png" % (self.config.SERVER_TYPE, self.config.QRA, self.config.OSM_TILE_WIDTH, self.config.OSM_TILE_HEIGHT, self.config.OSM_TILES_SQUARE)
      if DEBUG:
	  print >> sys.stderr, "Saving composite map image to " + fn
	  self.composite_image.save(fn)
    return self.composite_image

  def draw_debug(self, draw):
    # draw outlines of original OSM tiles in GREEN
    for dy in self.config.OSM_TILES_DELTAS:
        for dx in self.config.OSM_TILES_DELTAS:
          box1 = vmul(self.config.OSM_TILE_SIZE, (vadd((dx, dy), self.config.OSM_TILES_OFFSETS)))
          box2 = vmul(self.config.OSM_TILE_SIZE, (vadd((dx, dy), vadd(self.config.OSM_TILES_OFFSETS, (1, 1)))))
          box = box1+box2
          draw.rectangle(box, outline='#00ff00')
    # Draw dot at QRA in BLUE
    (px, py) = self.lonlat_xy_in_composite_osm_tile(self.poi.lonlat)
    #print >> sys.stderr, "qra (px,py) = (%d, %d)" % (px,py)
    Tiles.drawCircle(draw, px, py, 2, '#0000ff')
    # print >> sys.stderr, QRA at POI in BLUE
    # draw.text((px, py), qra, fill='#0000ff')


class LCD_Tile(object):
  def __init__(self, name, xy, top_left_lonlat, bottom_right_lonlat, lcd_image):
    self.name = name
    self.xy = xy
    self.lcd_image = lcd_image
    self.top_left_lonlat = top_left_lonlat
    self.bottom_right_lonlat = bottom_right_lonlat

class LCD_Tiles(object):
  def __init__(self, config, poi, composite_tile):
    self.config = config
    self.poi = poi
    self.composite_tile = composite_tile
    self.lcd_tiles = {}
    self.lon_degrees_per_pixel = 0.0
    self.lat_degrees_per_pixel = 0.0

  def clip_lcd_tiles(self):
    result = []
    description_fn = None
    if DEBUG:
	description_fn = "%s-%s-%dx%d.txt" % (self.config.SERVER_TYPE, self.config.qra, self.config.LCD_TILE_WIDTH, self.config.LCD_TILE_HEIGHT)
	try:
	    os.remove(description_fn)
	except:
	    pass
    poi_xy = self.composite_tile.lonlat_xy_in_composite_osm_tile(self.poi.lonlat)
    if DEBUG:
	print >> sys.stderr, "poi_xy %d %d in composite_osm_tile" % poi_xy
    center_lcd_tile_center_xy = (self.config.LCD_TILE_WIDTH / 2, self.config.LCD_TILE_HEIGHT / 2)
    if DEBUG:
	print >> sys.stderr, "center_lcd_tile_center_xy = %s %s" % (center_lcd_tile_center_xy)
    for dy in self.config.LCD_TILES_DELTAS:
        for dx in self.config.LCD_TILES_DELTAS:
          if DEBUG:
	      print >> sys.stderr, "Creating LCD_Tile %s (%d %d) " % (Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy), dx, dy)
          lcd_tile_dxy = vadd(poi_xy, vmul(self.config.LCD_TILE_SIZE, (dx, dy)))
          composite_box_top_left_xy = vsub(lcd_tile_dxy, center_lcd_tile_center_xy)
          composite_box_bottom_right_xy = vadd(lcd_tile_dxy, center_lcd_tile_center_xy)
          box = composite_box_top_left_xy + composite_box_bottom_right_xy
          lcd_image = self.composite_tile.composite_image.crop(box)
          osm_tl_dxdy = vsub(vidiv(composite_box_top_left_xy, self.config.OSM_TILE_SIZE), self.config.OSM_TILES_OFFSETS)
          osm_br_dxdy = vsub(vidiv(composite_box_bottom_right_xy, self.config.OSM_TILE_SIZE), self.config.OSM_TILES_OFFSETS)
	  if DEBUG:
	      print >> sys.stderr, "  LCD_Tile composite_box_top_left_xy = %d %d" % (composite_box_top_left_xy)
	      print >> sys.stderr, "  LCD_Tile osm_tl_dxdy = %d %s upper left is at this location in composite_box: %d %d" % (osm_tl_dxdy + composite_box_top_left_xy)
	      print >> sys.stderr, "  LCD_Tile osm_br_dxdy = %d %s bottom right is at this location in composite_box: %d %d" % (osm_br_dxdy + composite_box_top_left_xy)
	      print >> sys.stderr, "osm_tl_dxdy = %s osm_br_dxdy = %s" % (osm_tl_dxdy, osm_br_dxdy)
          osm_tile_tl = self.composite_tile.osm_tiles_by_dxdy[osm_tl_dxdy]
          osm_tile_br = self.composite_tile.osm_tiles_by_dxdy[osm_br_dxdy]
	  if DEBUG:
	      print >> sys.stderr, "  OSM_TILE pixels_per_degree %f %f, %f %f" % (osm_tile_tl.pixels_per_degree+osm_tile_br.pixels_per_degree)
	      print >> sys.stderr, "  OSM_Tile %s top_left_lonlat %f %f" % (osm_tile_tl.name, osm_tile_tl.top_left_lon, osm_tile_tl.top_left_lat)
          lcd_tile_top_left_in_osm_tile = vmod(composite_box_top_left_xy, self.config.OSM_TILE_SIZE)
          lcd_tile_bottom_right_in_osm_tile = vmod(composite_box_bottom_right_xy, self.config.OSM_TILE_SIZE)
          lcd_tile_top_left_lonlat = osm_tile_tl.xy_lonlat(lcd_tile_top_left_in_osm_tile)
          lcd_tile_bottom_right_lonlat = osm_tile_br.xy_lonlat(lcd_tile_bottom_right_in_osm_tile)
          #print >> sys.stderr, "  LCD_Tile %s (%d,%d) lcd_tile_top_left_in_osm_tile: %d %d" % ((Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy), dx, dy) + lcd_tile_top_left_in_osm_tile)
          #print >> sys.stderr, "  LCD_Tile %s (%d,%d) top left lon lat %f %f" % ((Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy), dx, dy) + lcd_tile_top_left_lonlat)
          if False:
            self.lcd_tiles[(dx,dy)] = LCD_Tile(Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy), (dx,dy), lcd_tile_top_left_lonlat, lcd_tile_bottom_right_lonlat, lcd_image)
          if DEBUG: png_fn = self.calculate_lcd_tile_fn(dx, dy)
          bmp_fn = self.calculate_lcd_bmp_fn(dx, dy)
          tl_latlon = Tiles.vswap(lcd_tile_top_left_lonlat)
          br_latlon = Tiles.vswap(lcd_tile_bottom_right_lonlat)
	  if DEBUG: lcd_image.save(png_fn, "PNG")
	  lcd_image.save(bmp_fn, "BMP")
	  result.append(bmp_fn)
          description = "%d,%d %d,%d\n" % tuple([round(x*1e6) for x in (tl_latlon[0],tl_latlon[1], br_latlon[0],br_latlon[1])])
	  self.lat_degrees_per_pixel += (br_latlon[0] - tl_latlon[0])
  	  self.lon_degrees_per_pixel += (br_latlon[1] - tl_latlon[1])
	  if dx == 0 and dy == 0:
	      poi_lcd_tile_tl_latlon = tl_latlon
	  if DEBUG:
	      #print >> sys.stderr, "Adding LCD map four corners to %s " % (description_fn)
	      with open(description_fn, 'a') as f:
		  f.write(Tiles.rose(self.config.LCD_TILES_OFFSETS, dx,dy))
		  f.write(" ")
		  f.write(description)
	      result.append(description_fn)
    pixels_files =  self.save_pixels_file(poi_lcd_tile_tl_latlon)
    result.extend(pixels_files)
    return result

  def save_pixels_file(self, poi_lcd_tile_tl_latlon):
    result = []
    self.lon_degrees_per_pixel = int(round(self.lon_degrees_per_pixel * 1e6 / self.config.LCD_TILE_WIDTH / (self.config.LCD_TILES_SQUARE * self.config.LCD_TILES_SQUARE)))
    self.lat_degrees_per_pixel = int(round(self.lat_degrees_per_pixel * 1e6 / self.config.LCD_TILE_HEIGHT / (self.config.LCD_TILES_SQUARE * self.config.LCD_TILES_SQUARE)))
    poi_h_template = open(self.config.SCRIPT_DIR + 'poi.h.template', 'r').read()
    if DEBUG:
	print >> sys.stderr, "Saving LCD map lon,lat degrees*1e6 per pixel to poi.h"
    with open('poi.h', 'w') as f:
	f.write(poi_h_template % (self.config.LCD_TILE_WIDTH, self.config.LCD_TILE_HEIGHT,
				  self.config.QRA, self.config.ZOOM,
				  (int(round(poi_lcd_tile_tl_latlon[0] * 1e6))),
				  (int(round(poi_lcd_tile_tl_latlon[1] * 1e6))),
				  abs(self.lat_degrees_per_pixel),
				  abs(self.lon_degrees_per_pixel),
				  self.config.LCD_TILES_SQUARE, self.config.LCD_TILES_SQUARE))
    result.append('poi.h')
    if DEBUG:
	print >> sys.stderr, "Saving LCD map lon,lat degrees*1e6 per pixel to poi.csv"
    poi_csv_template = open(self.config.SCRIPT_DIR + 'poi.csv.template', 'r').read()
    with open('poi.csv', 'w') as f:
	f.write(poi_csv_template % (self.config.LCD_TILE_WIDTH, self.config.LCD_TILE_HEIGHT,
				  self.config.qra, self.config.ZOOM, 
				  (int(round(poi_lcd_tile_tl_latlon[0] * 1e6))),
				  (int(round(poi_lcd_tile_tl_latlon[1] * 1e6))),
				  abs(self.lat_degrees_per_pixel),
				  abs(self.lon_degrees_per_pixel),
				  self.config.LCD_TILES_SQUARE, self.config.LCD_TILES_SQUARE))
    result.append('poi.csv')
    return result

  def calculate_lcd_tile_fn(self, dx, dy):
      return "%s-%s-%dx%d-%s.png" % (self.config.SERVER_TYPE, self.config.qra, self.config.LCD_TILE_WIDTH, self.config.LCD_TILE_HEIGHT, Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy))

  def calculate_lcd_bmp_fn(self, dx, dy):
      return "map%s.bmp" % (Tiles.rose(self.config.LCD_TILES_OFFSETS, dx, dy))

  def draw_debug(self, draw):
    poi_xy = self.composite_tile.lonlat_xy_in_composite_osm_tile(self.poi.lonlat)
    lcd_tile_center = (self.config.LCD_TILE_WIDTH / 2, self.config.LCD_TILE_HEIGHT / 2)
    # draw debugging info on image and save as foo.png
    # draw outlines of LCD tile crop in RED
    for dy in self.config.LCD_TILES_DELTAS:
        for dx in self.config.LCD_TILES_DELTAS:
          xy = vadd(poi_xy, vmul(self.config.LCD_TILE_SIZE, (dx, dy)))
          box = vsub(xy, lcd_tile_center) + vadd(xy, lcd_tile_center)
          draw.rectangle(box, outline='#ff0000')


# this makes a copy of the NxN (e.g. 3x3) 256x256 OSM tile composite image and draw on it,
# for debugging.  It draws the outlines of the OSM tiles and the outlines
# of the LCD tiles and a point at the POI
def save_debug_image(composite_tile, lcd_tiles):
  image = composite_tile.composite_image
  draw = ImageDraw.Draw(image)
  if DEBUG:
      composite_tile.draw_debug(draw)
      lcd_tiles.draw_debug(draw)
      print >> sys.stderr, "Saving debug-decorated composite map image to foo.png"
      image.save("foo.png")
    
def tilezip(qra, zoom, n):
    style='mapquest'
    config = Config(qra, zoom, n, style)
    poi = POI(config)
    composite_tile = Composite_Tile(config, poi)
    tempdir = tempfile.mkdtemp()
    old_dir = os.getcwd()
    os.chdir(tempdir)
    composite_tile.retrieve()
    lcd_tiles = LCD_Tiles(config, poi, composite_tile)
    filenames = lcd_tiles.clip_lcd_tiles()
    if DEBUG: save_debug_image(composite_tile, lcd_tiles)
    #zipfn = "%s/%s-%s-%d-%d.zip" % (old_dir, qra, style, zoom, n)
    filething = StringIO.StringIO()
    with zipfile.ZipFile(filething, "w", zipfile.ZIP_DEFLATED) as myZipFile:
	for fn in filenames:
	    myZipFile.write(fn)
    os.chdir(old_dir)
    # remove tmp files but do safety check
    if not DEBUG:
	if tempdir.startswith("/tmp/"): shutil.rmtree(tempdir)

    return filething.getvalue()

if __name__ == "__main__":
    if len(sys.argv) < 3:
	print >> sys.stderr, "usage: tile qra zoom ntiles"
	sys.exit(-1)

    qra = sys.argv[1]
    style = 'mapquest'
    zoom = int(sys.argv[2])
    n = int(sys.argv[3])

    fn = "%s-%s-%d-%d.zip" % (qra, style, zoom, n)
    with open(fn, 'w') as f:
	f.write(tilezip(qra, zoom, n))
    print(fn)

