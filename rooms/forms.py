from django import forms
from rooms.models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'code', 'capacity', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sala de Estudio A1'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. SALA-A1'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
