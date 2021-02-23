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
        return {r.codename: r.arts.count() for r in Rubric.objects.prefetch_related('arts').defer('arts__content').all()}

    @staticmethod
    def navbar_catalogs():
        return {
            'catBiology': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='biology').defer('content').order_by('updated')[:4],
            'catGenetics': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='genetics').defer('content').order_by('updated')[:4],
            'catGeography': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='geography').defer('content').order_by('updated')[:4],
            'catMath': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='math').defer('content').order_by('updated')[:4],
            'catMedicine': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='medicine').defer('content').order_by('updated')[:4],
            'catPhysics': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='physics').defer('content').order_by('updated')[:4],
            'catChemistry': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='chemistry').defer('content').order_by('updated')[:4],
            'catEcology': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='ecology').defer('content').order_by('updated')[:4],
            'catHistory': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='history').defer('content').order_by('updated')[:4],
            'catPsycho': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='psycho').defer('content').order_by('updated')[:4],
            'catSociology': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='sociology').defer('content').order_by('updated')[:4],
            'catEconomics': Article.objects.select_related('icon', 'author', 'rubric').filter(rubric__codename='economics').defer('content').order_by('updated')[:4]
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

    imgtypes = ('fresh_lg', 'fresh_med', 'fresh_sm', 'hot_hz', 'hot_vert', 'new_left', 'new_right')

    def __str__(self):
        return self.label

    def set_image(self, fl, image_type, save=False):
        if hasattr(self, image_type):
            setattr(self, image_type, fl)
            if save:
                self.save(update_fields=[image_type], force_update=True)

    def set_all_images(self, fl):
        [self.set_image(fl, image_type) for image_type in (self.imgtypes)]
        self.save(update_fields=self.imgtypes, force_update=True)


class Article(models.Model):
    title = models.CharField(verbose_name='Название', max_length=128, null=False, editable=True)
    trans_title = models.CharField(verbose_name='Транслитерированное название', max_length=128, null=False, editable=True)
    icon = models.ForeignKey(Icon, null=True, on_delete=models.SET_NULL)
    author = models.ForeignKey('management.Author', null=True, on_delete=models.SET_NULL, related_name='articles')
    rubric = models.ForeignKey(Rubric, null=True, blank=False, on_delete=models.CASCADE, related_name='arts')
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

    @staticmethod
    def by_datetime(req_date: str) -> dict:
        dt = [x for x in req_date.split('-') if x.isdigit()]
        if len(dt) == 3:
            dt = datetime(year=int(dt[0]), month=int(dt[1]), day=int(dt[2]), tzinfo=timezone.get_default_timezone())  #.replace(tzinfo=None)
        else:
            dt = timezone.now()
        return {'articles': Article.objects.select_related('icon', 'author', 'rubric').filter(updated__day=dt.day, updated__year=dt.year, updated__month=dt.month).order_by('updated'),
                'req_date': Article.date_printer(dt)}

    @staticmethod
    def date_printer(dt: datetime) -> str:
        cal = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
               9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
        return f'{dt.day} {cal[dt.month]} {dt.year}'  # dt.strftime(f'%d {cal[dt.month]} %Y ')  # %H:%M

    def print_time_updated(self):
        one_hour = 3600  # sec
        timedelta = (datetime.now() - self.updated.replace(tzinfo=None)).seconds  # (timezone.now() - self.updated).seconds
        if timedelta < one_hour:
            return 'Менее часа назад'
        elif one_hour < timedelta < one_hour*2:
            return 'Час назад'
        elif one_hour*2 < timedelta < one_hour*3:
            return 'Два часа назад'
        else:
            dt = self.updated
            #dt = self.updated.astimezone(timezone.get_default_timezone())
            return Article.date_printer(dt)

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
        self.rubric = Rubric.objects.get(pk=rubric)
        self.save()
        return True

    def update_title(self, title):
        if title == self.title:
            return
        trans_title = '-'.join(transliterate(title).split())
        if Article.objects.filter(trans_title=trans_title).exists():
            return
        self.title = title
        self.trans_title = trans_title
        self.save(update_fields=['title', 'trans_title'], force_update=True)

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

            # sliders to content of article
            slider_for_this_block = Slider.objects.filter(article=self, inserted=True, edit_block_num=num)
            if slider_for_this_block:
                self.content += json.loads(slider_for_this_block[0].content)
        self.save(update_fields=['content'], force_update=True)

    def update_sliders_links(self, sliders):  # current sliders state
        for s in Slider.objects.filter(article=self):  # drop current
            s.inserted = False
            s.edit_block_num = None
            s.save(update_fields=['inserted', 'edit_block_num'], force_update=True)
        for s in sliders:  # create actual
            pk, num = s[0], s[1]
            slider_instance = Slider.objects.get(pk=pk)
            slider_instance.inserted = True
            slider_instance.edit_block_num = num
            slider_instance.save(update_fields=['inserted', 'edit_block_num'], force_update=True)

    def set_icon(self, icon):
        icon = Icon.objects.get(pk=icon) if Icon.objects.filter(pk=icon).exists() else None
        self.icon = icon
        self.save(force_update=True)

    def get_edit_url(self):
        return f'/editor/{self.trans_title}'

    def get_news_url(self):
        return f'/news/{self.trans_title}'

    def by_rubric_url(self):
        return f'/news/sortby?rubric={self.rubric.codename}'

    def by_updated_url(self):
        return f'/news/sortby?date={str(self.updated.date())}'

    def by_author_url(self):
        return f'/news/sortby?author={self.author.pk}' if self.author else f'/news/sortby?author'


