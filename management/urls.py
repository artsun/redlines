from django.urls import path
from . import views


urlpatterns = [
    path('', views.LoginPage.as_view()),
    path('logout', views.LogoutPage.as_view()),
]
