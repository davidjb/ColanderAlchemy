Change Log
==========

0.3 (unreleased)
----------------

- Add ``objectify`` function on ``SQLAlchemySchemaNode`` -- use this to
  recreate SQLAlchemy object instances from the configured mappers.
  This new method is the opposite of ``dictify``.
  [davidjb]


0.2 (2013-05-16)
----------------

- No changes.

0.2a1 (2012-04-09)
------------------

- Ensure relationship mapped schemas have a ``name``. This ensures
  correct usage with ``Deform``.
- Ensure missing schema node information correctly maps to SQLAlchemy
  structures.
- Map missing information for "required" relationships based upon the
  join condition. This can be further customised by given relationships
  setting ``missing=colander.required`` within their respective
  configurations.
- Read Colander node init settings for a mapped class using the
  ``__colanderalchemy__`` attribute.  This allows for full customisation
  of the resulting ``colander.Mapping`` SchemaNode. 
- Allow non-SQLAlchemy schema nodes within ``SQLAlchemySchemaNode``.
  Previously, the ``dictify`` method would throw an ``AttributeError``.
- Fix setup.py for python 3k

0.1b7 (Unreleased)
------------------

- Ensure relationships are mapped recursively and adhere to
  ColanderAlchemy settings for mappings.
- Remove dictify method in SQLAlchemyMapping.

0.1b6 (2012-10-17)
------------------

- Fix minor bugs.

0.1b5 (2012-09-19)
------------------

- Fix bug in MappingRegistry.__init__:
  pkeys is a list of property keys instead of column name
- Add support to specify schema node ordering.

0.1b4 (2012-08-06)
------------------

- Fix bug related to 'ca_include=False'.
- Change tests to cover that bug.

0.1b3 (2012-08-02)
------------------

- Fix issue related to mapped class inheritance.
- Fix minor bugs.

0.1b2 (2012-06-14)
------------------

- Added support to use ColanderAlchemy declaratively.

0.1b (2012-05-19)
-----------------

- Added SQLAlchemyMapping.dictify method.
- Updated tests with checks needed to test SQLAlchemyMapping.dictify.

0.1.0a2 (unreleased)
--------------------

- Mentioned supported Python versions in trove classifiers.
- Updated tests to run with current `colander` versions.
- Made compatible with Python 3.2.

0.1.0a (2012-03-24)
-------------------

- Initial public release.
