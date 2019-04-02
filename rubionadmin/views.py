from .forms import  InstrumentBookingForm, MethodBookingForm, RejectionForm

import datetime 

from dateutil.relativedelta import relativedelta

from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Template, Context
from django.utils.translation import ugettext as _
from django.utils.translation import override as override_lang
from django.views.generic.base import View

import io


from instruments.models import (
    InstrumentPage, InstrumentByProjectBooking, 
    MethodsByProjectBooking
)
from instruments.mixins import get_bookings_for

from notifications.models import CentralRadiationSafetyDataSubmission

import re
from rubion.utils import iso_to_gregorian

from userinput.models import Project, WorkGroup, RUBIONUser
from userdata.models import StaffUser
import userdata.safety_instructions as SI

from wagtail.admin import messages
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core.models import PageRevision, UserPagePermissionsProxy

from website.models import EMailText, is_beirat
from website.utils import send_mail

import xlsxwriter

def approve_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')

    if request.method == 'POST':
        revision.approve_moderation()
        
        page = revision.page.specific
        page.go_live_at = datetime.datetime.now()


        r_user = RUBIONUser.objects.get(linked_user = revision.user_id)
        
        if isinstance(page, WorkGroup):
            success_text = _('Workgroup {0} approved.')
            mail_text_id = 'Workgroup.approved'
            context = {
                'workgroup' : page
            }

            try:
                user_revision = PageRevision.objects.filter(page = r_user).filter(submitted_for_moderation = True).first()
                user_revision.approve_moderation()
            except:
                pass
        else:
            page.expire_at = page.go_live_at + relativedelta(years = 1)
            success_text = _('Project {0} approved.')
            mail_text_id = 'Project.approved'
            context = {
                'project' : page
            }

        page.save()
        context['user'] = r_user
        context['full_user_name_de'] = r_user.full_name( language = 'de')
        context['full_user_name_en'] = r_user.full_name( language = 'en')

        messages.success(request, success_text.format(revision.page.get_admin_display_title()), buttons=[
            messages.button(revision.page.url, _('View live'), new_window=True),
            messages.button(reverse('wagtailadmin_pages:edit', args=(revision.page.id,)), _('Edit'))
        ])

        mail = EMailText.objects.get( identifier = mail_text_id )

        mail.send( r_user.email, context, lang = r_user.preferred_language )

    return redirect('wagtailadmin_home')


def reject_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)

    if request.method == 'POST':
        revision.reject_moderation()

        if not send_notification(revision.id, 'rejected', request.user.pk):
            messages.error(request, _("Failed to send rejection notifications"))

    return redirect('wagtailadmin_home')

