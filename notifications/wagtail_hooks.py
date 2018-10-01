from .models import NewsSnippet

from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)




class NewsSnippetModelAdmin( ModelAdmin ):
    model = NewsSnippet
    menu_label = _l('News')
    menu_icon = 'fa-info'
    menu_order = 300
    list_display = ('title_de', 'title_en', 'date_published')
    form_view_extra_js = ['js/admin/news/templates.js']
    form_view_extra_css = ['css/admin/news_create.css']

modeladmin_register(NewsSnippetModelAdmin)
