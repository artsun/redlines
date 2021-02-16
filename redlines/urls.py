
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from django.conf import settings

urlpatterns = [
    path('login', include('management.urls')),
    path('auth/', include('management.urls')),
    path('admin/', admin.site.urls),
    path('editor', include('editor.urls')),
    path('editor/', include('editor.urls')),
    path('', include('news.urls')),
    path('news', include('news.urls')),
    path('news/', include('news.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
