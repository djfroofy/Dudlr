
from google.appengine.ext import db

class Dudlr(db.Expando):
    """
    A user in the dudle system linked to a google account.
    """
    name = db.StringProperty(required=True)
    account = db.UserProperty(required=True )

class Dudle(db.Expando):
    """
    A saved dudle with an associated artist. 
    """
    created_date = db.DateTimeProperty(auto_now_add=True)
    updated_date = db.DateTimeProperty(auto_now=True)
    public = db.BooleanProperty(default=False)
    anonymous = db.BooleanProperty(default=False)
    rating = db.RatingProperty()
    image_data = db.BlobProperty()
    artist = db.ReferenceProperty(Dudlr)

class DudlePartial(db.Model):
    """
    Partial upload of a Dudle.  When completed image data is copied
    to associated Dudle object and the DudlePartial is removed.
    """
    dudle = db.ReferenceProperty(Dudle, required=True)
    data = db.BlobProperty(default='')
    #data = db.ListProperty(default=[])

