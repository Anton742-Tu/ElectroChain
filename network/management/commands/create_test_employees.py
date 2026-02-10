from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from network.models import Employee


class Command(BaseCommand):
    help = "Создает тестовых сотрудников для проверки прав доступа"

    def handle(self, *args, **options):
        # Создаем тестовых сотрудников

        # Администратор
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@electrochain.ru",
                "first_name": "Алексей",
                "last_name": "Петров",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            Employee.objects.create(
                user=admin_user, department="Администрация", position="Главный администратор", is_active=True
            )
            self.stdout.write(self.style.SUCCESS("Создан администратор: admin / admin123"))

        # Менеджер отдела продаж
        sales_user, created = User.objects.get_or_create(
            username="sales_manager",
            defaults={
                "email": "sales@electrochain.ru",
                "first_name": "Мария",
                "last_name": "Иванова",
                "is_staff": True,
            },
        )
        if created:
            sales_user.set_password("sales123")
            sales_user.save()
            Employee.objects.create(
                user=sales_user, department="Продажи", position="Менеджер по продажам", is_active=True
            )
            self.stdout.write(self.style.SUCCESS("Создан менеджер продаж: sales_manager / sales123"))

        # Аналитик
        analyst_user, created = User.objects.get_or_create(
            username="analyst",
            defaults={
                "email": "analyst@electrochain.ru",
                "first_name": "Дмитрий",
                "last_name": "Сидоров",
                "is_staff": True,
            },
        )
        if created:
            analyst_user.set_password("analyst123")
            analyst_user.save()
            Employee.objects.create(
                user=analyst_user, department="Аналитика", position="Старший аналитик", is_active=True
            )
            self.stdout.write(self.style.SUCCESS("Создан аналитик: analyst / analyst123"))

        # Неактивный сотрудник
        inactive_user, created = User.objects.get_or_create(
            username="inactive",
            defaults={
                "email": "inactive@electrochain.ru",
                "first_name": "Ольга",
                "last_name": "Кузнецова",
                "is_staff": True,
            },
        )
        if created:
            inactive_user.set_password("inactive123")
            inactive_user.save()
            Employee.objects.create(
                user=inactive_user,
                department="Техническая поддержка",
                position="Специалист",
                is_active=False,  # Неактивный!
            )
            self.stdout.write(self.style.SUCCESS("Создан неактивный сотрудник: inactive / inactive123"))

        self.stdout.write(self.style.SUCCESS("Тестовые сотрудники созданы успешно!"))
