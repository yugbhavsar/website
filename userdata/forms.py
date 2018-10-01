from django.forms.models import ModelForm
from django import forms

from .models.ugc import TestModel, UserGeneratedPage

class TestModelModelForm( ModelForm ):
    class Meta:
        model = TestModel
        exclude = UserGeneratedPage.exclude
    
