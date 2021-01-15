from django.db import models
from django.contrib.auth.models import User, Group

import json
from re import sub as rsub
from collections import OrderedDict

from django_resized import ResizedImageField

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


class Icon(models.Model):
    img = ResizedImageField(size=[1024, 768], crop=['middle', 'center'],  quality=100, upload_to='images/', blank=True, null=False)
    label = models.CharField(verbose_name='Заголовок', max_length=128, null=True, blank=True, editable=True, default="")
    descr = models.CharField(verbose_name='Подпись', max_length=512, null=True, blank=True, editable=True, default="")
    rubric = models.ForeignKey(Rubric, null=True, blank=False, on_delete=models.CASCADE, related_name='icons')

    def __str__(self):
        return self.label

    def upd_image(self, img):
        self.img = img
        self.save(force_update=True)

    def upd(self, itCl, val):
        if itCl not in ('card-title', 'card-text'):
            return
        self.label = val if itCl == 'card-title' else self.label
        self.descr = val if itCl == 'card-text' else self.descr
        self.save(force_update=True)


class Article(models.Model):
    title = models.CharField(verbose_name='Название', max_length=128, null=False, editable=True)
    trans_title = models.CharField(verbose_name='Транслитерированное название', max_length=128, null=False, editable=True)
    short = models.CharField(verbose_name='Подводка', max_length=512, null=True, editable=True)
    icon = models.ForeignKey(Icon, null=True, on_delete=models.SET_NULL)
    content = models.TextField()
    status = models.CharField(max_length=128, default='created', choices=ARTICLE_STATUS_CHOICES)
    active = models.BooleanField(default=False)
    status_updated = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.trans_title} ({self.title})'

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

    def full_update(self, parts, sliders, htmls, artUpdates):
        parts, sliders, htmls = [json.loads(x) for x in (parts, sliders, htmls)]
        if artUpdates is not None:
            title = json.loads(artUpdates)
            self.update_title(title)
        self.update_sliders_links(sliders)
        self.content = ''
        EditBlock.objects.filter(art=self).delete()

        for num, (html, block) in enumerate(zip(htmls, parts)):
            self.content += html
            eb = EditBlock()
            eb.art, eb.edit_block_num, eb.data, eb.html_data = self, num, rsub(r'\\"', "'", json.dumps(block)), html
            eb.save()

            if SliderToArticle.objects.filter(art=self, edit_block_num=num).exists():
                self.content += json.loads(SliderToArticle.objects.get(art=self, edit_block_num=num).slider.content)
        self.save()

    def update_sliders_links(self, sliders):
        SliderToArticle.objects.filter(art=self).delete()

        for sl in sliders:
            pk, num = sl[0], sl[1]
            sl_instance = Slider.objects.get(pk=pk)
            sta = SliderToArticle()
            sta.art, sta.slider, sta.edit_block_num = self, sl_instance, num
            sta.save()

    def set_icon(self, icon):
        icon = Icon.objects.get(pk=icon) if Icon.objects.filter(pk=icon).exists() else None
        self.icon = icon
        self.save(force_update=True)

    def get_edit_url(self):
        return f'/editor/{self.trans_title}'

    def get_news_url(self):
        return f'{self.trans_title}'


class ArticleToRubric(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='rub')
    rubric = models.ForeignKey(Rubric, null=False, blank=False, on_delete=models.CASCADE, related_name='arts')

    def __str__(self):
        return f'{self.rubric.title} ({self.art.title})'


class Slider(models.Model):
    content = models.TextField(null=True)
    rubric = models.ForeignKey(Rubric, null=True, blank=False, on_delete=models.CASCADE, related_name='sliders')

    def __str__(self):
        return f'{self.pk} {self.rubric.title}. Используется: {", ".join([sta.art.title for sta in SliderToArticle.objects.filter(slider=self)])}'

    def compouse_struct(self):
        sts_list = list(SlideToSlider.objects.filter(sld=self).order_by('num'))
        return [[x.slde.pk, x.slde.label, x.slde.descr, x.slde.img.url] for x in sts_list]

    def from_struct_and_content(self, struct, content, rubric):
        self.content = rsub('newsSlider', f'slider{self.pk}', content)
        self.rubric = rubric
        self.save(force_update=True)
        [x.delete() for x in list(SlideToSlider.objects.filter(sld=self))]
        for num, slide in enumerate(struct, start=0):
            if not Slide.objects.filter(pk=slide[0]).exists():
                continue
            sts = SlideToSlider(sld=self, slde=Slide.objects.get(pk=slide[0]), num=num)
            sts.save()


class EditBlock(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='edit_blocks')
    data = models.TextField()
    html_data = models.TextField(null=True)
    edit_block_num = models.IntegerField(verbose_name='Порядок', null=False, editable=True)

    def __str__(self):
        return f'Блок {self.edit_block_num} <- {self.art.title}'


class SliderToArticle(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='sliders')
    slider = models.ForeignKey(Slider, null=False, blank=False, on_delete=models.CASCADE, related_name='arts')
    edit_block_num = models.IntegerField(verbose_name='Блок привязки слайдера', null=True, editable=True)

    def __str__(self):
        return f'{self.art.title} -> {self.slider.pk} {self.slider.rubric}'


class Slide(models.Model):
    img = ResizedImageField(size=[1024, 768], crop=['middle', 'center'],  quality=100, upload_to='images/', blank=True, null=True)
    label = models.CharField(verbose_name='Заголовок', max_length=32, null=True, blank=True, editable=True)
    descr = models.CharField(verbose_name='Подпись', max_length=64, null=True, blank=True, editable=True)
    rubric = models.ForeignKey(Rubric, null=True, blank=False, on_delete=models.CASCADE, related_name='slides')

    def __str__(self):
        return f'{self.label} {self.img.name}' if self.label else f'slide{self.pk} {self.img.name}'

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

