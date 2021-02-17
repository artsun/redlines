from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

from django_resized import ResizedImageField

import json
from re import sub as rsub
from collections import OrderedDict
from datetime import datetime

import management
from .translators import transliterate


ARTICLE_STATUS_CHOICES = (
    ('created', 'Новая'),
    ('fixes', 'Правки'),
    ('approved', 'К публикации'),
    ('examine', 'На рассмотрении'),
)
ARTICLE_STATUS_CHOICES_KEYS = ('created', 'fixes', 'approved', 'examine')


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

    @staticmethod
    def statistics():
        return {r.codename: r.arts.count() for r in Rubric.objects.all()}

    @staticmethod
    def navbar_catalogs():
        return {
            'catBiology': Article.objects.filter(rub__rubric__codename='biology').order_by('updated')[:4],
            'catGenetics': Article.objects.filter(rub__rubric__codename='genetics').order_by('updated')[:4],
            'catGeography': Article.objects.filter(rub__rubric__codename='geography').order_by('updated')[:4],
            'catMath': Article.objects.filter(rub__rubric__codename='math').order_by('updated')[:4],
            'catMedicine': Article.objects.filter(rub__rubric__codename='medicine').order_by('updated')[:4],
            'catPhysics': Article.objects.filter(rub__rubric__codename='physics').order_by('updated')[:4],
            'catChemistry': Article.objects.filter(rub__rubric__codename='chemistry').order_by('updated')[:4],
            'catEcology': Article.objects.filter(rub__rubric__codename='ecology').order_by('updated')[:4],
            'catHistory': Article.objects.filter(rub__rubric__codename='history').order_by('updated')[:4],
            'catPsycho': Article.objects.filter(rub__rubric__codename='psycho').order_by('updated')[:4],
            'catSociology': Article.objects.filter(rub__rubric__codename='sociology').order_by('updated')[:4],
            'catEconomics': Article.objects.filter(rub__rubric__codename='economics').order_by('updated')[:4]
        }


class Icon(models.Model):
    fresh_lg = ResizedImageField(size=[534, 468], crop=['middle', 'center'],  quality=100, upload_to='images/', blank=True, null=True)
    fresh_med = ResizedImageField(size=[533, 261], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    fresh_sm = ResizedImageField(size=[800, 598], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    hot_hz = ResizedImageField(size=[1024, 550], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    hot_vert = ResizedImageField(size=[690, 1024], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    new_left = ResizedImageField(size=[800, 800], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    new_right = ResizedImageField(size=[800, 460], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)
    label = models.CharField(verbose_name='Заголовок', max_length=128, null=True, blank=True, editable=True, default="")
    short = models.CharField(verbose_name='Подпись', max_length=512, null=True, blank=True, editable=True, default="")
    rubric = models.ForeignKey(Rubric, null=True, blank=False, on_delete=models.CASCADE, related_name='icons')

    def __str__(self):
        return self.label

    def set_image(self, fl, image_type):
        if getattr(self, image_type):
            setattr(self, image_type, fl)

    def set_all_images(self, fl):
        [self.set_image(fl, image_type) for image_type in ('fresh_lg', 'fresh_med', 'fresh_sm', 'hot_hz', 'hot_vert', 'new_left', 'new_right')]
        self.save(force_update=True)

    def upd(self, itCl, val):
        if itCl not in ('card-title', 'card-text'):
            return
        self.label = val if itCl == 'card-title' else self.label
        self.short = val if itCl == 'card-text' else self.short
        self.save(force_update=True)


class Article(models.Model):
    title = models.CharField(verbose_name='Название', max_length=128, null=False, editable=True)
    trans_title = models.CharField(verbose_name='Транслитерированное название', max_length=128, null=False, editable=True)
    icon = models.ForeignKey(Icon, null=True, on_delete=models.SET_NULL)
    author = models.ForeignKey('management.Author', null=True, on_delete=models.SET_NULL)
    content = models.TextField()
    status = models.CharField(max_length=128, default='created', choices=ARTICLE_STATUS_CHOICES)
    active = models.BooleanField(default=False)
    status_updated = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.trans_title} ({self.title})'

    def isicon(self, imgtype):
        if self.icon:
            if getattr(self.icon, imgtype):
                return getattr(self.icon, imgtype).url
        return None

    def fresh_lg(self):
        return self.isicon('fresh_lg')

    def fresh_med(self):
        return self.isicon('fresh_med')

    def fresh_sm(self):
        return self.isicon('fresh_sm')

    def hot_hz(self):
        return self.isicon('hot_hz')

    def hot_vert(self):
        return self.isicon('hot_vert')

    def new_left(self):
        return self.isicon('new_left')

    def new_right(self):
        return self.isicon('new_right')

    def print_time_updated(self):
        one_hour = 3600  # sec
        timedelta = (datetime.now() - self.updated.replace(tzinfo=None)).seconds
        if timedelta < one_hour:
            return 'Менее часа назад'
        elif one_hour < timedelta < one_hour*2:
            return 'Час назад'
        elif one_hour*2 < timedelta < one_hour*3:
            return 'Два часа назад'
        else:
            dt = self.updated.astimezone(timezone.get_default_timezone())
            cal = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
            return f'{dt.day} {cal[dt.month]} {dt.year}'#dt.strftime(f'%d {cal[dt.month]} %Y ')  # %H:%M

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

    def part_update(self, parts, sliders, htmls, title):
        parts, sliders, htmls = [json.loads(x) for x in (parts, sliders, htmls)]
        if title is not None:
            title = json.loads(title)
            self.update_title(title) if 5 < len(title) < 120 else None

        self.update_sliders_links(sliders)
        EditBlock.objects.filter(art=self).delete()

        for num, (html, block) in enumerate(zip(htmls, parts)):
            eb = EditBlock()
            eb.art, eb.edit_block_num, eb.data, eb.html_data = self, num, rsub(r'\\"', "'", json.dumps(block)), html
            eb.save()
        self.save()


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
        return f'/news/{self.trans_title}'


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

