
from StringIO import StringIO

from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.api import users

from dudlr.models import Dudlr, Dudle
from dudlr.ext import png


def create_dudlr(user, name):
    """
    Create a new dudlr user
    """
    dudlr = Dudlr()
    dudlr.name = name
    dudlr.user = user
    dudlr.put()

def get_dudlr(user=None):
    """
    Get the dudlr associated with google user.
    """
    user = user or users.get_current_user()
    dudlr = Dudlr.all()
    dudlr.filter('user = ', user)
    return dudlr.get()

def create_dudle(dudlr=None):
    """
    Create a new unfinalized Dudle and an associated DudlePartial 
    object.
    """
    dudlr = dudlr or get_dudlr()
    dudle = Dudle(name="A doodle")
    dudle.artist = dudlr
    dudle.partial_data = db.Blob('')
    dudle.partial_stroke_data = db.Blob('')
    #dudle.partial_data = ''
    dudle.put()

    #dudlePartial = DudlePartial(dudle=dudle)
    #dudlePartial.put()

    return dudle


def update_dudle(id, format, data):
    """
    Update DudlePartial with data received from client
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key);
    #dudlePartial = DudlePartial.all().filter('dudle = ', dudle).get()
    #if not dudlePartial:
    #    dudlePartial = DudlePartial(dudle=dudle)
    if not hasattr(dudle, 'partial_data'):
        dudle.partial_data = db.Blob('')
    dudle.partial_data = db.Blob(dudle.partial_data
            + ''.join([ chr(int(n)) for n in data.split(',') ]))
    dudle.put()

def update_dudle_strokes(id, data):
    """Update stroke data
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key);
    if not hasattr(dudle, 'partial_stroke_data'):
        dudle.partial_stroke_data = db.Blob('')
    dudle.partial_stroke_data = db.Blob(dudle.partial_stroke_data
            + data)
    dudle.put()

def finalize_dudle(id, format, width, height):
    """
    Finalize the Dudle object based on associated DudlePartial
    object and remove the DudlePartial object from the datastore.
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    #dudlePartial = DudlePartial.all().filter('dudle = ', dudle).get()
    # TODO - convert to image type
    #dudle.image_data = _pngData(dudlePartial.data, width, height)
    dudle.image_data = _pngData(dudle.partial_data, width, height)
    del dudle.partial_data
    dudle.complete = True
    dudle.put()
    #dudlePartial.delete()

def finalize_dudle_strokes(id):
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    dudle.strokes = dudle.partial_stroke_data
    if hasattr(dudle, 'partial_data'):
        del dudle.partial_data
    del dudle.partial_stroke_data
    dudle.complete = True
    dudle.put()

def get_dudle(id):
    """
    Get dudle for id
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    return dudle

def get_latest_dudles(limit=50, order='asc'):
    """
    Get last C{limit} dudles
    """
    o = { 'asc':'', 'desc':'-' }[order]
    dudles = Dudle.all().filter('complete = ', True
            ).order('%screated_date' % o).fetch(limit)
    return dudles


def _pngData(data, width, height):
    fd = StringIO()
    writer = png.Writer(width, height, greyscale=True)
    def scanlines():
        for i in range(height):
            offset = i * width
            yield [ ord(c) for c in data[offset:offset+width] ]
    writer.write(fd, scanlines())
    return fd.getvalue()


