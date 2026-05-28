from django.urls import path, re_path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("news/", views.news_list, name="news_list"),
    path("glossary/", views.glossary, name="glossary"),
    path("contacts/", views.contacts, name="contacts"),
    path("privacy/", views.privacy, name="privacy"),
    path("vacancies/", views.vacancies, name="vacancies"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/new/", views.review_create, name="review_create"),
    path("coupons/", views.coupons, name="coupons"),
    path("doctors/", views.doctors, name="doctors"),
    path("appointments/", views.appointments, name="appointments"),
    path("appointments/new/", views.appointment_create, name="appointment_create"),
    path("orders/new/", views.order_create, name="order_create"),
    path("external-api/", views.external_api, name="external_api"),
    path("stats/", views.stats, name="stats"),
    path("stats/chart.png", views.stats_chart, name="stats_chart"),
    path("time/", views.time_info, name="time_info"),
    path("accounts/register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("services/", views.service_list, name="service_list"),
    path("services/new/", views.service_create, name="service_create"),
    re_path(r"^services/(?P<pk>[0-9]+)/$", views.service_detail, name="service_detail"),
    re_path(r"^services/(?P<pk>[0-9]+)/edit/$", views.service_update, name="service_update"),
    re_path(r"^services/(?P<pk>[0-9]+)/delete/$", views.service_delete, name="service_delete"),
]
