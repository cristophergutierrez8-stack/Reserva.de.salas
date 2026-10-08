import os

from axes.utils import reset as reset_axes_attempts
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from users.models import User


class Command(BaseCommand):
    help = "Optionally creates or resets the configured initial admin account."

    def handle(self, *args, **options):
        bootstrap_enabled = os.environ.get(
            "INITIAL_ADMIN_BOOTSTRAP", ""
        ).strip().lower()
        if bootstrap_enabled not in {"true", "false", ""}:
            raise CommandError("INITIAL_ADMIN_BOOTSTRAP must be true or false.")
        if bootstrap_enabled != "true":
            self.stdout.write("INITIAL ADMIN BOOTSTRAP DISABLED")
            return

        username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
        if username != "admin":
            raise CommandError(
                "INITIAL_ADMIN_USERNAME must be set to the required bootstrap username."
            )

        password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
        if not password:
            raise CommandError(
                "INITIAL_ADMIN_PASSWORD is required while bootstrap is enabled."
            )

        try:
            with transaction.atomic():
                existing_account = (
                    User.objects.select_for_update()
                    .filter(username=username)
                    .first()
                )

                if existing_account:
                    if not self._is_administrator(existing_account):
                        raise CommandError(
                            "INITIAL ADMIN ALREADY EXISTS NON-ADMIN"
                        )

                    self._set_password(existing_account, password)
                    existing_account.save(update_fields=["password"])
                    reset_axes_attempts(username=username)
                    outcome = "reset"
                else:
                    user = User(
                        username=username,
                        role=User.Role.ADMINISTRADOR,
                        is_active=True,
                        is_staff=True,
                        is_superuser=True,
                    )
                    self._set_password(user, password)
                    user.save(force_insert=True)
                    outcome = "created"
        except IntegrityError:
            # A concurrent startup may have created the configured username.
            existing_account = User.objects.filter(username=username).first()
            if not existing_account:
                raise CommandError(
                    "Initial administrator bootstrap could not complete."
                ) from None
            if not self._is_administrator(existing_account):
                raise CommandError(
                    "INITIAL ADMIN ALREADY EXISTS NON-ADMIN"
                ) from None

            try:
                with transaction.atomic():
                    existing_account = User.objects.select_for_update().get(
                        username=username
                    )
                    self._set_password(existing_account, password)
                    existing_account.save(update_fields=["password"])
                    reset_axes_attempts(username=username)
            except ValidationError as error:
                raise CommandError(
                    "INITIAL ADMIN PASSWORD VALIDATION FAILED"
                ) from error
            outcome = "reset"
        except ValidationError as error:
            raise CommandError(
                "INITIAL ADMIN PASSWORD VALIDATION FAILED"
            ) from error

        if outcome == "created":
            self.stdout.write("INITIAL ADMIN CREATED")
        else:
            self.stdout.write("INITIAL ADMIN PASSWORD RESET")

    @staticmethod
    def _is_administrator(user):
        return user.is_superuser or user.role == User.Role.ADMINISTRADOR

    @staticmethod
    def _set_password(user, password):
        validate_password(password, user=user)
        user.set_password(password)
