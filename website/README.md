# website

This app comprises models for general content of the website, several useful
mixins and blocks. Furthermore, it implements sending translated emails.

## Translation

This app contains a class ``TranslatedPage`` which
inmplements pages in two languages (english and german). All page-related
models should be derived from ``TranslatedPage``. Furthermore, it contains a
class ``TranslatedField`` which should be used to implement fields for two
languages.

## Hook for autmatically adding content

The ``add_child`` method of ``TranslatedPage`` is different from the method in
the standard ``Page`` model. It calls the methods ``after_create_hook`` of the
created instance, if available. This can be used, for example, to
automatically create sub-pages to the created instance. 
