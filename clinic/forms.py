from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import (
    Appointment,
    CustomerProfile,
    Order,
    OrderItem,
    PromoCode,
    Review,
    Service,
    validate_human_birth_date,
)


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=80)
    last_name = forms.CharField(label="Фамилия", max_length=80)
    email = forms.EmailField(label="Email")
    birth_date = forms.DateField(
        label="Дата рождения",
        validators=[validate_human_birth_date],
        widget=forms.DateInput(attrs={"type": "date", "max": timezone.localdate().isoformat()}),
    )
    address = forms.CharField(label="Адрес", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20, help_text="Формат: +375291234567")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "birth_date", "address", "phone")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                full_name=f"{user.last_name} {user.first_name}".strip() or user.username,
                birth_date=self.cleaned_data["birth_date"],
                address=self.cleaned_data["address"],
                phone=self.cleaned_data["phone"],
            )
        return user


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("author_name", "rating", "text")
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "text": forms.Textarea(attrs={"rows": 4}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "category", "description", "price", "duration_minutes", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "duration_minutes": forms.NumberInput(attrs={"min": 5, "max": 480}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("pet", "doctor", "planned_at", "reason", "services")
        widgets = {
            "planned_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "reason": forms.TextInput(attrs={"maxlength": 255}),
            "services": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_staff and hasattr(user, "customer_profile"):
            self.fields["pet"].queryset = user.customer_profile.pets.all()
        self.fields["services"].queryset = Service.objects.filter(is_active=True)


class OrderForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        label="Услуги",
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Order
        fields = ("pet", "doctor", "visit_at", "discount_code", "notes", "services")
        widgets = {
            "visit_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["services"].queryset = Service.objects.filter(is_active=True)
        self.fields["discount_code"].queryset = PromoCode.objects.filter(
            is_active=True,
            valid_until__gte=timezone.localdate(),
        )
        if user and hasattr(user, "customer_profile"):
            self.fields["pet"].queryset = user.customer_profile.pets.all()

    def clean_services(self):
        services = self.cleaned_data["services"]
        if not services:
            raise forms.ValidationError("Выберите хотя бы одну услугу.")
        return services

    @transaction.atomic
    def save_for_customer(self, customer):
        order = super().save(commit=False)
        order.customer = customer
        order.save()
        for service in self.cleaned_data["services"]:
            OrderItem.objects.create(order=order, service=service, quantity=1, price=service.price)
        return order
