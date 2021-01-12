from django.urls import path
from . import views

urlpatterns = [
    path('', views.ArtListPage.as_view()),
    path('newarticle', views.RubricPage.as_view()),
    path('editor/<str:trans_title>', views.Editor.as_view()),
    path('uploadFile', views.Uploader.as_view()),
    path('slider', views.SliderMake.as_view()),
    #path('editor/<str:trans_title>/slider', views.SliderMake.as_view()),
]
