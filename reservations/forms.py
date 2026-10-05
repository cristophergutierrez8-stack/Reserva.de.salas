from django import forms
from rooms.models import Room
from reservations.models import Reservation
from datetime import date


class ReservationForm(forms.Form):
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        label="Sala",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    date = forms.DateField(
        label="Fecha de Reserva",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': str(date.today()), 'required': True})
    )
    start_time = forms.TimeField(
        label="Hora Inicio",
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'required': True})
    )
    end_time = forms.TimeField(
        label="Hora Término",
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'required': True})
    )
    attendees_count = forms.IntegerField(
        label="Cantidad de Asistentes",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'required': True})
    )


class AssistedReservationForm(ReservationForm):
    rut = forms.CharField(
        label="RUT del Alumno",
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo: 11.111.111-1',
            'required': True
        })
    )
