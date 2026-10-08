from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from datetime import datetime, date
from audit.models import AuditLog
from audit.forms import ReportFilterForm
from reservations.models import Reservation
from rooms.models import Room
from users.models import User
from django.utils import timezone


@login_required
def audit_log_view(request):
    if not request.user.is_administrador():
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    logs = AuditLog.objects.all().select_related('user')[:100]
    return render(request, 'audit/audit_log.html', {'logs': logs})


@login_required
def reports_view(request):
    if not (request.user.is_administrador() or request.user.is_secretaria()):
        messages.error(request, "Acceso no autorizado.")
        return redirect('dashboard')

    form = ReportFilterForm(request.GET or None)
    reservations = Reservation.objects.all()
    if form.is_bound:
        if form.is_valid():
            filters = form.cleaned_data
            if filters['date_from']:
                reservations = reservations.filter(date__gte=filters['date_from'])
            if filters['date_to']:
                reservations = reservations.filter(date__lte=filters['date_to'])
            if filters['room']:
                reservations = reservations.filter(room=filters['room'])
        else:
            reservations = reservations.none()

    status_dict = dict(
        reservations.values('status').annotate(count=Count('pk')).values_list('status', 'count')
    )
    room_counts = dict(
        reservations.values('room_id').annotate(count=Count('pk')).values_list('room_id', 'count')
    )
    room_hours = {}
    for room_id, start_time, end_time in reservations.filter(
        status=Reservation.Status.CONFIRMADA
    ).values_list('room_id', 'start_time', 'end_time'):
        duration = (
            datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)
        ).total_seconds() / 3600
        room_hours[room_id] = room_hours.get(room_id, 0) + duration

    rooms = Room.objects.order_by('code')
    if form.is_valid() and form.cleaned_data['room']:
        rooms = rooms.filter(pk=form.cleaned_data['room'].pk)
    room_stats = [
        {
            'room': room,
            'reservation_count': room_counts.get(room.pk, 0),
            'reserved_hours': round(room_hours.get(room.pk, 0), 2),
        }
        for room in rooms
    ]
    reservations_by_period = reservations.values('date').annotate(
        count=Count('pk')
    ).order_by('date')

    context = {
        'form': form,
        'total_reservations': reservations.count(),
        'confirmadas_count': status_dict.get(Reservation.Status.CONFIRMADA, 0),
        'canceladas_count': status_dict.get(Reservation.Status.CANCELADA, 0),
        'noshow_count': status_dict.get(Reservation.Status.NO_SHOW, 0),
        'room_stats': room_stats,
        'reservations_by_period': reservations_by_period,
        'active_blocked_users_count': User.objects.filter(
            blocked_until__gt=timezone.now()
        ).count(),
    }
    return render(request, 'audit/reports.html', context)
