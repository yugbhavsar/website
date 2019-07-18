import datetime



from django.contrib.admin.utils import quote
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.urls import reverse

from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.core.models import Site

class AttendeeButtonHelper (ButtonHelper):
    delete_from_waitlist_button_classnames = []
    payed_button_classnames = []
    add_to_course_button_classnames = []


    def __init__( self, view, request, modeladmin = None ):
        self.view = view
        self.request = request
        if modeladmin:
            self.model = modeladmin.model
            self.permission_helper = modeladmin.permission_helper
            self.url_helper = modeladmin.url_helper
            self.verbose_name = modeladmin.model.display_name
        else:
            self.model = view.model
            self.permission_helper = view.permission_helper
            self.url_helper = view.url_helper

        
        self.opts = self.model._meta
        self.verbose_name = force_text(self.opts.verbose_name)
        self.verbose_name_plural = force_text(self.opts.verbose_name_plural)
        
    def get_next( self, action = 'inspect' ):
        if hasattr(self.view, 'instance'):
            opts = self.view.instance.__class__._meta        
            nxt = '?next='+reverse(
                '%s_%s_modeladmin_%s' % (opts.app_label, opts.model_name, action),
                args = [quote(self.view.instance.id)]
            )
        else:
            nxt = ''
        return nxt

        

    def edit_button(self, pk, classnames_add=None, classnames_exclude = None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        opts = self.obj.__class__._meta

        return {
            'url': reverse(
                '%s_%s_modeladmin_%s' % (opts.app_label, opts.model_name, 'edit'),
                args=[quote(pk)]
            )+self.get_next(),
            'label': _('Edit' ),
            'classname': cn,
            'title': _('Edit %s, %s') % (self.obj.last_name, self.obj.first_name)
        }

    def delete_button(self, pk, classnames_add=None, classnames_exclude = None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        opts = self.obj.__class__._meta
        return {
            'url': reverse(
                '%s_%s_modeladmin_%s' % (opts.app_label, opts.model_name, 'delete'),
                args=[quote(pk)]
            ),
            'label': _('Delete' ),
            'classname': cn,
            'title': _('Delete %s, %s') % (self.obj.last_name, self.obj.first_name)
        }

    def delete_from_waitlist_button(self, pk, classnames_add=None, classnames_exclude = None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        
        return {
            'url': self.url_helper.get_action_url('delete', quote(pk)),
            'label': _('Delete from waitlist'),
            'classname': cn,
            'title': _('Delete %s, %s from waiting list') % (self.obj.last_name, self.obj.first_name)
        }



    def has_payed_button(self, obj, classnames_add=None, classnames_exclude = None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.payed_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': reverse(
                'coursesadmin:haspayed', 
                args=[obj.id, self.view.instance.id]
            )+self.get_next(),
            'label': _('Has payed'),
            'classname': cn,
            'title': _('Mark as payed')
        }

    def add_to_course_button(self, pk, classnames_add=None, classnames_exclude = None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.add_to_course_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        
        return {
            'url': reverse('coursesadmin:add2course', args=[pk, self.view.instance.id])+self.get_next(),
            'label': _('Add to course'),
            'classname': cn,
            'title': _('Add %s, %s to course') %  (self.obj.last_name, self.obj.first_name)
        }


    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        
        self.obj = obj
        btns = super(AttendeeButtonHelper, self).get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude)

        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        if not hasattr(self.view, 'instance'):
            exclude.append('add_to_course')
            exclude.append('has_payed')

        pk = getattr(obj, self.opts.pk.attname)
        if 'delete_from_waitlist' not in exclude:
            if obj.waitlist_course:
                btns.append(
                    self.delete_from_waitlist_button(pk, classnames_add, classnames_exclude)
                )
        if 'add_to_course' not in exclude:
            btns.append(
                self.add_to_course_button(obj.courseattendee_ptr_id, classnames_add, classnames_exclude)
            )
        if 'has_payed' not in exclude:
            if hasattr(obj, 'payed'):
                if not obj.payed:
                    btns.append(
                        self.has_payed_button(obj, classnames_add, classnames_exclude)
                    )
        return btns


def get_next_invoice_number():
    from .models import CourseSettings
    settings = CourseSettings.for_site(
        Site.objects.filter(is_default_site = True).first()
    )

    this_year = datetime.date.today().year
    
    if settings.invoice_counter_year == this_year:
        settings.invoice_counter = settings.invoice_counter + 1
    else:
        settings.invoice_counter_year = this_year
        settings.invoice_counter = 1
        
    settings.save()
    return "{}-{:05d}-".format(
        settings.invoice_counter_year, 
        settings.invoice_counter
    )
