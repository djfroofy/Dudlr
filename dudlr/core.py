import logging
from StringIO import StringIO

from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.api import users

from dudlr.models import Dudlr, Dudle, DudleRating
from dudlr.ext import png


ERROR_DUDLR_NAME_TAKEN = 'dudlr name is already been taken'
ERROR_DUDLR_NAME_FROZEN = 'dudlr name has already been set'
ERROR_NOT_LOGGED_IN = 'user not logged in'
ERROR_CONFLICT_OF_INTEREST = 'user cannot rate his/her own dudle'

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

    @param user: C{User} object
    """
    user = user or users.get_current_user()
    if not user:
        return
    dudlr = Dudlr.all()
    dudlr.filter('user = ', user)
    dudlr = dudlr.get()
    if not dudlr:
        dudlr = Dudlr(user=user, name=user.nickname())
        dudlr.put()
    return dudlr

def get_dudlr_by_name(name):
    """
    Get dudlr by name.

    @param name: nickname of dudlr
    """
    dudlr = Dudlr.all().filter('name = ', name).get()
    return dudlr

def get_dudlr_by_id(id):
    """
    Get dudlr by id.

    @param id: numeric id of the C{Dudlr}
    """
    key = Key.from_path('Dudlr', id)
    dudlr = Dudlr.get(key)#Dudlr.all().filter('name = ', name).get()
    return dudlr

def set_dudlr_name(user, name):
    """
    Update Dudlr with new nickname.  Note that this can only be
    changed once.

    @param user: C{User} object
    @param name: new name for user
    """
    dudlr = Dudlr.all().filter('user = ', user).get()
    if dudlr.name != user.nickname():
        raise DudleException(ERROR_DUDLR_NAME_FROZEN)
    other = Dudlr.all().filter('name = ', name).get()
    if other:
        raise DudleException(ERROR_DUDLR_NAME_TAKEN)
    dudlr.name = name
    dudlr.put()

def create_dudle(dudlr=None, request=None):
    """
    Create a new unfinalized Dudle and an associated DudlePartial 
    object.
    """
    dudlr = dudlr or get_dudlr()
    dudle = Dudle(name="A doodle")
    dudle.artist = dudlr
    # todo save
    #if not dudlr and request:
    #    dudle.ip_address = request.
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

def finalize_dudle_strokes(id, public=True, anonymous=False):
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    dudle.anonymous = anonymous
    dudle.public = public
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
        raise DudleException(ERROR_NOT_LOGGED_IN)
    dudle_rating = DudleRating.all().filter('user = ', user).filter('dudle_id = ', id).get()
    rated = True
    if not dudle_rating:
        rated = False
        dudle_rating = DudleRating(user=user, rating=rating, dudle_id=id)
    key = Key.from_path('Dudle', id)
    dudle = Dudle.get(key)
    if dudle.artist and dudle.artist.user.email() == user.email():
        raise DudleException(ERROR_CONFLICT_OF_INTEREST)
    if not rated:
        adj = rating / float(dudle.rated_count + 1)
        r = dudle.rating * (dudle.rated_count/float(dudle.rated_count + 1))
        dudle.rated_count += 1
        r = r + adj
    else:
        adj = rating / float(dudle.rated_count)
        r = dudle.rating - (dudle_rating.rating / float(dudle.rated_count))
        dudle_rating.rating = rating
        r = r + adj
    if r > 100:
        r = 100
    dudle.rating = int(round(r))
    logging.info('Updated rating : ' + str(dudle.rating));
    dudle.put()
    dudle_rating.put()
    return dudle
    

def get_latest_dudles(limit=5, order='asc', offset=0):
    """
    Get last C{limit} dudles
    """
    o = { 'asc':'', 'desc':'-' }[order]
    dudles = Dudle.all().filter('complete = ', True
            ).filter('public = ', True).order('%screated_date' % o).fetch(limit)
    return dudles


def get_gallery(artist, current_user=None, offset=0, limit=5):
    """
    Get dudles by artist.

    @param artist: the C{Dudlr} artist
    @param current_user: the current ${User}
    @param offset: offset into results
    @param limit: limit of dules to return (default: 5)
    """
    #o = { 'asc':'', 'desc':'-' }[order]
    current_user = current_user or users.get_current_user
    query = Dudle.all().filter('artist = ', artist).filter('complete = ', True)
    if current_user != artist.user:
        query = query.filter('public = ', True).filter('anonymous = ', False)
    dudles = query.order('-created_date').fetch(limit=limit, offset=offset)
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


