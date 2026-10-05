from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from audit.models import AuditLog
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

    now = timezone.now()

    # Métricas generales
    total_reservations = Reservation.objects.count()
    status_counts = Reservation.objects.values('status').annotate(count=Count('status'))
    status_dict = {item['status']: item['count'] for item in status_counts}

    # Salas más reservadas
    top_rooms = Room.objects.annotate(
        total_res=Count('reservations')
    ).order_by('-total_res')[:5]

    # Usuarios actualmente bloqueados por No-Show
    active_blocked_users = User.objects.filter(blocked_until__gt=now)

    context = {
        'total_reservations': total_reservations,
        'confirmadas_count': status_dict.get(Reservation.Status.CONFIRMADA, 0),
        'canceladas_count': status_dict.get(Reservation.Status.CANCELADA, 0),
        'noshow_count': status_dict.get(Reservation.Status.NO_SHOW, 0),
        'top_rooms': top_rooms,
        'active_blocked_users': active_blocked_users,
    }
    return render(request, 'audit/reports.html', context)
