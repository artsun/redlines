from django.contrib import admin

from .models import IndexArticleFresh, IndexArticleHot, Author

@admin.register(IndexArticleFresh)
class IndexArticleFreshAdmin(admin.ModelAdmin):
    pass

@admin.register(IndexArticleHot)
class IndexArticleHotAdmin(admin.ModelAdmin):
    pass

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass
