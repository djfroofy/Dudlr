import os

from jinja2 import Environment, FileSystemLoader
from jinja2 import tests

def test_gt(n, other):
    return n > other

tests.TESTS.update({
    'gt' : test_gt
})


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH),
                        autoescape=True, trim_blocks=True)


def form(*names):
    spec = []
    for name in names:
        parts = name.split(':')
        if len(parts) == 2:
            spec.append((parts[0], eval(parts[1])))
        else:
            spec.append((parts[0], str))
    def _wrapper(m):
        def _wrapper2(self):
            d = {}
            for (name, cast) in spec:
                d[name] = cast(self.request.get(name))
            m(self, **d)
        _wrapper2.__name__ = m.__name__
        _wrapper2.__doc__ = m.__doc__
        return _wrapper2
    return _wrapper



def render_template(request, template, **context):
#    context['user'] = user = users.get_current_user()
#    context['dudlr'] = core.get_dudlr(user)
    context['request'] = request
#    if user is None:
#        context['login_url'] = users.create_login_url(self.request.url)
#    else:
#        context['logout_url'] = users.create_logout_url('/')
    return jinja_env.get_template(template).render(**context)
