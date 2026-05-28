from datetime import date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r"^\+375\s?(?:25|29|33|44)\s?\d{3}[- ]?\d{2}[- ]?\d{2}$",
    message="Телефон должен быть в формате +375291234567.",
)


def _age(value: date) -> int:
    today = timezone.localdate()
    return today.year - value.year - ((today.month, today.day) < (value.month, value.day))


def validate_human_birth_date(value: date) -> None:
    if value > timezone.localdate():
        raise ValidationError("Дата рождения не может быть в будущем.")
    if _age(value) < 14:
        raise ValidationError("Пользователь должен быть старше 14 лет.")
    if _age(value) > 120:
        raise ValidationError("Проверьте дату рождения: возраст больше 120 лет.")


def validate_not_future_date(value: date) -> None:
    if value > timezone.localdate():
        raise ValidationError("Дата не может быть в будущем.")


class TimeStampedModel(models.Model):
    created_at_utc = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    created_at_local = models.DateTimeField(editable=False, null=True, blank=True)
    updated_at_utc = models.DateTimeField(default=timezone.now, editable=False)
    updated_at_local = models.DateTimeField(editable=False, null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        now_utc = timezone.now()
        local_tz = ZoneInfo(settings.TIME_ZONE)
        if not self.created_at_utc:
            self.created_at_utc = now_utc
        self.created_at_local = timezone.localtime(self.created_at_utc, local_tz)
        self.updated_at_utc = now_utc
        self.updated_at_local = timezone.localtime(now_utc, local_tz)
        self.full_clean()
        super().save(*args, **kwargs)


class CompanyInfo(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    description = models.TextField()
    history_year = models.PositiveIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    requisites = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True)

    class Meta:
        ordering = ["history_year", "name"]
        verbose_name = "сведения о компании"
        verbose_name_plural = "сведения о компании"

    def __str__(self):
        return f"{self.history_year}: {self.name}"


class NewsArticle(TimeStampedModel):
    title = models.CharField(max_length=180)
    summary = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField()
    published_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "новость"
        verbose_name_plural = "новости"

    def __str__(self):
        return self.title


class GlossaryTerm(TimeStampedModel):
    term = models.CharField(max_length=120, unique=True)
    definition = models.TextField()
    added_at = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["term"]
        verbose_name = "термин"
        verbose_name_plural = "словарь терминов"

    def __str__(self):
        return self.term


class EmployeeContact(TimeStampedModel):
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=120)
    work_description = models.TextField()
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField()
    photo_url = models.URLField()

    class Meta:
        ordering = ["full_name"]
        verbose_name = "контакт сотрудника"
        verbose_name_plural = "контакты сотрудников"

    def __str__(self):
        return f"{self.full_name}, {self.position}"


class Vacancy(TimeStampedModel):
    title = models.CharField(max_length=150)
    description = models.TextField()
    salary_from = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    salary_to = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "вакансия"
        verbose_name_plural = "вакансии"

    def clean(self):
        if self.salary_to < self.salary_from:
            raise ValidationError("Верхняя граница зарплаты не может быть меньше нижней.")

    def __str__(self):
        return self.title


class PromoCode(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255)
    discount_percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(90)])
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_until", "code"]
        verbose_name = "промокод"
        verbose_name_plural = "промокоды и купоны"

    @property
    def is_valid_now(self):
        return self.is_active and self.valid_until >= timezone.localdate()

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"


