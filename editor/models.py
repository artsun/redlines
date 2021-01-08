from django.db import models
from django.contrib.auth.models import User, Group

import json

from .translators import transliterate


ARTICLE_STATUS_CHOICES = (
    ('created', 'Новая'),
    ('fixes', 'Правки'),
    ('approved', 'К публикации'),
    ('examine', 'На рассмотрении'),
)



class Image(models.Model):
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.image.name

    def commit(self, obj, force_update=False):
        self.image = obj
        self.save(force_update=force_update)


class Rubric(models.Model):
    title = models.CharField(verbose_name='Название рубрики', max_length=64, null=False, editable=True)
    codename = models.CharField(verbose_name='Код рубрики', max_length=64, null=False, editable=True)
    logo = models.ForeignKey(Image, null=True, on_delete=models.CASCADE, related_name='rubrics_logo')
    background = models.ForeignKey(Image, null=True, on_delete=models.CASCADE, related_name='rubrics_backs')

    def __str__(self):
        return self.title


class Article(models.Model):
    title = models.CharField(verbose_name='Название', max_length=128, null=False, editable=True)
    trans_title = models.CharField(verbose_name='Транслитерированное название', max_length=128, null=False, editable=True)
    short = models.CharField(verbose_name='Подводка', max_length=512, null=True, editable=True)
    content = models.TextField()
    status = models.CharField(max_length=128, default='created', choices=ARTICLE_STATUS_CHOICES)
    active = models.BooleanField(default=False)
    status_updated = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.trans_title

    def create(self, rubric, title):
        trans_title = '-'.join(transliterate(title).split())
        if Article.objects.filter(trans_title=trans_title).exists():
            return False
        self.trans_title = trans_title
        self.title = title
        self.status = 'created'
        self.save()
        if not Rubric.objects.filter(pk=rubric).exists():
            self.delete()
            return False
        link_to_rubric = ArticleToRubric(rubric=Rubric.objects.get(pk=rubric), art=self)
        link_to_rubric.save()
        return True

    def update_title(self, title):
        if title == self.title:
            return
        trans_title = '-'.join(transliterate(title).split())
        if Article.objects.filter(trans_title=trans_title).exists():
            return
        self.title = title
        self.trans_title = trans_title
        self.save(force_update=True)

    def update_short(self, short):
        self.short = short
        self.save(force_update=True)

    def get_edit_url(self):
        return f'/editor/{self.trans_title}'


class ArticleToImage(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE)
    img = models.ForeignKey(Image, null=False, blank=False, on_delete=models.CASCADE)

    def update_with_image(self, article, icon_file):
        img = Image()
        img.commit(icon_file)
        self.img = img
        self.art = article


class ArticleToRubric(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='rub')
    rubric = models.ForeignKey(Rubric, null=False, blank=False, on_delete=models.CASCADE, related_name='arts')


class Slider(models.Model):

    def compouse_struct(self):
        sts_list = list(SlideToSlider.objects.filter(sld=self).order_by('num'))
        return [[x.slde.pk, x.slde.label, x.slde.descr, x.slde.img.image.url] for x in sts_list]

    def from_struct(self, struct):
        [x.delete() for x in list(SlideToSlider.objects.filter(sld=self))]
        for num, slide in enumerate(struct, start=0):
            if not Slide.objects.filter(pk=slide[0]).exists():
                continue
            sts = SlideToSlider(sld=self, slde=Slide.objects.get(pk=slide[0]), num=num)
            sts.save()


class EditBlock(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='edit_blocks')
    data = models.TextField()


class SliderToArticle(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='sliders')
    slider = models.ForeignKey(Slider, null=False, blank=False, on_delete=models.CASCADE, related_name='arts')
    edit_block_num = models.IntegerField(verbose_name='Блок привязки слайдера', null=True, editable=True)


class Slide(models.Model):
    img = models.ForeignKey(Image, null=False, blank=False, on_delete=models.CASCADE, related_name='slides')
    label = models.CharField(verbose_name='Заголовок', max_length=32, null=True, blank=True, editable=True)
    descr = models.CharField(verbose_name='Подпись', max_length=64, null=True, blank=True, editable=True)

    def __str__(self):
        return f'{self.label} {self.img.image.name}' if self.label else f'slide{self.pk} {self.img.image.name}'

    def upd(self, itCl, val):
        if itCl not in ('card-title', 'card-text'):
            return
        self.label = val if itCl == 'card-title' else self.label
        self.descr = val if itCl == 'card-text' else self.descr
        self.save(force_update=True)


    def remove_from_slider(self, slider):
        slider_sts_list = list(SlideToSlider.objects.filter(sld=slider))
        [sts.delete() for sts in slider_sts_list if sts.slde.pk == self.pk]
        slider.delete() if len(list(SlideToSlider.objects.filter(sld=slider))) == 0 else None # del SLIDER if last


class SlideToSlider(models.Model):
    sld = models.ForeignKey(Slider, null=False, blank=False, on_delete=models.CASCADE, related_name='slider_slides')
    slde = models.ForeignKey(Slide, null=False, blank=False, on_delete=models.CASCADE, related_name='sliders')
    num = models.IntegerField(verbose_name='Номер слайда', null=False, editable=True)

    def __str__(self):
        return f'{self.num} {self.sld}'

