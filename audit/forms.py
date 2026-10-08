from django import forms

from rooms.models import Room


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    room = forms.ModelChoiceField(
        required=False,
        label="Sala",
        queryset=Room.objects.order_by('code'),
        empty_label="Todas las salas",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'La fecha final debe ser igual o posterior a la fecha inicial.')
        return cleaned_data
