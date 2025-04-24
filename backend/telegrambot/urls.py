from django.urls import path
from . import views

urlpatterns = [
    path("transact/", views.transfer_funds, name='transfer_funds')
]