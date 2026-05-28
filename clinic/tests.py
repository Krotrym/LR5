from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import CustomerRegistrationForm
from .models import Service, ServiceCategory


class PublicPageTests(TestCase):
    def test_required_public_pages_open(self):
        for name in [
            "home",
            "about",
            "news_list",
            "glossary",
            "contacts",
            "privacy",
            "vacancies",
            "reviews",
            "coupons",
            "service_list",
            "stats",
            "time_info",
        ]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)


class ValidationTests(TestCase):
    def test_registration_rejects_future_birth_date(self):
        form = CustomerRegistrationForm(
            data={
                "username": "future",
                "first_name": "Test",
                "last_name": "User",
                "email": "future@example.com",
                "birth_date": "2999-01-01",
                "address": "Минск",
                "phone": "+375291234567",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)

    def test_service_model_rejects_negative_price(self):
        category = ServiceCategory.objects.create(name="Диагностика", description="Тест")
        service = Service(
            name="Ошибочная услуга",
            category=category,
            description="Цена невалидна",
            price=Decimal("-1.00"),
            duration_minutes=30,
        )
        with self.assertRaises(ValidationError):
            service.full_clean()


class ServiceCrudTests(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(name="Терапия", description="Приемы")
        self.staff = User.objects.create_user("staff", password="pass12345", is_staff=True)

    def test_anonymous_cannot_create_service(self):
        response = self.client.get(reverse("service_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_staff_can_create_update_and_delete_service(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("service_create"),
            {
                "name": "Первичный прием",
                "category": self.category.pk,
                "description": "Осмотр питомца",
                "price": "42.00",
                "duration_minutes": 30,
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("service_list"))
        service = Service.objects.get(name="Первичный прием")

        response = self.client.post(
            reverse("service_update", args=[service.pk]),
            {
                "name": "Повторный прием",
                "category": self.category.pk,
                "description": "Контроль лечения",
                "price": "35.00",
                "duration_minutes": 25,
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("service_detail", args=[service.pk]))
        service.refresh_from_db()
        self.assertEqual(service.name, "Повторный прием")

        response = self.client.post(reverse("service_delete", args=[service.pk]))
        self.assertRedirects(response, reverse("service_list"))
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())