def reject_moderation_form( request, revision_id ):

    # --- Helper functions

    def prepare_mail_texts(mail_text, user, page):
        # This is a slightly awkward treatment. We 
        # split the mail's text template at {{reasons}} (no spaces!)
        # and render an intro and a footer.
        #
        # reasons will be provided by the user

        template_intro_de, template_footer_de = mail_text.text_de.split('{{reasons}}')
        template_intro_en, template_footer_en = mail_text.text_en.split('{{reasons}}')

        tpl_intro_de = Template(template_intro_de)
        tpl_intro_en = Template(template_intro_en)
        tpl_footer_de = Template(template_footer_de)
        tpl_footer_en = Template(template_footer_en)
         
        context_de = Context( 
            {
                'user' : {'female': user.sex == RUBIONUser.FEMALE}, 
                'full_user_name' : user.full_name('de'),
                'project' : page,
                'workgroup' : page
            }
        ) 
        context_en = Context( 
            {
                'user' : {'female': user.sex == RUBIONUser.FEMALE}, 
                'full_user_name' : user.full_name('en'),
                'project' : page,
                'workgroup' : page
            }
        ) 

        de = {
            'intro':  tpl_intro_de.render( context = context_de ),
            'footer': tpl_footer_de.render( context = context_de )
        }
        en = {
            'intro':  tpl_intro_en.render( context = context_en ),
            'footer': tpl_footer_en.render( context = context_en )
        }

        return [de, en]

    def compose_and_send_mail(email, send_de = False, send_en = False, de = {}, en = {}):
        # Slightly annoying: Check if we send in two languages 
        # and compose and send the mail

        subject_sep = ' | '
        body_sep = '\n----------------------------------------------------------------------\n'
        
        two_langs = send_de and send_en
        
        if two_langs:
            subject = '{}{}{}'.format(de['subject'], subject_sep, en['subject'])
            body = '[english text below]\n\n{}{}{}'.format(de['body'], body_sep, en[body])
        elif send_de:
            subject = de['subject']
            body = de['body']
        else:
            subject = en['subject']
            body = en['body']
        send_mail(
            user.email,
            subject,
            body
        )

    def reject_item( revision ):
        revision.reject_moderation()
        page = revision.page

        if isinstance(page, WorkGroup):
            # delete the RUBIONUser instance and the website user.
            r_user = RUBIONUser.objects.get(linked_user = revision.user_id)
            user = r_user.linked_user
            r_user.delete()
            user.delete()
        page.delete()

    # --- Start of the function body

    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    page = revision.page.specific
    mail_text_obj = None
    model_str = ''
    if isinstance(page, Project):
        mail_text_obj = EMailText.objects.get(identifier = 'Project.rejected')
        model_str = 'project'

    if isinstance(page, WorkGroup):
        mail_text_obj = EMailText.objects.get(identifier = 'Workgroup.rejected')
        model_str = 'workgroup'

    if not revision.submitted_for_moderation:
        messages.error(request, _("The {0} '{1}' is not currently awaiting approval.").format(model_str, revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')


    user = RUBIONUser.objects.get(linked_user = revision.user_id)

    de, en = prepare_mail_texts( mail_text_obj, user, page )
    subject_en = mail_text_obj.subject_en
    subject_de = mail_text_obj.subject_de

    if request.method == 'GET':
        form = RejectionForm()
        
    if request.method == 'POST':
        form = RejectionForm( request.POST )
        if form.is_valid():
            compose_and_send_mail(
                user.email,
                send_de = form.send_de,
                send_en = form.send_en,
                de = {
                    'subject' : subject_de,
                    'body' : '{}{}{}'.format(
                        de['intro'], 
                        form.cleaned_data['reasons_de'],
                        de['footer']
                    )
                },
                en = {
                    'subject' : subject_en,
                    'body' : '{}{}{}'.format(
                        en['intro'], 
                        form.cleaned_data['reasons_en'],
                        en['footer']
                    )
                }
            )
            title = revision.page.get_admin_display_title()
            reject_item( revision )
            messages.success(request, _("Page '{0}' rejected for publication.").format(title))
            return render_modal_workflow(request, '', 'rubionadmin/rejection_form_success.js', {})

    return render_modal_workflow(request, 'rubionadmin/rejection_form.html', 'rubionadmin/rejection_form.js', {
        'revision':  revision,
        'page':      page,
        'lang' : user.preferred_language,
        'intro_de' : de['intro'],
        'intro_en' : en['intro'],
        'footer_de' : de['footer'],
        'footer_en' : en['footer'],
        'form' : form
    })
    


def instrument_cal ( request, request_id, year = None, week = None, method_booking_id = None ):
    weeks_to_show = 2

    now = datetime.datetime.now()
    if year is None:
        year = now.year
    else:
        year = int(year)
    if week is None:
        week = now.isocalendar()[1]
    else:
        week = int(week)

    booking = InstrumentByProjectBooking.objects.get( id = request_id )
    instrument = booking.instrument

    cal_start = iso_to_gregorian(year, week-1, 7)
    cal_end = iso_to_gregorian(year, week+2, 6)

    booked = get_bookings_for( instrument, cal_start, cal_end )

    def instrument_cal__get( form = None ):
        if form is None:
            form = InstrumentBookingForm( method_booking_id = method_booking_id)

        return render_modal_workflow(
            request, 
            'rubionadmin/instrument_cal_form.html', 
            'rubionadmin/instrument_cal_form.js', 
            {
                'instrument' : instrument,
                'form' : form,
                'bookings' : booked,
                'week' : week,
                'weeks' : range(week, week + weeks_to_show),
                'nextweek' : week + weeks_to_show,
                'prevweek' : week - weeks_to_show,
                'year': year,
                'booking':booking
            }
        )

    def instrument_cal__post( ):
        form = InstrumentBookingForm( request.POST, method_booking_id = method_booking_id )
        
        if form.is_valid():
            booking.start = form.cleaned_data['start']
            booking.end = form.cleaned_data['end']
            booking.save()
            # @TODO Send e-mail to booker
            # @TODO Send message to current user
            return render_modal_workflow(
                request,
                '',
                'rubionadmin/rejection_form_success.js',
                {}
            )
        else:
            return instrument_cal__get( form = form )

    if request.method=='GET' or method_booking_id:
        return instrument_cal__get()
    if request.method=='POST':
        return instrument_cal__post()
        

def method_cal ( request, booking_id ):
    
    booking = MethodsByProjectBooking.objects.get( id = booking_id )
    method = booking.method
    instruments = method.get_instruments()

    def method_cal__get( form = None ):
        if form is None:
            form = MethodBookingForm( instruments = instruments )

        return render_modal_workflow(
            request, 
            'rubionadmin/method_cal_form.html', 
            'rubionadmin/method_cal_form.js', 
            {
                'form' : form,
                'booking':booking
            }
        )

    def method_cal__post():
        form =  MethodBookingForm( request.POST, instruments = instruments )
        if form.is_valid():
            # @TODO This leads to booking requests for instruments if cancelled.
            # There might be a better solution for this.

            inst = [ i for i in instruments if str(i.id) == form.cleaned_data['instrument'] ]

            instrument_booking = InstrumentByProjectBooking()
            instrument_booking.project = booking.project;
            instrument_booking.instrument = inst[0];
            instrument_booking.booked_by = booking.booked_by
            instrument_booking.save()

            booking.instrument_booking = instrument_booking
            booking.save()

            return instrument_cal( request, instrument_booking.id, method_booking_id = booking_id )
        else:
            return method_cal__get( form = form )
        


    if request.method == 'GET':
        return method_cal__get()
    if request.method == 'POST':
        return method_cal__post()

def method_done ( request, booking_id ):
    if not request.user.has_perm('instruments.add_MethodsByProjectBooking'):
        raise PermissionDenied
    booking = MethodsByProjectBooking.objects.get( id = booking_id)
    booking.start = datetime.datetime.now()
    booking.save()
    return redirect('wagtailadmin_home')

def user_keys_reject( request, user_id ):

    r_user = RUBIONUser.objects.get( id = user_id )
    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(r_user).can_edit():
        raise PermissionDenied

    r_user.needs_key = False
    r_user.save_revision_and_publish( user = request.user )
    messages.success(request, _('The application for a key for {} was rejected.').format( r_user.full_name() ))
    return redirect('wagtailadmin_home')

def user_keys_accept( request, user_id ):


    r_user = RUBIONUser.objects.get( id = user_id )
    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(r_user).can_edit():
        raise PermissionDenied

    num = request.POST.get('keyId', None)
    if num:
        r_user.key_number = num
        r_user.save_revision_and_publish( user = request.user )
    
        messages.success(request, _('{} now was assigned the key with number {}.').format( r_user.full_name(), r_user.key_number ))
        return JsonResponse({'redirect' : reverse('wagtailadmin_home')})
    else:
        return JsonResponse({'wrong' : 'Did not receive a keyId'})

def user_inititally_seen( request, user_id ):
    if not request.user.has_perm('userinput.edit_RUBIONUser'):
        raise PermissionDenied

    r_user = RUBIONUser.objects.get( id = user_id )
    r_user.initially_seen = true
    r_user.save_revision_and_publish( user = request.user )
    messages.success(request, _('The application for a key for {} was rejected.').format( r_user.full_name() ))
    return redirect('wagtailadmin_home')



def full_xls_list( request ):


    # create an output stream
    output = io.BytesIO()


    # create an excel file
    wb = xlsxwriter.workbook.Workbook(output)
    # ... with bold as format
    bold = wb.add_format({'bold': True})
    textwrap = wb.add_format()
    textwrap.set_text_wrap()

    # add a worksheet
    ws = wb.add_worksheet()

    widths = {}

    def w_write( row, col, content, fmt = None ):
        if content:
            if fmt:
                ws.write(row, col, str(content), fmt)
            else:
                ws.write(row, col, str(content))

        if content:

            try:
                if widths[col] < len(str(content)):
                    widths[col] = len(str(content))
            except KeyError:
                widths[col] = len(str(content))


    HEADROW = 1

    # Pseudo-constants as for columns
    NAME = 0
    w_write(HEADROW,NAME,'Name', bold)

    VORNAME = 1
    w_write(HEADROW,VORNAME,'Vorname', bold)

    TITEL = 2
    w_write(HEADROW,TITEL,'Titel', bold)
    
    NI = 3
    w_write(HEADROW,NI,'NI', bold)

    NT = 4
    w_write(HEADROW,NT,'NT', bold)

    STED = 5
    w_write(HEADROW,STED,'Mikroskopie', bold)

    UNIVERSITAET = 7
    w_write(HEADROW,UNIVERSITAET,'Universität', bold)

    INSTITUT = 6
    w_write(HEADROW,INSTITUT,'Institut', bold)

    NUTZER = 11
    w_write(HEADROW,NUTZER,'Nutzer', bold)

    MITARBEITER = 10
    w_write(HEADROW,MITARBEITER,'Mitarbeiter', bold)

    LEITUNG = 12
    w_write(HEADROW,LEITUNG,'AG-Leiter', bold)

    ARBEITSGRUPPE = 8
    w_write(HEADROW,ARBEITSGRUPPE,'Arbeitsgruppe', bold)

    AGLEITER = 9
    w_write(HEADROW,AGLEITER,'Leitung der Arbeitsgruppe', bold)

    BEIRAT = 13
    w_write(HEADROW,BEIRAT,'Beirat', bold)

    MITGLIED = 14
    w_write(HEADROW,MITGLIED,'RUBION-Mitglied', bold)

    MITGLIEDERVERSAMMLUNG = 15
    w_write(HEADROW,MITGLIEDERVERSAMMLUNG,'Einladung MV', bold)

    SONSTIGE = 16
    w_write(HEADROW,SONSTIGE,'Sonstige', bold)
    
    RMETHODS = 17
    w_write(HEADROW,RMETHODS,'Methoden', bold)

    RAUM = 18
    w_write(HEADROW,RAUM,'Raum', bold)

    TELEFON = RAUM+1
    w_write(HEADROW,TELEFON,'Telefon', bold)
    EMAIL = TELEFON+1
    w_write(HEADROW,EMAIL,'E-Mail', bold)
    WOHNORT = EMAIL+1
    w_write(HEADROW,WOHNORT,'Wohnort', bold)
    STRASSE = WOHNORT+1
    w_write(HEADROW,STRASSE,'Straße', bold)
    GEBURTSTAG = STRASSE+1
    w_write(HEADROW,GEBURTSTAG,'Geburtstag', bold)
    GEBURTSORT = GEBURTSTAG+1
    w_write(HEADROW,GEBURTSORT,'Geburtsort', bold)
    FRUEHERERNAME = GEBURTSORT+1
    w_write(HEADROW,FRUEHERERNAME,'Früherer Name', bold)
    SCHLUESSEL = FRUEHERERNAME+1
    w_write(HEADROW,SCHLUESSEL,'Schlüssel', bold)
    DOSEMETER = SCHLUESSEL + 1
    w_write(HEADROW,DOSEMETER,'Art des Dosimeters', bold)
    nextpos = DOSEMETER + 1
    SICOORDINATES = {}
    with override_lang('de'):
        for instruction in SI.AVALABLE_SAFETY_INSTRUCTIONS:
            SICOORDINATES.update({ instruction : nextpos })
            ws.merge_range(
                HEADROW-1, nextpos, HEADROW-1, nextpos+1,
                str(SI.SAFETYINSTRUCTION_NAMES[instruction]), bold)
            w_write(HEADROW,nextpos,'benötigt?', bold)
            w_write(HEADROW,nextpos+1,'letzte Auffrischung', bold)
            nextpos = nextpos + 2
        
    
    
    BEMERKUNGEN1 = nextpos 
    w_write(HEADROW,BEMERKUNGEN1,'Bemerkungen 1', bold)
    BEMERKUNGEN2 = BEMERKUNGEN1 + 1
    w_write(HEADROW,BEMERKUNGEN2,'Bemerkungen 2', bold)

    # end pseudo-constants
    
    # maximum column number
    MAXCOL = BEMERKUNGEN2


    # internal function for writing safety instruction information

    def write_safety_information(row, user):
        informations = SI.get_instruction_information( user )
        for instruction, information in informations.items():
            if information['required']:
                w_write( row, SICOORDINATES[instruction],  "✓" )
            w_write( row, SICOORDINATES[instruction]+1, information['last']  )

    # internal function for writing staff information
    def write_staff_user(row, staff):
        w_write(row, NAME, staff.get_last_name())
        w_write(row, VORNAME, staff.get_first_name())
        w_write(row, EMAIL, staff.mail)
        try:
            ru = RUBIONUser.objects.filter(linked_user = staff.user).first()
        except RUBIONUser.DoesNotExist:
            ru = None

        if is_beirat(staff) or is_beirat(ru):
            w_write(row, BEIRAT, "✓")
            w_write(row, MITGLIEDERVERSAMMLUNG, '✓')
            beirat = True
        else:
            beirat = False

        if staff.get_parent().specific.show_in_list:
            w_write(row, MITARBEITER, "✓")        
            w_write(row, MITGLIED, '✓')
            w_write(row, MITGLIEDERVERSAMMLUNG, '✓')
        else:
            if not beirat:
                w_write(row, SONSTIGE, "✓")        
        

 
        w_write(row, SCHLUESSEL, staff.key_number)
        w_write(row, TITEL, staff.grade)
        w_write(row, RAUM, staff.room)
        w_write(row, TELEFON, str(staff.phone))
        write_safety_information( row, staff )

    # internal function for writing user information
    def write_rubion_user(row, ru):
        w_write(row, NAME, ru.last_name)
        
        w_write(row, VORNAME, ru.first_name)
        w_write(row, TITEL, ru.get_academic_title_display())
        w_write(row, EMAIL, ru.email)
        w_write(row, NUTZER, '✓')
        if ru.is_leader:
            w_write(row, LEITUNG, '✓')
        wg = ru.get_workgroup()
        w_write(row, UNIVERSITAET, wg.university)
        w_write(row, INSTITUT, wg.institute)
        w_write(row, ARBEITSGRUPPE, wg.title_trans)
        rm = wg.get_methods()
        r_methods = ''
        for method in rm:
            r_methods = r_methods + str(method) + '\n'
            # this fails for people retrieving the data in german
            #if ( str(method) == 'Working with unstable isotopes' or
            #     str(method) == 'Other' or
            #     str(method).
            #) :
            if re.match(r'.*[ui]nstab(le|il).*', str(method)):
                w_write(row, NI, '✓')
            else:
                w_write(row, NT, '✓')

        w_write(row, RMETHODS, r_methods)
        head = wg.get_head()
        if head:
            w_write(row, AGLEITER, "{} {}".format(head.first_name, head.last_name))

        w_write(row, GEBURTSORT, ru.place_of_birth)
        w_write(row, GEBURTSTAG, ru.date_of_birth)
        w_write(row, FRUEHERERNAME, ru.previous_names)

        try:
            su = StaffUser.objects.filter(user = ru.linked_user).first()
        except StaffUser.DoesNotExist:
            su = None
        

        beirat = is_beirat(ru) or is_beirat(su)
        if not su:
            w_write(row, SCHLUESSEL, ru.key_number)
            if ru.phone:
                w_write(row, TELEFON, str(ru.phone))

        if beirat:
            w_write(row, BEIRAT, '✓')

        if (ru.is_rub and ru.is_leader):
            w_write(row, MITGLIED, '✓')
            w_write(row, MITGLIEDERVERSAMMLUNG, '✓')
        if beirat:
            w_write(row, MITGLIEDERVERSAMMLUNG, '✓')
        w_write(row, FRUEHERERNAME, ru.previous_names)

        w_write(row, DOSEMETER, ru.get_dosemeter_display())
        w_write(row, BEMERKUNGEN1, ru.internal_rubion_comment.replace('<br/>','\n').replace('</p>','\n'), textwrap)
        write_safety_information(row, ru)


    row = HEADROW + 1

    allstaff = StaffUser.objects.all()

    linked_users = []

    for staff in allstaff:
        write_staff_user(row, staff)
        if staff.linked_user:
            linked_users.append(staff.linked_user)
            try:
                write_rubion_user(row, RUBIONUser.objects.get(linked_user = staff.linked_user))
            except RUBIONUser.DoesNotExist:
                pass

        row=row+1

    rubionusers = RUBIONUser.objects.exclude(linked_user__in = linked_users)

    for ru in rubionusers:
        write_rubion_user(row, ru)

        row=row+1

    ws.autofilter(HEADROW,0,row,MAXCOL)

    for i in range(MAXCOL+1):
        try:
            if widths[i] > 9:
                ws.set_column(i,i, widths[i]*1.2)
            else:
                ws.set_column(i,i, 12)
        except KeyError:
            ws.set_column(i,i, 12)

    wb.close()

    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    response['Content-Disposition'] = "attachment; filename=nutzer-{}-.xlsx".format(datetime.datetime.now())

    output.close()

    return response

def user_set_dosemeter( request, user_id, dosemeter ):
    ruser = get_object_or_404(RUBIONUser, id=user_id)
    
    if not ruser.permissions_for_user(request.user).can_edit():
        return HttpResponseNotAllowed

    dosemeter = str(dosemeter)

    valid_choice = False
    for ch in RUBIONUser.DOSEMETER_CHOICES:
        if ch[0] == dosemeter:
            valid_choice = True
            break

    if not valid_choice:
        return HttpResponseNotAllowed

    ruser.dosemeter = dosemeter
    ruser.save_revision_and_publish( user = request.user )
    return redirect('wagtailadmin_home')


def user_send_data_to_cro( request, user_id ):
    if not request.user.has_perm('notifications.add_centralradiationsafetydatasubmission'):
        return HttpResponseNotAllowed
    ruser = get_object_or_404(RUBIONUser, id = user_id )
    submission = CentralRadiationSafetyDataSubmission(ruser = ruser)
    submission.send_and_save()

    
    if request.GET.get('next', None):
        return redirect(request.GET.get('next'))
    else:
        return redirect('wagtailadmin_home')
    

def user_cro_knows_data( request, user_id ):
    if not request.user.has_perm('notifications.add_centralradiationsafetydatasubmission'):
        return HttpResponseNotAllowed
    ruser = get_object_or_404(RUBIONUser, id = user_id )
    submission = CentralRadiationSafetyDataSubmission(ruser = ruser)
    submission.save()

    
    if request.GET.get('next', None):
        return redirect(request.GET.get('next'))
    else:
        return redirect('wagtailadmin_home')
    

    
