import io
import logging
from decimal import Decimal
from statistics import StatisticsError, mean, median, mode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .external_api import load_external_widgets
from .forms import AppointmentForm, CustomerRegistrationForm, OrderForm, ReviewForm, ServiceForm
from .models import (
    Appointment,
    CompanyInfo,
    CustomerProfile,
    Doctor,
    EmployeeContact,
    GlossaryTerm,
    NewsArticle,
    Order,
    OrderItem,
    PromoCode,
    Review,
    Service,
    ServiceCategory,
    Vacancy,
)


logger = logging.getLogger(__name__)


def staff_required(view_func):
    return user_passes_test(lambda user: user.is_authenticated and (user.is_staff or user.is_superuser))(view_func)


def home(request):
    latest_news = NewsArticle.objects.first()
    services = Service.objects.filter(is_active=True).select_related("category")[:6]
    reviews = Review.objects.select_related("user")[:3]
    return render(
        request,
        "clinic/home.html",
        {
            "latest_news": latest_news,
            "services": services,
            "reviews": reviews,
        },
    )


def about(request):
    facts = CompanyInfo.objects.all()
    return render(request, "clinic/about.html", {"facts": facts})


def news_list(request):
    news = NewsArticle.objects.all()
    return render(request, "clinic/news_list.html", {"news": news})


def glossary(request):
    terms = GlossaryTerm.objects.all()
    return render(request, "clinic/glossary.html", {"terms": terms})


def contacts(request):
    employees = EmployeeContact.objects.all()
    return render(request, "clinic/contacts.html", {"employees": employees})


def privacy(request):
    return render(request, "clinic/privacy.html")


def vacancies(request):
    items = Vacancy.objects.filter(is_active=True)
    return render(request, "clinic/vacancies.html", {"vacancies": items})


def coupons(request):
    codes = PromoCode.objects.all()
    return render(request, "clinic/coupons.html", {"codes": codes})


def reviews(request):
    items = Review.objects.select_related("user")
    return render(request, "clinic/reviews.html", {"reviews": items})


@login_required
def review_create(request):
    initial_name = request.user.get_full_name() or request.user.username
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.author_name = form.cleaned_data.get("author_name") or initial_name
            review.save()
            messages.success(request, "Отзыв добавлен. Спасибо!")
            logger.info("Review created by user %s", request.user.username)
            return redirect("reviews")
    else:
        form = ReviewForm(initial={"author_name": initial_name})
    return render(request, "clinic/review_form.html", {"form": form})


def service_list(request):
    services = Service.objects.filter(is_active=True).select_related("category")
    categories = ServiceCategory.objects.all()
    return render(
        request,
        "clinic/service_list.html",
        {
            "services": services,
            "categories": categories,
        },
    )


def service_detail(request, pk):
    service = get_object_or_404(Service.objects.select_related("category"), pk=pk)
    return render(request, "clinic/service_detail.html", {"service": service})


@staff_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Услуга создана.")
            logger.info("Service created by %s", request.user.username)
            return redirect("service_list")
    else:
        form = ServiceForm()
    return render(request, "clinic/service_form.html", {"form": form, "title": "Новая услуга"})


@staff_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Услуга обновлена.")
            logger.info("Service %s updated by %s", service.pk, request.user.username)
            return redirect("service_detail", pk=service.pk)
    else:
        form = ServiceForm(instance=service)
    return render(request, "clinic/service_form.html", {"form": form, "title": "Редактирование услуги"})


@staff_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Услуга удалена.")
        logger.info("Service %s deleted by %s", pk, request.user.username)
        return redirect("service_list")
    return render(request, "clinic/service_confirm_delete.html", {"service": service})


def doctors(request):
    items = Doctor.objects.select_related("category", "department").prefetch_related("specializations")
    return render(request, "clinic/doctors.html", {"doctors": items})


@login_required
def appointments(request):
    if request.user.is_staff or request.user.is_superuser:
        items = Appointment.objects.select_related("pet", "doctor", "pet__owner").prefetch_related("services")
    elif hasattr(request.user, "customer_profile"):
        items = Appointment.objects.filter(pet__owner=request.user.customer_profile).select_related("pet", "doctor")
    else:
        items = Appointment.objects.none()
    return render(request, "clinic/appointments.html", {"appointments": items})


