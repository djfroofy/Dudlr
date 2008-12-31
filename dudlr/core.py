import logging
from StringIO import StringIO

from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.api import users

from dudlr.models import Dudlr, Dudle, DudleRating
from dudlr.ext import png


class DudleException(Exception):
    pass

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
    if not user:
        return
    dudlr = Dudlr.all()
    dudlr.filter('user = ', user)
    dudlr = dudlr.get()
    if not dudlr:
        dudlr = Dudlr(user=user, name='dudlr')
        dudlr.put()
    return dudlr

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
    dudle.put()
    return dudle


def update_dudle(id, format, data):
    """
    Update DudlePartial with data received from client
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key);
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
    dudle.image_data = _pngData(dudle.partial_data, width, height)
    del dudle.partial_data
    dudle.complete = True
    dudle.put()

def finalize_dudle_strokes(id):
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    dudle.strokes = dudle.partial_stroke_data
    if hasattr(dudle, 'partial_data'):
        del dudle.partial_data
    del dudle.partial_stroke_data
    if len(dudle.strokes) > 7:
        dudle.complete = True
    dudle.put()

def get_dudle(id):
    """
    Get dudle for id
    """
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    return dudle

def rate_dudle(id, rating, user):
    """
    Rate a dudle - may only be done once per dudle per authenticated user.

    @param id: id of dudle to rate
    @param rating: the rating (0-100)
    @param user: the user rating the dudle
    """
    if not user:
        raise DudleException('user not logged in')
    dudle_rating = DudleRating.all().filter('user = ', user).filter('id = ', id).get()
    if dudle_rating:
        raise DudleException('user already rated dudle')
    dudle_rating = DudleRating(user=user, rating=rating, dudle_id=id)
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    #dudle.rated_count.increment()
    adj = rating / float(dudle.rated_count + 1)
    dudle.rated_count += 1
    r = dudle.rating * (dudle.rated_count/float(dudle.rated_count + 1))
    r = r + adj
    if r > 100:
        r = 100
    dudle.rating = int(r)
    logging.info('Updated rating : ' + str(dudle.rating));
    dudle.put()
    dudle_rating.put()
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


