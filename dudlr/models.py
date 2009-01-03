
from google.appengine.ext import db

class Dudlr(db.Expando):
    """
    A user in the dudle system linked to a google account.

    @param name: screenname of the user
    @param account: Google account associated with the user
    """
    name = db.StringProperty(required=True)
    user = db.UserProperty(required=True )

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
    public = db.BooleanProperty(default=True)
    anonymous = db.BooleanProperty(default=False)
    rating = db.RatingProperty(default=0)
    rated_count = db.IntegerProperty(default=0)
    image_data = db.BlobProperty()
    strokes = db.BlobProperty()
    complete = db.BooleanProperty(default=False)
    artist = db.ReferenceProperty(Dudlr)


class DudleRating(db.Model):
    """
    A record of a users rating on a dudle
    """
    dudle_id = db.IntegerProperty(required=True)
    rating = db.RatingProperty(default=0)
    user = db.UserProperty(required=True)


