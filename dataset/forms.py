# forms.py
from .models import Dataset
from django import forms

class DatasetInfoForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'status']

class DatasetFileForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['cover_image', 'data_file']
