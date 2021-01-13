from django.urls import path
from . import views

urlpatterns = [
	path('', views.IndexPage.as_view()),
    path('<str:trans_title>', views.NewsPage.as_view()),
]
