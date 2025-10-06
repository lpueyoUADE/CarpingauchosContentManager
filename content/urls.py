from django.urls import path
from . import views

urlpatterns = [
    path("generate_key/<str:model>/", views.generate_key, name="generate_key"),
]