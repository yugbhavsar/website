from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet

from website.models import TranslatedField

@register_snippet
class FundingSnippet( models.Model ):
    agency = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        verbose_name = _('funding agency')
    )
    project_number = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        verbose_name = _('project ID')
    )
    title_en = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('project title (english)'),
    )
    title_de = models.CharField(
        max_length = 256,
        blank = True,
        null = True,
        verbose_name = _('project title (german)'),
    )
    title = TranslatedField('title')
    project_url = models.CharField(
        max_length = 128,
        blank = True,
        null = True,
        verbose_name = _('project url'),
    )
    def __str__(self):
        return self.title_en
        
@register_snippet
class PublicationSnippet ( models.Model ):
    doi = models.CharField(
        max_length = 32,
        blank = True,
        null = True
    )
    authors = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('authors'),
        help_text = _('comma separated list of authors')
    )
    title = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('title'),
        help_text = _('title of the publication')
    )
    journal = models.CharField(
        max_length = 128,
        blank = False,
        null = False,
        verbose_name = _('journal')
    )
    volume = models.CharField(
        max_length = 16,
        blank = False,
        null = False,
        verbose_name = _('volume')
    )
    year = models.IntegerField(
        blank = False,
        null = False,
        verbose_name = _('year')
    )
    pages = models.CharField(
        blank = True,
        null = True,
        max_length = 32,
        verbose_name = _('pages')
    )



    def __str__(self):
        return self.title


@register_snippet
class ThesisSnippet( models.Model ):
    HAB = 'h'
    PHD = 'p'
    MS  = 'm'
    BS  = 'b'

    THESES_TYPES = [
        (HAB, _('Habilitation')),
        (PHD, _('PhD thesis')),
        (MS,  _('Master\'s thesis')),
        (BS,  _('Bachelor\'s thesis'))
    ]

    thesis_type = models.CharField(
        max_length = 1,
        blank = False,
        null = False,
        choices = THESES_TYPES,
        verbose_name = _('theses type (Bachelor, Master or PhD)')
    )
    title = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('title'),
        help_text = _('title of the thesis')
    )
    author = models.CharField(
        max_length = 128,
        blank = False,
        null = False,
        verbose_name = _('author')
    )
    year = models.IntegerField(
        blank = False,
        null = False,
        verbose_name = _('year')
    )
    url = models.CharField(
        max_length = 256,
        blank = True,
        null = True,
        verbose_name = _('internet address')
        
    )

    def __str__(self):
        return self.title


@register_snippet
class UserComment ( models.Model ):
    page = models.ForeignKey( Page, on_delete = models.CASCADE )
    text = models.TextField() 
    created_at = models.DateTimeField(
        auto_now_add = True
    )
    is_creatable = False
    
    
@register_snippet
class Nuclide ( models.Model ):
    element = models.CharField(
        max_length = 3,
        verbose_name = _('Element')
    )

    mass = models.IntegerField(
        null = True,
        blank = True,
        verbose_name = _('Isotope mass')
    )

    def __str__(self):
        return "{}-{}".format(self.element, self.mass)


