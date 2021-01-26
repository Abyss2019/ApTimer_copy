from django import forms


class ExcelForm(forms.Form):
    excel = forms.FileField()

class InputIniboundForm(forms.Form):
    file = forms.FileField()
