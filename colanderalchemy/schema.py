# types.py
# Copyright (C) 2012 the ColanderAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of ColanderAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from colander import (Mapping,
                      null,
                      required,
                      SchemaNode,
                      Sequence)
from inspect import isfunction
from sqlalchemy import (Boolean,
                        Date,
                        DateTime,
                        Enum,
                        Float,
                        inspect,
                        Integer,
                        String,
                        Numeric,
                        Time)
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm import object_mapper
import colander
import logging


__all__ = ['SQLAlchemySchemaNode']

log = logging.getLogger(__name__)


class SQLAlchemySchemaNode(colander.SchemaNode):

    """ Build a Colander Schema based on the SQLAlchemy mapped class.
    """

    sqla_info_key = 'colanderalchemy'

    def __init__(self, class_, includes=None,
                 excludes=None, overrides=None, unknown='raise'):

        log.debug('SQLAlchemySchemaNode.__init__: %s', class_)

        # The default type of this SchemaNode is Mapping.
        colander.SchemaNode.__init__(self, Mapping(unknown))
        self.class_ = class_
        self.includes = includes or {}
        self.excludes = excludes or {}
        self.overrides = overrides or {}
        self.unknown = unknown
        self.declarative_overrides = {}
        self.inspector = inspect(class_)
        self.add_nodes(self.includes, self.excludes, self.overrides)

    def add_nodes(self, includes, excludes, overrides):

        for prop in self.inspector.attrs:

            name = prop.key

            if name in excludes and name in includes:
                msg = 'excludes and includes are mutually exclusive.'
                raise ValueError(msg)

            if name in excludes or (includes and name not in includes):
                log.debug('Attribute %s skipped imperatively', name)
                continue

            try:
                getattr(self.inspector.column_attrs, name)
                factory = 'get_schema_from_column'

            except AttributeError:
                getattr(self.inspector.relationships, name)
                factory = 'get_schema_from_relationship'

            node = getattr(self, factory)(prop, overrides.get(name,{}).copy())
            if node is None:
                continue

            self.add(node)

    def get_schema_from_column(self, prop, overrides):
        """ Build and return a Colander SchemaNode
            using information stored in the column.
        """

        # The name of the SchemaNode is the ColumnProperty key.
        name = prop.key
        column = prop.columns[0]
        declarative_overrides = column.info.get(self.sqla_info_key, {}).copy()
        self.declarative_overrides[name] = declarative_overrides.copy()

        if declarative_overrides.pop('exclude', False):
            log.debug('Column %s skipped due to declarative overrides', name)
            return None

        msg = None
        key = 'name'
        if key in declarative_overrides:
            msg = 'Column %s: name cannot be overridden via info kwarg.'

        elif key in overrides:
            msg = 'Column %s: name cannot be overridden imperatively.'

        key = 'children'
        if key in declarative_overrides or key in overrides:
            msg = 'Column %s: children cannot be overridden via info kwarg.'

        elif key in overrides:
            msg = 'Column %s: children cannot be overridden imperatively.'

        if msg:
            raise ValueError(msg % name)

        # The SchemaNode built using the ColumnProperty has no children.
        children = []

        # The SchemaNode has no validator.
        validator = None

        # The type of the SchemaNode will be evaluated using the Column type.
        # User can overridden the default type via Column.info or 
        # imperatively using overrides arg in SQLAlchemySchemaNode.__init__
        # support sqlalchemy.types.TypeDecorator
        column_type = getattr(column.type, 'impl', column.type)

        imperative_type = overrides.pop('typ', None)
        declarative_type = declarative_overrides.pop('typ', None)

        if not imperative_type is None:
            type_ = imperative_type
            msg = 'Column %s: type overridden imperatively: %s.'
            log.debug(msg, name, type_)

        elif not declarative_type is None:
            type_ = declarative_type
            msg = 'Column %s: type overridden via declarative: %s.'
            log.debug(msg, name, type_)

        elif isinstance(column_type, Boolean):
            type_ = colander.Boolean()

        elif isinstance(column_type, Date):
            type_ = colander.Date()

        elif isinstance(column_type, DateTime):
            type_ = colander.DateTime()

        elif isinstance(column_type, Enum):
            type_ = colander.String()
            validator = colander.OneOf(column.type.enums)

        elif isinstance(column_type, Float):
            type_ = colander.Float()

        elif isinstance(column_type, Integer):
            type_ = colander.Integer()

        elif isinstance(column_type, String):
            type_ = colander.String()
            validator = colander.Length(0, column.type.length)

        elif isinstance(column_type, Numeric):
            type_ = colander.Decimal()

        elif isinstance(column_type, Time):
            type_ = colander.Time()

        else:
            raise NotImplementedError('Unknown type: %s' % column_type)

        # Add default values for missing parameters during serialization/deserialization.
        if column.default is None:
            default = null

        elif column.default.is_callable:
            # Fix: SQLA wraps callables in lambda ctx: fn().
            default = lambda: column.default.arg(None)

        else:
            default = column.default.arg

        if not column.nullable:
            missing = required

        elif not column.default is None and column.default.is_callable:
            # Fix: SQLA wraps default callables in lambda ctx: fn().
            missing = column.default.arg(None)

        elif not column.default is None and not column.default.is_callable:
            missing = column.default.arg

        else:
            missing = null

        kwargs = dict(name=name,
                      default=default,
                      missing=missing,
                      validator=validator)
        kwargs.update(declarative_overrides)
        kwargs.update(overrides)

        return colander.SchemaNode(type_, *children, **kwargs)

    def get_schema_from_relationship(self, prop, overrides):
        """ Build and return a Colander SchemaNode
            using information stored in the relationship property.
        """

        # The name of the SchemaNode is the ColumnProperty key.
        name = prop.key
        declarative_overrides = prop.info.get(self.sqla_info_key, {}).copy()
        self.declarative_overrides[name] = declarative_overrides.copy()

        if isfunction(prop.argument):
            class_ = prop.argument()

        else:
            class_ = prop.argument

        if declarative_overrides.pop('exclude', False):
            log.debug('Relationship %s skipped due to declarative overrides',
                      name)
            return None

        msg = None
        key = 'name'
        if key in declarative_overrides:
            msg = 'Relationship %s: name cannot be overridden via declarative.'

        elif key in overrides:
            msg = 'Relationship %s: name cannot be overridden imperatively.'

        key = 'typ'
        if key in declarative_overrides or key in overrides:
            msg = 'Relationship %s: typ cannot be overridden via declarative.'

        elif key in overrides:
            msg = 'Relationship %s: typ cannot be overridden imperatively.'

        if msg:
            raise ValueError(msg % name)

        key = 'children'
        imperative_children = overrides.pop(key, None)
        declarative_children = declarative_overrides.pop(key, None)

        if not imperative_children is None:
            children = imperative_children
            msg = 'Relationship %s: %s overridden imperatively.'
            log.debug(msg, name, key)

        elif not declarative_children is None:
            children = declarative_children
            msg = 'Relationship %s: %s overridden via declarative.'
            log.debug(msg, name, key)

        else:
            children = []

        key = 'includes'
        imperative_includes = overrides.pop(key, None)
        declarative_includes = declarative_overrides.pop(key, None)

        if not imperative_includes is None:
            includes = imperative_includes
            msg = 'Relationship %s: %s overridden imperatively.'
            log.debug(msg, name, key)

        elif not declarative_includes is None:
            includes = declarative_includes
            msg = 'Relationship %s: %s overridden via declarative.'
            log.debug(msg, name, key)

        else:
            includes = [p.key for p in inspect(class_).column_attrs]

        key = 'excludes'
        imperative_excludes = overrides.pop(key, None)
        declarative_excludes = declarative_overrides.pop(key, None)

        if not imperative_excludes is None:
            excludes = imperative_excludes
            msg = 'Relationship %s: %s overridden imperatively.'
            log.debug(msg, name, key)

        elif not declarative_excludes is None:
            excludes = declarative_excludes
            msg = 'Relationship %s: %s overridden via declarative.'
            log.debug(msg, name, key)

        else:
            excludes = None

        key = 'overrides'
        imperative_rel_overrides = overrides.pop(key, None)
        declarative_rel_overrides = declarative_overrides.pop(key, None)

        if not imperative_rel_overrides is None:
            rel_overrides = imperative_rel_overrides
            msg = 'Relationship %s: %s overridden imperatively.'
            log.debug(msg, name, key)

        elif not declarative_rel_overrides is None:
            rel_overrides = declarative_rel_overrides
            msg = 'Relationship %s: %s overridden via declarative.'
            log.debug(msg, name, key)

        else:
            rel_overrides = None

        kwargs = dict(name=name)
        kwargs.update(declarative_overrides)
        kwargs.update(overrides)

        if children and prop.uselist:
            # xToMany relationships.
            return SchemaNode(Sequence(), *children, **kwargs)

        if children and not prop.uselist:
            # xToOne relationships.
            return SchemaNode(Mapping(), *children, **kwargs)

        node = SQLAlchemySchemaNode(class_,
                                    includes=includes,
                                    excludes=excludes,
                                    overrides=rel_overrides)

        if prop.uselist:
            return SchemaNode(Sequence(), node, **kwargs)

        node.name = name

        return node

    def dictify(self, obj):
        """ Build and return a dictified version of `obj`
            using schema information to choose what attributes
            will be included in the returned dict.
        """

        dict_ = OrderedDict()
        for name in self._reg.attrs:

            if (name in self._reg.excludes and self._reg.excludes[name]) or\
               (self._reg.includes and name not in self._reg.includes):
                continue

            if name in self._reg.fields:
                dict_[name] = getattr(obj, name)

            elif name in self._reg.references:
                value = getattr(obj, name)
                if not value is None:
                    value = self.dictify_relationship(value)
                dict_[name] = value

            elif name in self._reg.collections:
                dict_[name] = [self.dictify_relationship(value)
                               for value in getattr(obj, name)]

        return dict_

    def dictify_relationship(self, obj):
        dict_ = {}
        for col in object_mapper(obj).primary_key:
            dict_[col.name] = getattr(obj, col.name)
        return dict_

    def clone(self):
        cloned = self.__class__(self.class_,
                                self.includes,
                                self.excludes,
                                self.overrides,
                                self.unknown)
        cloned.__dict__.update(self.__dict__)
        cloned.children = [node.clone() for node in self.children]
        return cloned