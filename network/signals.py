from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Employee


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    Автоматически создает профиль сотрудника при создании пользователя.
    Только для персонала (is_staff=True).
    """
    if created and instance.is_staff:
        Employee.objects.get_or_create(
            user=instance, defaults={"department": "Не назначен", "position": "Сотрудник", "is_active": True}
        )


@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    """Сохраняет профиль сотрудника при сохранении пользователя"""
    if hasattr(instance, "employee_profile"):
        instance.employee_profile.save()
