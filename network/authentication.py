from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Employee


class ActiveEmployeeAuthentication(SessionAuthentication):
    """
    Кастомная аутентификация, проверяющая активность сотрудника.
    """

    def authenticate(self, request):
        # Используем базовую аутентификацию SessionAuthentication
        user_auth_tuple = super().authenticate(request)

        if user_auth_tuple is not None:
            user, auth = user_auth_tuple

            # Проверяем, активен ли сотрудник
            try:
                employee = user.employee_profile
                if not employee.is_active:
                    raise AuthenticationFailed("Ваш аккаунт сотрудника деактивирован.")

                # Обновляем дату последнего входа
                employee.update_last_login()

            except Employee.DoesNotExist:
                # Если у пользователя нет профиля сотрудника
                if user.is_superuser:
                    # Суперпользователям разрешаем доступ без профиля
                    return user_auth_tuple
                raise AuthenticationFailed("Профиль сотрудника не найден.")

            return user_auth_tuple

        return None
