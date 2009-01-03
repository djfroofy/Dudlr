import logging
import math

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
        context['request'] = self.request
        if user is None:
            context['login_url'] = users.create_login_url(self.request.url)
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

    @form('id:int', 'data:str', 'width:int', 'height:int', 'public:str', 'anon:str')
    def post(self, id, data, width, height, public, anon):
        logging.info('public = ' + public)
        public = public == 'true'
        logging.info('public = ' + str(public))
        logging.info('anon = ' + anon)
        anon = anon == 'true'
        logging.info('anon = ' + str(anon))
        core.update_dudle_strokes(id, data)
        core.finalize_dudle_strokes(id, public, anon)
        self.json('ok')

class ViewDudleHandler(BaseHandler):

    def get(self):
        order = 'desc'
        page = int(self.request.get('page', 1))
        offset = (page - 1) * 5
        dudles, count = core.get_latest_dudles(limit=5, order=order, offset=offset)
        dudles = [ (d.key().id(), d ) for d in dudles ]
        dudle_ids = [ k for (k,v) in dudles ]
        dudles = dict(dudles)
        self.render_template('latest.html',
                dudle_ids=dudle_ids,
                dudles=dudles, artist=False,
                page=page, pages=int(math.ceil(count/5.)))

class TopRatedDudleHandler(BaseHandler):

    def get(self):
        page = int(self.request.get('page', 1))
        offset = (page - 1) * 5
        dudles, count = core.get_toprated_dudles(limit=5, offset=offset)
        dudles = [ (d.key().id(), d ) for d in dudles ]
        dudle_ids = [ k for (k,v) in dudles ]
        dudles = dict(dudles)
        logging.info('got dudles : %d' % len(dudles))
        self.render_template('latest.html',
                dudle_ids=dudle_ids,
                dudles=dudles, artist=False,
                page=page, pages=int(math.ceil(count/5.)))

class DudlrGalleryHandler(BaseHandler):

    def get(self):
        order = 'desc'
        id = int(self.request.path.split('/')[-1])
        logging.info('artist : %d' % id)
        page = int(self.request.get('page', 1))
        offset = (page - 1) * 5
        artist = core.get_dudlr_by_id(id)
        dudles, count = core.get_gallery(artist, users.get_current_user(), limit=5, offset=offset)
        dudles = [ (d.key().id(), d ) for d in dudles ]
        dudle_ids = [ k for (k,v) in dudles ]
        dudles = dict(dudles)
        self.render_template('latest.html',
                dudle_ids=dudle_ids, dudles=dudles, artist=artist,
                page=page, pages=int(math.ceil(count/5.)))


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
        error = self.request.get('error')
        if error:
            self.render_template('profile.html', error=error,
                    name=self.request.get('name'))
        else:
            self.render_template('profile.html')

class SaveProfileHandler(BaseHandler):

    @form('name:unicode')
    def post(self, name):
        name = u' '.join(name.split())
        if len(name) > 32:
            self.redirect('/profile/edit?error=3&name=%s' % name)
            return
        user = users.get_current_user()
        try:
            core.set_dudlr_name(user, name)
        except DudleException, de:
            code = { core.ERROR_DUDLR_NAME_FROZEN: 1,
                     core.ERROR_DUDLR_NAME_TAKEN: 2 }[de.message]
            self.redirect('/profile/edit?error=%d&name=%s' % (code, name))
        else:
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
        


