# -*- coding: utf-8 -*-
"""
    jinja2.loaders
    ~~~~~~~~~~~~~~

    Jinja loader classes.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from os import path
from jinja2.exceptions import TemplateNotFound
from jinja2.utils import LRUCache

import logging

def split_template_path(template):
    """Split a path into segments and perform a sanity check.  If it detects
    '..' in the path it will raise a `TemplateNotFound` error.
    """
    pieces = []
    for piece in template.split('/'):
        if path.sep in piece \
           or (path.altsep and path.altsep in piece) or \
           piece == path.pardir:
            raise TemplateNotFound(template)
        elif piece and piece != '.':
            pieces.append(piece)
    return pieces


class BaseLoader(object):
    """Baseclass for all loaders.  Subclass this and override `get_source` to
    implement a custom loading mechanism.  The environment provides a
    `get_template` method that calls the loader's `load` method to get the
    :class:`Template` object.

    A very basic example for a loader that looks up templates on the file
    system could look like this::

        from jinja2 import BaseLoader, TemplateNotFound
        from os.path import join, exists, getmtime

        class MyLoader(BaseLoader):

            def __init__(self, path, cache_size=50, auto_reload=True):
                BaseLoader.__init__(self, cache_size, auto_reload)
                self.path = path

            def get_source(self, environment, template):
                path = join(self.path, template)
                if not exists(path):
                    raise TemplateNotFound(template)
                mtime = getmtime(path)
                with file(path) as f:
                    source = f.read().decode('utf-8')
                return source, path, lambda: mtime == getmtime(path)
    """

    def get_source(self, environment, template):
        """Get the template source, filename and reload helper for a template.
        It's passed the environment and template name and has to return a
        tuple in the form ``(source, filename, uptodate)`` or raise a
        `TemplateNotFound` error if it can't locate the template.

        The source part of the returned tuple must be the source of the
        template as unicode string or a ASCII bytestring.  The filename should
        be the name of the file on the filesystem if it was loaded from there,
        otherwise `None`.  The filename is used by python for the tracebacks
        if no loader extension is used.

        The last item in the tuple is the `uptodate` function.  If auto
        reloading is enabled it's always called to check if the template
        changed.  No arguments are passed so the function must store the
        old state somewhere (for example in a closure).  If it returns `False`
        the template will be reloaded.
        """
        raise TemplateNotFound(template)

    def load(self, environment, name, globals=None):
        """Loads a template.  This method looks up the template in the cache
        or loads one by calling :meth:`get_source`.  Subclasses should not
        override this method as loaders working on collections of other
        loaders (such as :class:`PrefixLoader` or :class:`ChoiceLoader`)
        will not call this method but `get_source` directly.
        """
        if globals is None:
            globals = {}
        source, filename, uptodate = self.get_source(environment, name)
        code = environment.compile(source, name, filename)
        return environment.template_class.from_code(environment, code,
                                                    globals, uptodate)


class FileSystemLoader(BaseLoader):
    """Loads templates from the file system.  This loader can find templates
    in folders on the file system and is the preferred way to load them.

    The loader takes the path to the templates as string, or if multiple
    locations are wanted a list of them which is then looked up in the
    given order:

    >>> loader = FileSystemLoader('/path/to/templates')
    >>> loader = FileSystemLoader(['/path/to/templates', '/other/path'])

    Per default the template encoding is ``'utf-8'`` which can be changed
    by setting the `encoding` parameter to something else.
    """

    def __init__(self, searchpath, encoding='utf-8'):
        if isinstance(searchpath, basestring):
            searchpath = [searchpath]
        self.searchpath = list(searchpath)
        self.encoding = encoding

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        for searchpath in self.searchpath:
            filename = path.join(searchpath, *pieces)
            #if not path.isfile(filename):
            #    logging.info('not a file')
            #    continue
            f = file(filename)
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()
            old = path.getmtime(filename)
            return contents, filename, lambda: path.getmtime(filename) == old
        raise TemplateNotFound(template)


class PackageLoader(BaseLoader):
    """Load templates from python eggs or packages.  It is constructed with
    the name of the python package and the path to the templates in that
    package:

    >>> loader = PackageLoader('mypackage', 'views')

    If the package path is not given, ``'templates'`` is assumed.

    Per default the template encoding is ``'utf-8'`` which can be changed
    by setting the `encoding` parameter to something else.  Due to the nature
    of eggs it's only possible to reload templates if the package was loaded
    from the file system and not a zip file.
    """

    def __init__(self, package_name, package_path='templates',
                 encoding='utf-8'):
        from pkg_resources import DefaultProvider, ResourceManager, get_provider
        provider = get_provider(package_name)
        self.encoding = encoding
        self.manager = ResourceManager()
        self.filesystem_bound = isinstance(provider, DefaultProvider)
        self.provider = provider
        self.package_path = package_path

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        p = '/'.join((self.package_path,) + tuple(pieces))
        if not self.provider.has_resource(p):
            raise TemplateNotFound(template)

        filename = uptodate = None
        if self.filesystem_bound:
            filename = self.provider.get_resource_filename(self.manager, p)
            mtime = path.getmtime(filename)
            def uptodate():
                return path.getmtime(filename) == mtime

        source = self.provider.get_resource_string(self.manager, p)
        return source.decode(self.encoding), filename, uptodate


class DictLoader(BaseLoader):
    """Loads a template from a python dict.  It's passed a dict of unicode
    strings bound to template names.  This loader is useful for unittesting:

    >>> loader = DictLoader({'index.html': 'source here'})

    Because auto reloading is rarely useful this is disabled per default.
    """

    def __init__(self, mapping):
        self.mapping = mapping

    def get_source(self, environment, template):
        if template in self.mapping:
            source = self.mapping[template]
            return source, None, lambda: source != self.mapping[template]
        raise TemplateNotFound(template)


class FunctionLoader(BaseLoader):
    """A loader that is passed a function which does the loading.  The
    function becomes the name of the template passed and has to return either
    an unicode string with the template source, a tuple in the form ``(source,
    filename, uptodatefunc)`` or `None` if the template does not exist.

    >>> def load_template(name):
    ...     if name == 'index.html'
    ...         return '...'
    ...
    >>> loader = FunctionLoader(load_template)

    The `uptodatefunc` is a function that is called if autoreload is enabled
    and has to return `True` if the template is still up to date.  For more
    details have a look at :meth:`BaseLoader.get_source` which has the same
    return value.
    """

    def __init__(self, load_func):
        self.load_func = load_func

    def get_source(self, environment, template):
        rv = self.load_func(template)
        if rv is None:
            raise TemplateNotFound(template)
        elif isinstance(rv, basestring):
            return rv, None, None
        return rv


class PrefixLoader(BaseLoader):
    """A loader that is passed a dict of loaders where each loader is bound
    to a prefix.  The prefix is delimited from the template by a slash per
    default, which can be changed by setting the `delimiter` argument to
    something else.

    >>> loader = PrefixLoader({
    ...     'app1':     PackageLoader('mypackage.app1'),
    ...     'app2':     PackageLoader('mypackage.app2')
    ... })

    By loading ``'app1/index.html'`` the file from the app1 package is loaded,
    by loading ``'app2/index.html'`` the file from the second.
    """

    def __init__(self, mapping, delimiter='/'):
        self.mapping = mapping
        self.delimiter = delimiter

    def get_source(self, environment, template):
        try:
            prefix, template = template.split(self.delimiter, 1)
            loader = self.mapping[prefix]
        except (ValueError, KeyError):
            raise TemplateNotFound(template)
        return loader.get_source(environment, template)


class ChoiceLoader(BaseLoader):
    """This loader works like the `PrefixLoader` just that no prefix is
    specified.  If a template could not be found by one loader the next one
    is tried.

    >>> loader = ChoiceLoader([
    ...     FileSystemLoader('/path/to/user/templates'),
    ...     PackageLoader('myapplication')
    ... ])

    This is useful if you want to allow users to override builtin templates
    from a different location.
    """

    def __init__(self, loaders):
        self.loaders = loaders

    def get_source(self, environment, template):
        for loader in self.loaders:
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(template)
