from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from rooms.models import Room
from users.models import User
from reservations.models import Reservation
from reservations.forms import AvailabilityFilterForm, ReservationForm, AssistedReservationForm
from reservations.services import (
    validate_and_create_reservation,
    cancel_reservation,
    register_noshow
)


@login_required
def availability_view(request):
    """Consulta de disponibilidad de salas por fecha."""
    form = AvailabilityFilterForm(request.GET or None)
    selected_date = date.today()
    rooms = Room.objects.filter(is_active=True)
    if form.is_bound:
        if form.is_valid():
            selected_date = form.cleaned_data['date'] or date.today()
            selected_room = form.cleaned_data['room_id']
            if selected_room:
                rooms = rooms.filter(pk=selected_room.pk)
        else:
            rooms = rooms.none()

    # Buscar reservas confirmadas para la fecha
    confirmed_reservations = Reservation.objects.filter(
        date=selected_date,
        status=Reservation.Status.CONFIRMADA
    )

    rooms_availability = []
    for room in rooms:
        room_res = confirmed_reservations.filter(room=room).order_by('start_time')
        rooms_availability.append({
            'room': room,
            'reservations': room_res
        })

    context = {
        'form': form,
        'selected_date': selected_date,
        'rooms_availability': rooms_availability
    }
    return render(request, 'reservations/availability.html', context)


@login_required
def create_reservation_view(request):
    """Creación de reserva directa por Alumno."""
    if request.user.is_blocked():
        blocked_str = request.user.blocked_until.strftime('%d/%m/%Y a las %H:%M')
        messages.error(request, f"No puede realizar reservas. Tiene un bloqueo vigente hasta {blocked_str}.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            room = form.cleaned_data['room']
            res_date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            attendees_count = form.cleaned_data['attendees_count']

            try:
                reservation = validate_and_create_reservation(
                    student=request.user,
                    created_by=request.user,
                    room=room,
                    date=res_date,
                    start_time=start_time,
                    end_time=end_time,
                    attendees_count=attendees_count
                )
                messages.success(request, f"¡Reserva #{reservation.pk} creada exitosamente!")
                return redirect('my_reservations')
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        # Pre-poblar fecha o sala si viene por query params
        initial_data = {}
        if request.GET.get('room_id'):
            initial_data['room'] = request.GET.get('room_id')
        if request.GET.get('date'):
            initial_data['date'] = request.GET.get('date')
        form = ReservationForm(initial=initial_data)

    return render(request, 'reservations/reservation_form.html', {'form': form, 'title': 'Nueva Reserva Directa'})


@login_required
def assisted_reservation_view(request):
    """Reserva asistida realizada por Secretaría ingresando el RUT del alumno."""
    if not (request.user.is_secretaria() or request.user.is_administrador()):
        messages.error(request, "Acceso no autorizado. Función exclusiva de Secretaría y Administración.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = AssistedReservationForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data['rut'].strip()
            room = form.cleaned_data['room']
            res_date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            attendees_count = form.cleaned_data['attendees_count']

            # Validar existencia del alumno por RUT (RB02 / RF02)
            try:
                student = User.objects.get(rut=rut, role=User.Role.ALUMNO)
            except User.DoesNotExist:
                messages.error(request, f"No se encontró ningún alumno registrado con el RUT '{rut}'.")
                return render(request, 'reservations/assisted_reservation_form.html', {'form': form})

            # Validar que esté habilitado y tenga condición de alumno regular (RB02)
            if not student.is_active:
                messages.error(request, f"El alumno {student.get_full_name() or student.username} se encuentra desactivado en el sistema.")
                return render(request, 'reservations/assisted_reservation_form.html', {'form': form})

            if not student.is_regular_student:
                messages.error(request, f"El alumno {student.get_full_name() or student.username} (RUT: {rut}) NO cumple con la condición de Alumno Regular.")
                return render(request, 'reservations/assisted_reservation_form.html', {'form': form})

            # Crear reserva asistida aplicando todas las reglas de negocio en backend
            try:
                reservation = validate_and_create_reservation(
                    student=student,
                    created_by=request.user,
                    room=room,
                    date=res_date,
                    start_time=start_time,
                    end_time=end_time,
                    attendees_count=attendees_count
                )
                messages.success(request, f"¡Reserva Asistida #{reservation.pk} creada exitosamente para el alumno {student.get_full_name()}!")
                return redirect('my_reservations')
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = AssistedReservationForm()

    return render(request, 'reservations/assisted_reservation_form.html', {'form': form})


@login_required
def my_reservations_view(request):
    """Listado e historial de reservas del alumno o consulta global para gestión."""
    user = request.user
    if user.is_alumno():
        reservations = Reservation.objects.filter(student=user)
    else:
        reservations = Reservation.objects.all()

    context = {
        'reservations': reservations.select_related('student', 'room')
    }
    return render(request, 'reservations/my_reservations.html', context)


@login_required
def reservation_detail_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    # Verificar acceso (dueño o personal autorizado)
    if not (request.user == reservation.student or request.user.is_secretaria() or request.user.is_administrador()):
        messages.error(request, "No tiene permisos para ver este detalle.")
        return redirect('my_reservations')

    return render(request, 'reservations/reservation_detail.html', {'reservation': reservation})


@login_required
def cancel_reservation_view(request, reservation_id):
    if request.method != 'POST':
        return redirect('my_reservations')

    reservation = get_object_or_404(Reservation, pk=reservation_id)

    try:
        cancel_reservation(reservation, request.user)
        messages.success(request, f"La reserva #{reservation.pk} fue cancelada correctamente.")
    except ValidationError as e:
        messages.error(request, e.message)

    return redirect('my_reservations')


@login_required
def noshow_list_view(request):
    """Módulo de gestión de No-Show para Secretaría y Administración."""
    if not (request.user.is_secretaria() or request.user.is_administrador()):
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    now = timezone.now()
    today = now.date()

    # Buscar reservas confirmadas cuya fecha/hora de término ya pasó
    past_confirmed = [
        res for res in Reservation.objects.filter(status=Reservation.Status.CONFIRMADA, date__lte=today).select_related('student', 'room')
        if res.can_be_marked_noshow()
    ]

    context = {
        'past_reservations': past_confirmed,
        'blocked_users': User.objects.filter(blocked_until__gt=now)
    }
    return render(request, 'reservations/noshow_list.html', context)


@login_required
def register_noshow_view(request, reservation_id):
    if request.method != 'POST':
        return redirect('noshow_list')

    reservation = get_object_or_404(Reservation, pk=reservation_id)

    try:
        register_noshow(reservation, request.user)
        messages.success(
            request,
            f"Se registró el No-Show para la reserva #{reservation.pk}. "
            f"Se aplicó el bloqueo de 3 días calendario al alumno '{reservation.student.username}' hasta {reservation.student.blocked_until.strftime('%d/%m/%Y %H:%M')}."
        )
    except ValidationError as e:
        messages.error(request, e.message)

    return redirect('noshow_list')
