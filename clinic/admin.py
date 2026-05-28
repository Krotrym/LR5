from django.contrib import admin

from .models import (
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


class TimeStampedAdminMixin:
    readonly_fields = ("created_at_utc", "created_at_local", "updated_at_utc", "updated_at_local")


class PetInline(admin.TabularInline):
    model = Pet
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ("service",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("full_name", "phone", "birth_date", "user")
    search_fields = ("full_name", "phone", "user__username")
    inlines = (PetInline,)


@admin.register(Pet)
class PetAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "owner", "species", "breed", "birth_date", "weight_kg")
    list_filter = ("species", "breed")
    search_fields = ("name", "owner__full_name")


@admin.register(Service)
class ServiceAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "price", "duration_minutes", "is_active")
    list_filter = ("category", "is_active")
    list_editable = ("price", "is_active")
    search_fields = ("name", "description")


@admin.register(Order)
class OrderAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "customer", "pet", "doctor", "visit_at", "status", "total")
    list_filter = ("status", "doctor", "visit_at")
    autocomplete_fields = ("customer", "pet", "doctor", "discount_code")
    inlines = (OrderItemInline,)


@admin.register(Appointment)
class AppointmentAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("pet", "doctor", "planned_at", "status", "reason")
    list_filter = ("status", "doctor", "planned_at")
    filter_horizontal = ("services",)
    search_fields = ("pet__name", "doctor__full_name", "reason")


@admin.register(Doctor)
class DoctorAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("full_name", "category", "department", "phone", "email")
    list_filter = ("category", "department", "specializations")
    filter_horizontal = ("specializations",)
    search_fields = ("full_name", "phone", "email")


@admin.register(PromoCode)
class PromoCodeAdmin(TimeStampedAdminMixin, admin.ModelAdmin):
    list_display = ("code", "discount_percent", "valid_until", "is_active")
    list_filter = ("is_active", "valid_until")
    search_fields = ("code", "description")


for model in (
    CompanyInfo,
    Department,
    Diagnosis,
    DoctorCategory,
    EmployeeContact,
    GlossaryTerm,
    NewsArticle,
    Review,
    ServiceCategory,
    Specialization,
    Vacancy,
):
    admin.site.register(model)
