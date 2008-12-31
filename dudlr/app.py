from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

from dudlr import views


DEBUG = True

def main():
    app = webapp.WSGIApplication([
        ('/', views.ViewDudleHandler),
        ('/dudles/draw', views.DudlrDemoHandler),
        ('/dudles/view', views.ViewDudleHandler),
        ('/dudles/images', views.DudleImage),
        ('/profile/edit', views.EditProfileHandler),
        ('/profile/save', views.SaveProfileHandler),
        ('/json/dudles/save', views.DudleCreationHandler),
        ('/json/dudles/rate', views.RatingHandler),
        ('/json/dudles/update', views.DudleUpdateHandler),
        ('/json/dudles/updateStrokes', views.DudleUpdateStrokesHandler),
        ('/json/dudles/strokes', views.DudleStrokes)
        ], debug=DEBUG)
    run_wsgi_app(app)


if __name__ == '__main__':
    main()

