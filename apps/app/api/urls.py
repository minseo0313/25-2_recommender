from django.urls import path
from . import views

urlpatterns = [
    path("onboarding/", views.onboarding, name="onboarding"),  # POST
    path("recommendations/<int:session_id>/", views.recommendations, name="recommendations"),  # GET
]
