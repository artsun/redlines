from django.db import models

from django.contrib.auth.models import User, Group


class Image(models.Model):
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.image.name

    def commit(self, obj, force_update=False):
        self.image = obj
        self.save(force_update=force_update)


class Slider(models.Model):
    header = models.CharField(verbose_name='Название', max_length=32, null=True, blank=True, editable=True)
    content = models.CharField(max_length=512, null=True, blank=False, editable=False)


class SlideToSlider(models.Model):
    sld = models.ForeignKey(Slider, null=False, blank=False, on_delete=models.CASCADE, related_name='slider_slides')
    num = models.IntegerField(verbose_name='Номер слайда', null=False, editable=True)


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


