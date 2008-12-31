import logging

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.api import users

from dudlr import core
from dudlr.core import DudleException
from dudlr.utils import jinja_env, form

class TemplateRequestHandler(webapp.RequestHandler):

    def render_template(self, template, headers=None, **context):
        self.response.headers['Content-Type'] = 'text/html'
        context['user'] = user = users.get_current_user()
        context['dudlr'] = core.get_dudlr(user)
        if user is None:
            context['login_url'] = users.create_login_url('/')
        else:
            context['logout_url'] = users.create_logout_url('/')
        if headers:
            response.headers.update(headers)
        self.response.out.write(
                jinja_env.get_template(template).render(**context))

BaseHandler = TemplateRequestHandler

class JsonHandler(webapp.RequestHandler):

    def json(self, data):
        self.response.headers['Content-Type'] = 'application/json'
        simplejson.dump(data, self.response.out)

class DudlrDemoHandler(BaseHandler):

    def get(self):
        self.render_template('demo.html')


class DudleCreationHandler(JsonHandler):

    def post(self):
        dudle = core.create_dudle()
        self.json({'id':dudle.key().id()})


class DudleUpdateHandler(JsonHandler):

    @form('id:int', 'data:str', 'format:str', 'width:int', 'height:int')
    def post(self, id, data, format, width, height):
        core.update_dudle(id, format, data)
        core.finalize_dudle(id, format, width, height)
        self.json('ok')

class DudleUpdateStrokesHandler(JsonHandler):

    @form('id:int', 'data:str', 'width:int', 'height:int')
    def post(self, id, data, width, height):
        core.update_dudle_strokes(id, data)
        core.finalize_dudle_strokes(id)
        self.json('ok')

class ViewDudleHandler(BaseHandler):

    def get(self):
        #limit = self.request.get('limit', '5')
        #limit = 5
        order = self.request.get('order', 'desc')
        page = self.request.get('page', 1)
        offset = (int(page) - 1) * 5
        dudles = core.get_latest_dudles(limit=5, order=order)
        dudles = [ (d.key().id(), d ) for d in dudles ]
        dudle_ids = [ k for (k,v) in dudles ]
        dudles = dict(dudles)
        self.render_template('latest.html', dudle_ids=dudle_ids, dudles=dudles)

class DudleImage(webapp.RequestHandler):

    def get(self):
        dudle = core.get_dudle(int(self.request.get('id')))
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(dudle.image_data)


class DudleStrokes(JsonHandler):

    def get(self):
        dudle = core.get_dudle(int(self.request.get('id')))
        self.json(dudle.strokes)

class EditProfileHandler(BaseHandler):

    def get(self):
        self.render_template('profile.html')

class SaveProfileHandler(BaseHandler):

    @form('name:unicode')
    def post(self, name):
        dudlr = core.get_dudlr()
        dudlr.name = name
        dudlr.put()
        self.redirect('/')


class RatingHandler(JsonHandler):

    @form('rating:int', 'id:int')
    def post(self, rating, id):
        user = users.get_current_user()
        try:
            dudle = core.rate_dudle(id, rating * 20, user)
        except DudleException, de:
            # FIXME do something
            self.json({'status':'error', 'message':str(de)})
        else:
            self.json({'status':'ok', 'rating': dudle.rating})
        


