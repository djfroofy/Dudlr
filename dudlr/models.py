
from google.appengine.ext import db

class Dudlr(db.Expando):
    """
    A user in the dudle system linked to a google account.

    @param name: screenname of the user
    @param account: Google account associated with the user
    """
    name = db.StringProperty(required=True)
    account = db.UserProperty(required=True )

class Dudle(db.Expando):
    """
    A saved dudle with an associated artist.

    @param created_date: Date and time dudle was created
    @param uploaded_date: Last date and time dudle was updated
    @param public: Dudle is publically visible
    @param anonymous: Dudle artist should appear anonymously
    @param rating: Community rating of dudle
    @param image_data: Image data (PNG-encoded)
    @param complete: Upload has completed
    @param artist: Dudlr who drew the dudle
    """
    created_date = db.DateTimeProperty(auto_now_add=True)
    updated_date = db.DateTimeProperty(auto_now=True)
    public = db.BooleanProperty(default=False)
    anonymous = db.BooleanProperty(default=False)
    rating = db.RatingProperty()
    image_data = db.BlobProperty()
    strokes = db.BlobProperty()
    complete = db.BooleanProperty(default=False)
    artist = db.ReferenceProperty(Dudlr)
    # partial = Temporary reference to partially uploaded image data

#class DudlePartial(db.Model):
#    """
#    Partial upload of a Dudle.  When completed image data is copied
#    to associated Dudle object and the DudlePartial is removed.
#    """
#    dudle = db.ReferenceProperty(Dudle, required=True)
#    data = db.BlobProperty(default='')
#    #data = db.ListProperty(default=[])

