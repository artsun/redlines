from django.urls import path
from . import views

urlpatterns = [
    path('', views.ArtListPage.as_view()),  # /editor/
    path('new', views.RubricPage.as_view()),
    path('icon', views.IconMake.as_view()),
    path('slider', views.SliderMake.as_view()),
    path('uploadFile', views.Uploader.as_view()),
    path('<str:trans_title>', views.Editor.as_view()),    
]
