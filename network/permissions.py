from rest_framework import permissions

from .models import Employee


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешает доступ только активным сотрудникам.
    Сотрудник должен быть:
    1. Аутентифицированным пользователем
    2. Иметь связанный профиль Employee
    3. Иметь is_active = True в профиле Employee
    """

    message = "Доступ разрешен только активным сотрудникам."

    def has_permission(self, request, view):
        # Проверяем, аутентифицирован ли пользователь
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем, является ли пользователь суперпользователем или персоналом
        if not (request.user.is_superuser or request.user.is_staff):
            return False

        # Для суперпользователей всегда разрешаем доступ
        if request.user.is_superuser:
            return True

        try:
            # Получаем профиль сотрудника
            employee = request.user.employee_profile

            # Проверяем, активен ли сотрудник
            if not employee.is_active:
                self.message = "Ваш аккаунт сотрудника деактивирован. Обратитесь к администратору."
                return False

            # Обновляем дату последнего входа
            employee.update_last_login()

            return True

        except Employee.DoesNotExist:
            # Если у пользователя нет профиля сотрудника
            self.message = "Профиль сотрудника не найден. Обратитесь к администратору."
            return False


class IsAdminOrReadOnlyForEmployees(permissions.BasePermission):
    """
    Разрешает полный доступ администраторам,
    а активным сотрудникам - только безопасные методы (GET, HEAD, OPTIONS).
    """

    message = "Для выполнения этого действия требуются права администратора."

    def has_permission(self, request, view):
        # Разрешаем безопасные методы для всех аутентифицированных
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Для остальных методов требуем суперпользователя
        return request.user and request.user.is_authenticated and request.user.is_superuser


class DepartmentPermission(permissions.BasePermission):
    """
    Разрешения на основе отдела сотрудника.
    """

    def has_permission(self, request, view):
        # Проверяем базовые разрешения
        if not request.user or not request.user.is_authenticated:
            return False

        # Суперпользователи имеют все права
        if request.user.is_superuser:
            return True

        # Проверяем профиль сотрудника
        try:
            employee = request.user.employee_profile

            if not employee.is_active:
                return False

            # Разные отделы - разные права
            department = employee.department.lower()

            # Администраторы - полный доступ
            if department in ["администрация", "administration", "руководство"]:
                return True

            # Отдел продаж - доступ к сети и продуктам
            elif department in ["продажи", "sales", "торговый отдел"]:
                # Разрешаем все методы кроме DELETE
                return request.method != "DELETE"

            # Отдел аналитики - только чтение
            elif department in ["аналитика", "analytics", "отдел анализа"]:
                return request.method in permissions.SAFE_METHODS

            # Остальные - только безопасные методы
            else:
                return request.method in permissions.SAFE_METHODS

        except Employee.DoesNotExist:
            return False
