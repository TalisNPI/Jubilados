from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, ReservationForm
from .models import Reservation, Camarero
from purchases.models import Purchase
from purchases.forms import PurchaseForm
from django.db.models import Sum
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter
import requests
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.utils.timezone import localdate
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def home_view(request):
    # Verificar si hay un camarero seleccionado
    selected_camarero = None
    if 'selected_camarero_id' in request.session:
        selected_camarero_id = request.session['selected_camarero_id']
        selected_camarero = get_object_or_404(Camarero, id=selected_camarero_id)

    # Formularios
    reservation_form = ReservationForm()
    purchase_form = PurchaseForm()

    # Obtener la fecha más reciente que tiene reservas
    latest_date = Reservation.objects.latest('date').date

    # Obtener las últimas 3 reservas de la fecha más reciente
    reservations = Reservation.objects.filter(date=latest_date).order_by('-date', '-id')[:3]

    # Agrupar las reservas por la fecha más reciente
    grouped_reservations = {latest_date: reservations}

    # Ordenar las compras por orden alfabético y mostrar solo 3
    purchases = Purchase.objects.all().order_by('item_name')[:3]

    # Calcular el total de comensales y contar el número de reservas
    total_comensales = Reservation.objects.filter(date=latest_date).aggregate(Sum('guests'))['guests__sum'] or 0
    mesas_reservadas = Reservation.objects.filter(date=latest_date).count()

    # Calcular el porcentaje de ocupación
    capacidad_total = 55
    porcentaje_ocupacion = (total_comensales / capacidad_total) * 100

    # Obtener los datos meteorológicos de Turis
    weather_info = get_weather_data(latitude=39.3667, longitude=-0.6833)

    return render(request, 'home.html', {
        'grouped_reservations': grouped_reservations,
        'purchases': purchases,
        'reservation_form': reservation_form,
        'purchase_form': purchase_form,
        'total_comensales': total_comensales,
        'mesas_reservadas': mesas_reservadas,
        'capacidad_total': capacidad_total,
        'porcentaje_ocupacion': porcentaje_ocupacion,
        'weather_info': weather_info,
        'selected_camarero': selected_camarero  # Pasar el camarero seleccionado al template
    })


@login_required
def add_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user

            # Asociar la reserva al camarero seleccionado
            if 'selected_camarero_id' in request.session:
                camarero = get_object_or_404(Camarero, id=request.session['selected_camarero_id'])
                reservation.camarero = camarero

            reservation.save()
            messages.success(request, 'Reserva añadida con éxito.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, 'Hubo un error al añadir la reserva. Por favor, revisa el formulario.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = ReservationForm()

    return render(request, 'add_reservation.html', {'form': form})


@login_required
def all_reservations_view(request):
    query = request.GET.get('q', None)
    today = localdate()
    latest_date = Reservation.objects.latest('date').date

    if query:
        reservations = Reservation.objects.filter(
            Q(name__icontains=query) & Q(date__gte=today)
        ).order_by('-date')
    else:
        reservations = Reservation.objects.all().order_by('-date')

    # Agrupar las reservas por fecha
    grouped_reservations = {latest_date: reservations}
    grouped_notes = {}

    for date, group in groupby(reservations, key=attrgetter('date')):
        reservations_list = list(group)
        grouped_reservations[date] = reservations_list

        # Recoger las notas de las reservas de este grupo
        notes_list = [{'name': reservation.name, 'note': reservation.notes}
                      for reservation in reservations_list if reservation.notes]
        if notes_list:
            grouped_notes[date] = notes_list

    # Calcular el total de comensales y contar el número de reservas
    total_comensales = Reservation.objects.filter(date=latest_date).aggregate(Sum('guests'))['guests__sum'] or 0
    mesas_reservadas = Reservation.objects.filter(date=latest_date).count()

    # Calcular el porcentaje de ocupación
    capacidad_total = 55
    porcentaje_ocupacion = (total_comensales / capacidad_total) * 100

    reservation_form = ReservationForm()

    return render(request, 'all_reservations.html', {
        'grouped_reservations': grouped_reservations,
        'grouped_notes': grouped_notes,
        'query': query,
        'found_reservations': reservations.exists(),
        'reservation_form': reservation_form,
        'total_comensales': total_comensales,
        'mesas_reservadas': mesas_reservadas,
        'capacidad_total': capacidad_total,
        'porcentaje_ocupacion': porcentaje_ocupacion,
    })


@login_required
def edit_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(instance=reservation)
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('all_reservations')
    return render(request, 'edit_reservation.html', {'form': form, 'reservation': reservation})


@login_required
def delete_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        return redirect('all_reservations')
    return render(request, 'delete_reservation.html', {'reservation': reservation})


def get_weather_data(latitude, longitude):
    base_url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'daily': 'temperature_2m_max,temperature_2m_min,weathercode',
        'timezone': 'Europe/Madrid'
    }

    response = requests.get(base_url, params=params)
    weather_data = response.json()

    if response.status_code == 200:
        daily_data = weather_data.get('daily', {})
        week_data = []

        for i in range(len(daily_data['time'])):
            date_str = daily_data['time'][i]
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')

            weather_code = daily_data['weathercode'][i]
            if weather_code in [1, 2]:
                weather_desc = 'Soleado'
                weather_icon = '☀️'
            elif weather_code in [3]:
                weather_desc = 'Parcialmente Nublado'
                weather_icon = '⛅'
            else:
                weather_desc = 'Variable'
                weather_icon = '🌤️'

            week_data.append({
                'day_name': date_obj.strftime('%A'),
                'temperature_max': daily_data['temperature_2m_max'][i],
                'temperature_min': daily_data['temperature_2m_min'][i],
                'weather_desc': weather_desc,
                'weather_icon': weather_icon,
            })

        return week_data
    else:
        return None


@require_GET
@login_required
def get_reservations(request):
    saturday_reservations = Reservation.objects.filter(date__week_day=7).values('date').annotate(total_guests=Sum('guests'))

    events = []
    for reservation in saturday_reservations:
        events.append({
            'title': f'{reservation["total_guests"]}',
            'start': reservation['date'].isoformat(),
            'end': reservation['date'].isoformat(),
        })

    return JsonResponse(events, safe=False)


@login_required
def get_reservations_for_date(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            reservations = Reservation.objects.filter(date=date)

            reservation_list = []
            for reservation in reservations:
                reservation_list.append({
                    'id': reservation.id,
                    'name': reservation.name,
                    'phone': reservation.phone,
                    'guests': reservation.guests,
                })

            return JsonResponse(reservation_list, safe=False)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    else:
        return JsonResponse({'error': 'Date parameter is missing'}, status=400)


@login_required
def select_camarero(request):
    # Obtener todos los camareros
    camareros = Camarero.objects.all()

    if request.method == 'POST':
        # Verificar si el camarero ha sido seleccionado
        camarero_id = request.POST.get('camarero_id')
        if camarero_id:
            try:
                # Obtener el camarero seleccionado
                camarero = Camarero.objects.get(id=camarero_id)
                # Guardar la selección en la sesión
                request.session['selected_camarero_id'] = camarero.id
                messages.success(request, f"Camarero {camarero.nombre} seleccionado correctamente.")
                return redirect('home')  # Redirigir a la página principal
            except Camarero.DoesNotExist:
                messages.error(request, "El camarero seleccionado no existe.")
        else:
            messages.error(request, "No se ha seleccionado ningún camarero.")

    return render(request, 'select_camarero.html', {
        'camareros': camareros
    })
