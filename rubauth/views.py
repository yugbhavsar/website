from .forms import RUBUserCreationForm, IdentificationForm
from .models import Identification

from django.contrib.auth import logout as auth_logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _

from wagtail.admin import messages
from wagtail.admin.utils import (
    any_permission_required, permission_denied, 
    permission_required
)
from wagtail.users.wagtail_hooks import add_user_perm



def get_user_creation_form():
    return RUBUserCreationForm

@permission_required(add_user_perm)
def create(request):
    if request.method == 'POST':
        form = get_user_creation_form()(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' created.").format(user), buttons=[
                messages.button(reverse('wagtailusers_users:edit', args=(user.pk,)), _('Edit'))
            ])
            return redirect('wagtailusers_users:index')
        else:
            messages.error(request, _("The user could not be created due to errors."))
    else:
        form = get_user_creation_form()()
    return render(request, 'rubauth/users/create.html', {
        'form': form,
    })

def logout(request, *args, **kwargs):
    auth_logout(request, *args, **kwargs)
    next_page = request.GET.get('next_page', None)
    if not next_page:
        next_page = '/'
    return HttpResponseRedirect(next_page)
        
def identify( request, *args, **kwargs ):
    pk = kwargs['pk']
    ident = None
    
    # ------------------------------------------------- 
    def is_rub_ip( request ):

        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[-1].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip


        return get_client_ip( request ).startswith('134.147')
    # ------------------------------------------------- 

    try:
        ident = Identification.objects.get(id = pk)
    except:
        pass
    if ident is None or ident.has_been_shown:
        raise Http404('Page does not exists')
    
    init_user = IdentificationForm.EXT
    if is_rub_ip( request ):
        init_user = IdentificationForm.RUB

    if request.method == 'GET':
#        ident.has_been_shown = True
#        ident.save()
        form = IdentificationForm(initial = {'usertype' : init_user })
        return render(
            request,
            'rubauth/identify.html',
            {
                'form': form
            }
        )
    elif request.method == 'POST':
        form = IdentificationForm(request.POST)
        if form.is_valid():
            if form.rub_username and form.rub_login_valid:
                response = ident.is_identified(form.rub_username, request, rub_user = True)
            else:
                response = ident.send_mail(form.email, request)
                if not response:
                    response = render(
                        request,
                        'rubauth/identification_mail_sent.html',
                        {
                            'mail' : form.email
                        }
        )

            return response
        else:
            return render(
                request,
                'rubauth/identify.html',
                {
                    'form': form
                }
            )
 


def confirm( request, uuid ):
    ident = get_object_or_404(Identification, uuid = uuid )
    if not ident:
        raise Http404('UUID not found')
    else:
        return ident.is_identified( ident.email, request )
