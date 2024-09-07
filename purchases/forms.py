from django import forms
from .models import Purchase, AjustePedido


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['item_name', 'quantity', 'category']  # Asegúrate de incluir 'category'
        labels = {
            'item_name': 'Artículo',
            'quantity': 'Cantidad',
            'category': 'Categoría',
        }
        widgets = {
            'item_name': forms.TextInput(attrs={
                'placeholder': 'Nombre del artículo',
                'class': 'form-control',
                'required': 'required',
                'autocomplete': 'off',
                'id': 'item_name'
            }),
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Cantidad',
                'class': 'form-control',
                'required': 'required',
                'min': 1,
                'autocomplete': 'off',
                'id': 'quantity'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'category'
            })
        }


class AjustePedidoForm(forms.ModelForm):
    class Meta:
        model = AjustePedido
        fields = ['articulo', 'cantidad_ajustada', 'motivo', 'comprado_fuera']