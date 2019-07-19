from django.db import models

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting

@register_setting
class CourseSettings(BaseSetting):
    vat = models.DecimalField(
        max_digits = 4,
        decimal_places = 2,
        default = 19,
        verbose_name = _('VAT rate')
    )

    invoice_counter = models.IntegerField(
        default = 0,
    )
    invoice_counter_year = models.IntegerField(
        default = 2018
    )

    panels = [
        FieldPanel('vat')
    ]