class Slider(models.Model):
    content = models.TextField(null=False, default='{"Пустой": "слайдер"}', editable=True, blank=True)
    edit_block_num = models.IntegerField(verbose_name='Блок привязки слайдера', null=True, editable=True, blank=True)
    inserted = models.BooleanField(default=False, null=False)
    article = models.ForeignKey(Article, null=True, blank=False, on_delete=models.CASCADE, related_name='sliders')

    def __str__(self):
        return f'{self.pk} {self.article.trans_title} {self.inserted}'

    def compouse_struct(self):
        slides = Slide.objects.filter(slider=self).order_by('num')
        return [[s.pk, s.label, s.descr, s.img.url] for s in slides]

    def from_struct_and_content(self, struct, content):
        for slide in Slide.objects.filter(slider=self):
            slide.num = None
            slide.save(update_fields=['num'], force_update=True)
        self.content = rsub('newsSlider', f'slider{self.pk}', content)
        self.save(update_fields=['content'], force_update=True)

        for num, slide in enumerate(struct, start=0):
            slide = Slide.objects.filter(pk=slide[0])
            if not slide:
                continue
            slide = slide[0]
            slide.num = num
            slide.save(update_fields=['num'], force_update=True)

    def get_edit_url(self):
        return f'/editor/slider?article={self.article.trans_title}&spk={self.pk}'


class EditBlock(models.Model):
    art = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE, related_name='edit_blocks')
    data = models.TextField()
    html_data = models.TextField(null=True)
    edit_block_num = models.IntegerField(verbose_name='Порядок', null=False, editable=True)

    def __str__(self):
        return f'Блок {self.edit_block_num} <- {self.art.title}'


class Slide(models.Model):
    img = ResizedImageField(size=[1024, 768], crop=['middle', 'center'],  quality=100, upload_to='images/', blank=True, null=True)
    label = models.CharField(verbose_name='Заголовок', max_length=32, null=True, blank=True, editable=True)
    descr = models.CharField(verbose_name='Подпись', max_length=64, null=True, blank=True, editable=True)
    num = models.IntegerField(verbose_name='Номер слайда', null=True, editable=True)
    slider = models.ForeignKey(Slider, null=True, blank=True, on_delete=models.CASCADE, related_name='slides')

    def __str__(self):
        return f'{self.label} {self.img.name}' if self.label else f'(nolabel){self.pk} {self.img.name}'

    @staticmethod
    def update_if_exists(pk, field_name, value):
        slide = Slide.objects.filter(pk=pk)
        if not slide:
            return
        slide = slide[0]
        if field_name == 'card-title':
            slide.label = value
            slide.save(update_fields=['label'], force_update=True)
        elif field_name == 'card-text':
            slide.descr = value
            slide.save(update_fields=['descr'], force_update=True)
        elif field_name == 'photo':
            slide.img = value
            slide.save(update_fields=['img'], force_update=True)