@login_required
def appointment_create(request):
    if not hasattr(request.user, "customer_profile") and not request.user.is_staff:
        messages.error(request, "Для записи нужен профиль клиента.")
        return redirect("profile")
    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, "Посещение запланировано.")
            logger.info("Appointment %s created by %s", appointment.pk, request.user.username)
            return redirect("appointments")
    else:
        form = AppointmentForm(user=request.user)
    return render(request, "clinic/appointment_form.html", {"form": form})


@login_required
def order_create(request):
    if not hasattr(request.user, "customer_profile"):
        messages.error(request, "Покупка услуг доступна после регистрации клиентского профиля.")
        return redirect("profile")
    customer = request.user.customer_profile
    if request.method == "POST":
        form = OrderForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save_for_customer(customer)
            messages.success(request, f"Заказ #{order.pk} создан.")
            logger.info("Order %s created by %s", order.pk, request.user.username)
            return redirect("profile")
    else:
        form = OrderForm(user=request.user)
    return render(request, "clinic/order_form.html", {"form": form})


def external_api(request):
    widgets = load_external_widgets()
    return render(request, "clinic/external_api.html", widgets)


def _statistics_context():
    prices = [service.price for service in Service.objects.filter(is_active=True)]
    price_values = [float(price) for price in prices]
    avg_price = mean(price_values) if price_values else 0
    median_price = median(price_values) if price_values else 0
    try:
        mode_price = mode(price_values) if price_values else 0
    except StatisticsError:
        mode_price = "нет единственной моды"

    line_total = ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField(max_digits=12, decimal_places=2))
    category_sales = list(
        OrderItem.objects.values("service__category__name")
        .annotate(total=Sum(line_total), quantity=Sum("quantity"))
        .order_by("-total")
    )
    popular_service = (
        OrderItem.objects.values("service__name")
        .annotate(quantity=Sum("quantity"))
        .order_by("-quantity")
        .first()
    )
    revenue = sum((row["total"] or Decimal("0.00") for row in category_sales), Decimal("0.00"))
    return {
        "avg_price": avg_price,
        "median_price": median_price,
        "mode_price": mode_price,
        "category_sales": category_sales,
        "popular_service": popular_service,
        "revenue": revenue,
    }


def stats(request):
    return render(request, "clinic/stats.html", _statistics_context())


def stats_chart(request):
    from PIL import Image, ImageDraw, ImageFont

    context = _statistics_context()
    rows = context["category_sales"]
    labels = [row["service__category__name"] for row in rows] or ["No sales"]
    values = [float(row["total"] or 0) for row in rows] or [0]
    max_value = max(values) or 1
    width, height = 900, 460
    margin_left, margin_top, margin_bottom = 80, 60, 70
    plot_width = width - margin_left - 40
    plot_height = height - margin_top - margin_bottom
    bar_gap = 12
    bar_width = max(24, (plot_width - bar_gap * (len(values) - 1)) // len(values))
    colors = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#65a30d"]

    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin_left, 24), "Revenue by service category, BYN", fill="#172033", font=font)
    draw.line((margin_left, margin_top, margin_left, height - margin_bottom), fill="#657086", width=2)
    draw.line((margin_left, height - margin_bottom, width - 30, height - margin_bottom), fill="#657086", width=2)

    for index, value in enumerate(values):
        x1 = margin_left + index * (bar_width + bar_gap)
        bar_height = int((value / max_value) * (plot_height - 20))
        y1 = height - margin_bottom - bar_height
        x2 = x1 + bar_width
        y2 = height - margin_bottom
        draw.rectangle((x1, y1, x2, y2), fill=colors[index % len(colors)])
        draw.text((x1, y1 - 18), f"{value:.0f}", fill="#172033", font=font)
        label = labels[index][:10]
        draw.text((x1, height - margin_bottom + 10), label, fill="#172033", font=font)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def time_info(request):
    return render(request, "clinic/time_info.html")


def register(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация завершена.")
            logger.info("User registered: %s", user.username)
            return redirect("profile")
    else:
        form = CustomerRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    customer = CustomerProfile.objects.filter(user=request.user).first()
    orders = Order.objects.filter(customer=customer).prefetch_related("items__service") if customer else Order.objects.none()
    appointments_qs = Appointment.objects.filter(pet__owner=customer).select_related("pet", "doctor") if customer else Appointment.objects.none()
    return render(
        request,
        "clinic/profile.html",
        {
            "customer": customer,
            "orders": orders,
            "appointments": appointments_qs,
        },
    )
