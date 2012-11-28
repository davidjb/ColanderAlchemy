# declarative.py
# Copyright (C) 2012 the ColanderAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of ColanderAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import sqlalchemy.schema
import sqlalchemy.ext.declarative

__all__ = ['Column', 'relationship']


class Column(sqlalchemy.schema.Column):
    """Drop-in for ``sqlachemy.schema.Column`` for use with ColanderAlchemy.

    This class extends the basic ``Column`` by allowing :ref:`keyword
    arguments <ca-keyword-arguments>` to be specified during creation to
    customize the resulting ``Colander`` schema after mapping.
    """

    def __init__(self, *args, **kwargs):

        self._ca_registry = {}

        for key in kwargs.keys():
            if key[:3] == 'ca_':
                value = kwargs.pop(key)
            else:
                continue

            self._ca_registry[key[3:]] = value

        super(Column, self).__init__(*args, **kwargs)

    @property
    def ca_registry(self):
        return self._ca_registry

    def copy(self, **kwargs):
        col = super(Column, self).copy(**kwargs)
        col._ca_registry = self._ca_registry.copy()
        return col


def relationship(argument, secondary=None, **kwargs):
    """Drop-in for ``sqlachemy.orm.relationship`` to use with ColanderAlchemy

    This function wraps the basic ``relationship`` by allowing :ref:`keyword
    arguments <ca-keyword-arguments>` to be specified during creation to
    customize the resulting ``Colander`` schema after mapping.
    """

    registry = {}

    for key in kwargs.keys():
        print key
        if key[:3] == 'ca_':
            value = kwargs.pop(key)
        else:
            continue

        registry[key[3:]] = value

    relationship = sqlalchemy.orm.relationship(argument, secondary, **kwargs)
    relationship.ca_registry = registry
    return relationship
