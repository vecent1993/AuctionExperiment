# -*- coding: utf-8 -*-
"""This module contains all self defined Errors and Exceptions.

"""


class Error(Exception):
    def __init__(self, value):
        """Base ERROR.

        :param value: str of error description.
        :return:
        """
        self.value = value

    def __str__(self):
        return repr(self.value)
