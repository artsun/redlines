from django.contrib import admin

from .models import NewsComment

@admin.register(NewsComment)
class NewsCommentAdmin(admin.ModelAdmin):
    pass
