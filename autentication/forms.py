from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Reservation
from django.forms.widgets import DateInput
from django.core.exceptions import ValidationError
from datetime import datetime

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'avatar')
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'password1': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
            'password2': forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        }

class ReservationForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': 'required',
            'min': datetime.today().strftime('%Y-%m-%d'),  # Fecha mínima hoy
            'placeholder': 'Seleccione una fecha',
            'autocomplete': 'off',  # Para desactivar autocompletado de fecha si es necesario
        })
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'maxlength': '9',
            'pattern': r'^\d{9}$',  # Regex para un teléfono válido
            'title': 'Introduzca un número de teléfono válido',
            'placeholder': 'Ingrese su número de teléfono',
            'autocomplete': 'tel',  # Autocompletado para teléfonos
            'id': 'phone'  # Asegura que la etiqueta se vincule correctamente
        })
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date < datetime.today().date():
            raise ValidationError("La fecha de la reserva no puede ser en el pasado.")
        return date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if len(phone) != 9:
            raise ValidationError("El número de teléfono debe tener exactamente 9 dígitos.")
        return phone

    class Meta:
        model = Reservation
        fields = ['name', 'phone', 'guests', 'date', 'notes']  # Añadir 'notes' a los campos
        labels = {
            'name': 'Nombre',
            'phone': 'Teléfono',
            'guests': 'Comensales',
            'date': 'Fecha',
            'notes': 'Notas'  # Etiqueta para el campo 'notes'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'placeholder': 'Nombre del cliente',
                'autocomplete': 'name',  # Autocompletado para nombres
                'id': 'name'
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'min': 1,
                'placeholder': 'Número de comensales',
                'autocomplete': 'off',  # Desactiva autocompletado si es necesario
                'id': 'guests'
            }),
            'notes': forms.Textarea(attrs={  # Añadir el widget para 'notes'
                'class': 'form-control',
                'placeholder': 'Añadir notas adicionales...',
                'rows': 3,  # Opcional: establecer la altura del área de texto
                'id': 'notes'
            })
        }