class Review(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()

    class Meta:
        ordering = ["-created_at_utc"]
        verbose_name = "отзыв"
        verbose_name_plural = "отзывы"

    def __str__(self):
        return f"{self.author_name}: {self.rating}/5"


class Department(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    room = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, validators=[phone_validator])

    class Meta:
        ordering = ["name"]
        verbose_name = "отделение"
        verbose_name_plural = "отделения"

    def __str__(self):
        return self.name


class DoctorCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()

    class Meta:
        ordering = ["name"]
        verbose_name = "категория врача"
        verbose_name_plural = "категории врачей"

    def __str__(self):
        return self.name


class Specialization(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "специализация"
        verbose_name_plural = "специализации врачей"

    def __str__(self):
        return self.name


class Doctor(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    category = models.ForeignKey(DoctorCategory, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    specializations = models.ManyToManyField(Specialization, related_name="doctors")
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField()
    photo_url = models.URLField()

    class Meta:
        ordering = ["full_name"]
        verbose_name = "врач"
        verbose_name_plural = "врачи"

    def __str__(self):
        return self.full_name


class ServiceCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField()

    class Meta:
        ordering = ["name"]
        verbose_name = "категория услуги"
        verbose_name_plural = "категории услуг"

    def __str__(self):
        return self.name


class Service(TimeStampedModel):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="services")
    description = models.TextField()
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(5), MaxValueValidator(480)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]
        unique_together = ["name", "category"]
        verbose_name = "услуга"
        verbose_name_plural = "услуги"

    def __str__(self):
        return f"{self.name} - {self.price} BYN"


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    full_name = models.CharField(max_length=150)
    birth_date = models.DateField(validators=[validate_human_birth_date])
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, validators=[phone_validator])

    class Meta:
        ordering = ["full_name"]
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

    def __str__(self):
        return self.full_name


class Pet(TimeStampedModel):
    owner = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=80)
    species = models.CharField(max_length=80)
    breed = models.CharField(max_length=120)
    birth_date = models.DateField(validators=[validate_not_future_date])
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.10"))])

    class Meta:
        ordering = ["owner__full_name", "name"]
        unique_together = ["owner", "name"]
        verbose_name = "питомец"
        verbose_name_plural = "домашние животные"

    def __str__(self):
        return f"{self.name} ({self.species})"


class Diagnosis(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    pets = models.ManyToManyField(Pet, blank=True, related_name="diagnoses")
    doctors = models.ManyToManyField(Doctor, blank=True, related_name="diagnoses")

    class Meta:
        ordering = ["name"]
        verbose_name = "диагноз"
        verbose_name_plural = "диагнозы"

    def __str__(self):
        return self.name


class Appointment(TimeStampedModel):
    STATUS_CHOICES = [
        ("planned", "Запланирован"),
        ("done", "Завершен"),
        ("canceled", "Отменен"),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    planned_at = models.DateTimeField(db_index=True)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    services = models.ManyToManyField(Service, blank=True, related_name="appointments")

    class Meta:
        ordering = ["planned_at", "pet__name"]
        verbose_name = "планируемое посещение"
        verbose_name_plural = "планируемые посещения"

    def clean(self):
        if self.planned_at and self.planned_at < timezone.now() - timedelta(days=1):
            raise ValidationError("Планируемое посещение не может быть в далеком прошлом.")

    def __str__(self):
        return f"{self.pet} -> {self.doctor} {self.planned_at:%d/%m/%Y %H:%M}"


class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("paid", "Оплачен"),
        ("completed", "Выполнен"),
        ("canceled", "Отменен"),
    ]

    customer = models.ForeignKey(CustomerProfile, on_delete=models.PROTECT, related_name="orders")
    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, related_name="orders")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="orders")
    visit_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)
    discount_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    services = models.ManyToManyField(Service, through="OrderItem", related_name="orders")

    class Meta:
        ordering = ["-visit_at"]
        verbose_name = "продажа/заказ"
        verbose_name_plural = "продажи и заказы"

    def clean(self):
        if self.pet_id and self.customer_id and self.pet.owner_id != self.customer_id:
            raise ValidationError("Питомец должен принадлежать выбранному клиенту.")
        if self.visit_at and self.visit_at > timezone.now() + timedelta(days=365):
            raise ValidationError("Дата заказа слишком далеко в будущем.")

    @property
    def total_before_discount(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    @property
    def total(self):
        total = self.total_before_discount
        if self.discount_code and self.discount_code.is_valid_now:
            total -= total * Decimal(self.discount_code.discount_percent) / Decimal("100")
        return total.quantize(Decimal("0.01"))

    def __str__(self):
        return f"Заказ #{self.pk or 'new'} для {self.customer}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])

    class Meta:
        unique_together = ["order", "service"]
        verbose_name = "строка заказа"
        verbose_name_plural = "строки заказов"

    @property
    def line_total(self):
        return self.price * self.quantity

    def clean(self):
        if self.service_id and not self.price:
            self.price = self.service.price

    def __str__(self):
        return f"{self.service} x {self.quantity}"
