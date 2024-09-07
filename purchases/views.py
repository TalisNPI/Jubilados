import qrcode
from io import BytesIO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from .models import Purchase
from .forms import PurchaseForm, AjustePedidoForm
from collections import defaultdict

def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.user = request.user
            purchase.save()
            messages.success(request, 'Compra añadida con éxito.')
        else:
            messages.error(request, 'Hubo un error al añadir la compra. Por favor, revisa el formulario.')
        
        # Redirigir a la página desde la cual se hizo la solicitud
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'home'))
    else:
        form = PurchaseForm()
    return render(request, 'purchases/add_purchase.html', {'form': form})

def all_purchases_view(request):
    # Obtener todas las compras ordenadas por fecha
    purchases = Purchase.objects.all().order_by('-date')
    
    # Obtener las últimas 5 compras
    last_five_purchases = purchases[:5]
    
    # Agrupar las compras por categoría
    purchases_by_category = defaultdict(list)
    for purchase in purchases:
        purchases_by_category[purchase.category].append(purchase)
    
    # Convertir defaultdict a un diccionario normal para evitar problemas en el template
    purchases_by_category = dict(purchases_by_category)
    
    # Inicializar el formulario de compras para los modales
    purchase_form = PurchaseForm()

    # Pasar las compras agrupadas, el formulario y las últimas compras al template
    return render(request, 'purchases/all_purchases.html', {
        'purchases_by_category': purchases_by_category,
        'purchase_form': purchase_form,
        'last_five_purchases': last_five_purchases,
    })

def generate_qr_code(request):
    if request.method == "POST":
        # Obtener todas las compras actuales
        purchases = Purchase.objects.all()

        # Generar el contenido de texto para el QR
        purchase_list_text = "\n".join([f"{purchase.item_name} - {purchase.quantity}" for purchase in purchases])

        # Generar el QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(purchase_list_text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Guardar la imagen en un objeto BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        # Guardar la imagen en un archivo temporal
        filename = default_storage.save('qr_codes/qr_image.png', ContentFile(img_io.read()))

        # Devolver la URL de la imagen generada
        return JsonResponse({'qr_code_image_url': default_storage.url(filename)})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def edit_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return redirect('all_purchases')
    else:
        form = PurchaseForm(instance=purchase)
    return render(request, 'purchases/edit_purchase.html', {'form': form})

def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    if request.method == 'POST':
        purchase.delete()
        return redirect('all_purchases')
    return render(request, 'purchases/delete_purchase.html', {'purchase': purchase})

def add_ajuste_pedido(request):
    if request.method == 'POST':
        form = AjustePedidoForm(request.POST)
        if form.is_valid():
            ajuste = form.save(commit=False)
            ajuste.usuario = request.user
            ajuste.save()
            messages.success(request, 'Ajuste de pedido registrado con éxito.')
            return redirect('add_ajuste_pedido')
    else:
        form = AjustePedidoForm()

    return render(request, 'purchases/add_ajuste_pedido.html', {'form': form})
