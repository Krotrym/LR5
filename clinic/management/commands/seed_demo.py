from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from clinic.models import (
    Appointment,
    CompanyInfo,
    CustomerProfile,
    Department,
    Diagnosis,
    Doctor,
    DoctorCategory,
    EmployeeContact,
    GlossaryTerm,
    NewsArticle,
    Order,
    OrderItem,
    Pet,
    PromoCode,
    Review,
    Service,
    ServiceCategory,
    Specialization,
    Vacancy,
)


class Command(BaseCommand):
    help = "Fill the database with demo data for LR5."

    def handle(self, *args, **options):
        admin = self._user("admin", "admin@example.com", "Администратор", "Клиники", staff=True, superuser=True)
        self.stdout.write(f"Admin user: {admin.username} / admin12345")

        self._company()
        self._news()
        self._glossary()
        self._contacts()
        self._vacancies()
        promos = self._promos()
        departments = self._departments()
        categories = self._doctor_categories()
        specializations = self._specializations()
        doctors = self._doctors(categories, departments, specializations)
        service_categories = self._service_categories()
        services = self._services(service_categories)
        customers = self._customers()
        pets = self._pets(customers)
        self._diagnoses(pets, doctors)
        self._appointments(pets, doctors, services)
        orders = self._orders(customers, pets, doctors, promos)
        self._order_items(orders, services)
        self._reviews(customers)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    def _user(self, username, email, first_name, last_name, staff=False, superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": staff,
                "is_superuser": superuser,
            },
        )
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = staff
        user.is_superuser = superuser
        if created:
            user.set_password("admin12345" if superuser else "client12345")
        user.save()
        return user

    def _company(self):
        for i in range(10):
            CompanyInfo.objects.update_or_create(
                name=f"VetCare этап {i + 1}",
                defaults={
                    "description": f"Развитие клиники: направление {i + 1}, расширение услуг и оборудования.",
                    "history_year": 2015 + i,
                    "requisites": f"УНП 19345{i:04d}, Минск, ул. Заботы, {i + 1}",
                    "logo_url": f"https://picsum.photos/seed/vet-logo-{i}/300/220",
                },
            )

    def _news(self):
        for i in range(10):
            NewsArticle.objects.update_or_create(
                title=f"Новость клиники #{i + 1}",
                defaults={
                    "summary": f"Краткое сообщение о работе ветклиники и полезной услуге #{i + 1}.",
                    "content": f"Полная новость: врачи клиники обновили рекомендации для владельцев питомцев по теме #{i + 1}.",
                    "image_url": f"https://picsum.photos/seed/vet-news-{i}/900/520",
                    "published_at": timezone.now() - timedelta(days=i),
                },
            )

    def _glossary(self):
        terms = [
            "Анамнез",
            "Вакцинация",
            "Диагноз",
            "Кастрация",
            "Стерилизация",
            "УЗИ",
            "Чипирование",
            "Дегельминтизация",
            "Терапия",
            "Хирургия",
        ]
        for i, term in enumerate(terms):
            GlossaryTerm.objects.update_or_create(
                term=term,
                defaults={
                    "definition": f"Учебное определение термина '{term}' для словаря ветеринарной клиники.",
                    "added_at": timezone.localdate() - timedelta(days=i),
                },
            )

    def _contacts(self):
        positions = ["Администратор", "Терапевт", "Хирург", "Ассистент", "Лаборант"]
        for i in range(10):
            EmployeeContact.objects.update_or_create(
                full_name=f"Сотрудник Контактный {i + 1}",
                defaults={
                    "position": positions[i % len(positions)],
                    "work_description": f"Отвечает за направление работы клиники #{i + 1}.",
                    "phone": f"+37529{1000000 + i:07d}",
                    "email": f"employee{i + 1}@vetcare.local",
                    "photo_url": f"https://i.pravatar.cc/320?img={i + 1}",
                },
            )

    def _vacancies(self):
        for i in range(10):
            Vacancy.objects.update_or_create(
                title=f"Вакансия #{i + 1}",
                defaults={
                    "description": f"Открытая позиция для работы с пациентами и клиентами клиники #{i + 1}.",
                    "salary_from": Decimal("1200.00") + i * Decimal("80.00"),
                    "salary_to": Decimal("1800.00") + i * Decimal("100.00"),
                    "is_active": True,
                },
            )

    def _promos(self):
        promos = []
        for i in range(10):
            promo, _ = PromoCode.objects.update_or_create(
                code=f"PET{i + 1:02d}",
                defaults={
                    "description": f"Скидка на услугу или профилактический прием #{i + 1}.",
                    "discount_percent": 5 + i,
                    "valid_until": timezone.localdate() + timedelta(days=30 + i),
                    "is_active": True,
                },
            )
            promos.append(promo)
        return promos

    def _departments(self):
        departments = []
        for i in range(10):
            department, _ = Department.objects.update_or_create(
                name=f"Отделение #{i + 1}",
                defaults={"room": f"{100 + i}", "phone": f"+37533{2000000 + i:07d}"},
            )
            departments.append(department)
        return departments

    def _doctor_categories(self):
        categories = []
        for i in range(10):
            category, _ = DoctorCategory.objects.update_or_create(
                name=f"Категория врача #{i + 1}",
                defaults={"description": f"Квалификационная категория врача уровня #{i + 1}."},
            )
            categories.append(category)
        return categories

    def _specializations(self):
        names = [
            "Терапия",
            "Хирургия",
            "Дерматология",
            "Кардиология",
            "Стоматология",
            "Офтальмология",
            "Диагностика",
            "Реабилитация",
            "Онкология",
            "Неврология",
        ]
        specializations = []
        for name in names:
            specialization, _ = Specialization.objects.update_or_create(name=name)
            specializations.append(specialization)
        return specializations

    def _doctors(self, categories, departments, specializations):
        doctors = []
        for i in range(10):
            user = self._user(
                f"doctor{i + 1}",
                f"doctor{i + 1}@vetcare.local",
                f"Доктор{i + 1}",
                "Вет",
                staff=True,
            )
            doctor, _ = Doctor.objects.update_or_create(
                full_name=f"Врач Ветеринарный {i + 1}",
                defaults={
                    "user": user,
                    "category": categories[i],
                    "department": departments[i],
                    "phone": f"+37544{3000000 + i:07d}",
                    "email": f"doctor{i + 1}@vetcare.local",
                    "photo_url": f"https://i.pravatar.cc/320?img={20 + i}",
                },
            )
            doctor.specializations.set([specializations[i], specializations[(i + 1) % len(specializations)]])
            doctors.append(doctor)
        return doctors

    def _service_categories(self):
        categories = []
        for i in range(10):
            category, _ = ServiceCategory.objects.update_or_create(
                name=f"Категория услуг #{i + 1}",
                defaults={"description": f"Группа ветеринарных услуг #{i + 1}."},
            )
            categories.append(category)
        return categories

    def _services(self, categories):
        services = []
        for i in range(10):
            service, _ = Service.objects.update_or_create(
                name=f"Услуга #{i + 1}",
                category=categories[i],
                defaults={
                    "description": f"Описание ветеринарной услуги #{i + 1}: консультация, диагностика и рекомендации.",
                    "price": Decimal("25.00") + i * Decimal("7.50"),
                    "duration_minutes": 20 + i * 5,
                    "is_active": True,
                },
            )
            services.append(service)
        return services

    def _customers(self):
        customers = []
        for i in range(10):
            user = self._user(
                f"client{i + 1}",
                f"client{i + 1}@example.com",
                f"Клиент{i + 1}",
                "Питомцев",
            )
            customer, _ = CustomerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": f"Питомцев Клиент {i + 1}",
                    "birth_date": date(1985 + i % 12, 5, 10),
                    "address": f"Минск, ул. Клиентская, {i + 1}",
                    "phone": f"+37525{4000000 + i:07d}",
                },
            )
            customers.append(customer)
        return customers

    def _pets(self, customers):
        pets = []
        species = ["кот", "собака", "кролик", "попугай", "хорек"]
        for i, customer in enumerate(customers):
            pet, _ = Pet.objects.update_or_create(
                owner=customer,
                name=f"Пациент {i + 1}",
                defaults={
                    "species": species[i % len(species)],
                    "breed": f"Порода #{i + 1}",
                    "birth_date": date(2018 + i % 5, 3, 12),
                    "weight_kg": Decimal("3.50") + i,
                },
            )
            pets.append(pet)
        return pets

    def _diagnoses(self, pets, doctors):
        for i in range(10):
            diagnosis, _ = Diagnosis.objects.update_or_create(
                name=f"Диагноз #{i + 1}",
                defaults={"description": f"Учебное описание диагноза и плана лечения #{i + 1}."},
            )
            diagnosis.pets.set([pets[i]])
            diagnosis.doctors.set([doctors[i], doctors[(i + 1) % len(doctors)]])

    def _appointments(self, pets, doctors, services):
        for i in range(10):
            appointment, _ = Appointment.objects.update_or_create(
                pet=pets[i],
                doctor=doctors[i],
                reason=f"Плановый прием #{i + 1}",
                defaults={"planned_at": timezone.now() + timedelta(days=i + 1, hours=i), "status": "planned"},
            )
            appointment.services.set([services[i]])

    def _orders(self, customers, pets, doctors, promos):
        orders = []
        for i in range(10):
            order, _ = Order.objects.update_or_create(
                customer=customers[i],
                pet=pets[i],
                doctor=doctors[i],
                notes=f"Учебный заказ и продажа услуг #{i + 1}.",
                defaults={
                    "visit_at": timezone.now() - timedelta(days=i),
                    "status": "completed" if i % 2 == 0 else "paid",
                    "discount_code": promos[i],
                },
            )
            orders.append(order)
        return orders

    def _order_items(self, orders, services):
        for i, order in enumerate(orders):
            OrderItem.objects.update_or_create(
                order=order,
                service=services[i],
                defaults={"quantity": 1 + i % 3, "price": services[i].price},
            )

    def _reviews(self, customers):
        for i, customer in enumerate(customers):
            Review.objects.update_or_create(
                user=customer.user,
                author_name=customer.full_name,
                defaults={
                    "rating": 4 + i % 2,
                    "text": f"Отзыв #{i + 1}: прием прошел аккуратно, врач объяснил план лечения.",
                },
            )
