import logging

from django.utils import simplejson
from google.appengine.ext import webapp


from dudlr import core
from dudlr.utils import jinja_env, form

class TemplateRequestHandler(webapp.RequestHandler):

    def render_template(self, template, headers=None, **context):
        self.response.headers['Content-Type'] = 'text/html'
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
        logging.info('data[0] = ' + data[0])
        core.update_dudle_strokes(id, data)
        core.finalize_dudle_strokes(id)
        self.json('ok')

class ViewDudleHandler(BaseHandler):

    def get(self):
        limit = self.request.get('limit', '1')
        order = self.request.get('order', 'desc')
        dudles = core.get_latest_dudles(limit=int(limit), order=order)
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

