from django import forms

class TitleForm(forms.Form):
	title0 = forms.CharField(label="First Movie or TV Show")
	title1 = forms.CharField(label="Second Movie or TV Show")
