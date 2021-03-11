from django.contrib import admin

# Register your models here.
from .models import Image, Slide, Slider, Rubric, Article, EditBlock, Icon

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    pass

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    pass

@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    pass

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    pass

@admin.register(EditBlock)
class EditBlockAdmin(admin.ModelAdmin):
    pass

@admin.register(Icon)
class IconAdmin(admin.ModelAdmin):
    pass
