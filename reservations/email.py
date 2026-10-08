import logging
import smtplib

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

logger = logging.getLogger(__name__)


def send_reservation_confirmation(reservation):
    recipient = reservation.student.email
    if not recipient:
        return

    try:
        validate_email(recipient)
    except ValidationError:
        logger.info(
            "Reservation confirmation email skipped for reservation %s: invalid recipient address.",
            reservation.pk,
        )
        return

    try:
        send_mail(
            subject=f"Reserva de sala confirmada #{reservation.pk}",
            message=(
                f"Su reserva de la sala {reservation.room.name} ({reservation.room.code}) "
                f"para el {reservation.date:%d/%m/%Y}, de "
                f"{reservation.start_time:%H:%M} a {reservation.end_time:%H:%M}, "
                "ha sido confirmada."
            ),
            from_email=None,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except (OSError, smtplib.SMTPException) as error:
        logger.error(
            "Reservation confirmation email failed for reservation %s (%s).",
            reservation.pk,
            type(error).__name__,
        )
