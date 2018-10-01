from wagtail.contrib.modeladmin.helpers import PageButtonHelper
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.wagtailcore import hooks

# Register your models here.


class HiddenModelAdmin( ModelAdmin ):

    def register_with_wagtail(self):
        @hooks.register('register_permissions')
        def register_permissions():
            return self.get_permissions_for_registration()

        @hooks.register('register_admin_urls')
        def register_admin_urls():
            return self.get_admin_urls_for_registration()

        # omit the menu_hook registration

        if self.will_modify_explorer_page_queryset():
            @hooks.register('construct_explorer_page_queryset')
            def construct_explorer_page_queryset(parent_page, queryset, request):
                return self.modify_explorer_page_queryset(
                    parent_page, queryset, request)
    

class NoCopyButtonHelper( PageButtonHelper ):
    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        if exclude is None:
            exclude = ['copy']
        else:
            exclude.append('copy')
        return super(NoCopyButtonHelper, self).get_buttons_for_obj( obj, exclude, classnames_add, classnames_exclude )

class NoCopyNoDelButtonHelper( PageButtonHelper ):
    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        if exclude is None:
            exclude = ['copy', 'delete']
        else:
            exclude.append('copy', 'delete')
        return super(NoCopyNoDelButtonHelper, self).get_buttons_for_obj( obj, exclude, classnames_add, classnames_exclude )
