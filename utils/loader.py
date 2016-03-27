# -*- coding: utf-8 -*-
"""This module contains multiple directories template loader
based on tornado's base loader.

Usage:
template_dirs = (
    'handler/thandler/template',
)

loader = MultiDirLoader(template_dirs)
loader.add_dir('handler/phandler/template')
"""
from tornado.template import Loader


class MultiDirLoader(object):
    def __init__(self, template_dirs=[]):
        """Multiple directories template loader

        :param template_dirs: list of templates directories.
        :return:
        """
        self._loaders = dict()
        self._templates = dict()

        for template_dir in template_dirs:
            self.add_dir(template_dir)

    def add_dir(self, template_dir):
        """Add new template directory to loader

        :param template_dir: str of template directory.
        :return:
        """
        if template_dir in self._loaders:
            return
        self._loaders[template_dir] = Loader(template_dir)

    def load(self, name):
        """Loader template.

        :param name: str of template file name.
        :return:
        """
        if name not in self._templates:
            self._load_template(name)
        return self._templates[name]

    def _load_template(self, name):
        for template_dir in self._loaders:
            try:
                template = self._loaders[template_dir].load(name)
                self._templates[name] = template
                return
            except IOError, e:
                pass

        raise IOError('template "{}" not found'.format(name))
