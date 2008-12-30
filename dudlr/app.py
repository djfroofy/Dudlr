from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

from dudlr import views


DEBUG = True

def main():
    app = webapp.WSGIApplication([
        ('/', views.ViewDudleHandler),
        ('/e0be1635-0883-499f-b6bd-fda13721d304', views.DudlrDemoHandler),
        ('/dudles/view', views.ViewDudleHandler),
        ('/dudles/images', views.DudleImage),
        ('/json/dudles/save', views.DudleCreationHandler),
        ('/json/dudles/update', views.DudleUpdateHandler)
        ], debug=DEBUG)
    run_wsgi_app(app)


if __name__ == '__main__':
    main()

