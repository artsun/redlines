from django.contrib import admin

# Register your models here.
from .models import Image, Slide, SlideToSlider, Slider, Rubric, Article, ArticleToRubric, EditBlock, SliderToArticle, Icon

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    pass

@admin.register(SlideToSlider)
class SlideToSliderAdmin(admin.ModelAdmin):
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

@admin.register(ArticleToRubric)
class ArticleToRubricAdmin(admin.ModelAdmin):
    pass

@admin.register(EditBlock)
class EditBlockAdmin(admin.ModelAdmin):
    pass

@admin.register(SliderToArticle)
class SliderToArticleAdmin(admin.ModelAdmin):
    pass

@admin.register(Icon)
class IconAdmin(admin.ModelAdmin):
    pass
