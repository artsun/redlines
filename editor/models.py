from django.db import models
from django.contrib.auth.models import User, Group

from .html_constructors import HTMLSlider


class Image(models.Model):
    image = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.image.name

    def commit(self, obj, force_update=False):
        self.image = obj
        self.save(force_update=force_update)


class Slider(models.Model):
    content = models.CharField(max_length=10240, null=False, blank=False, editable=False)

    def update_with_slide(self, slide):
        sts_list = list(SlideToSlider.objects.filter(sld=self).order_by('num'))
        html = HTMLSlider(self.pk)
        new_sts = SlideToSlider(sld=self, slde=slide, num=sts_list[-1].num + 1)
        new_sts.save()
        [html.aggregate(sts.slde.label, sts.slde.descr, sts.slde.img.image.url) for sts in sts_list + [new_sts]]
        self.content = html.gen()
        self.save(force_update=True)

    def refresh(self):
        sts_list = list(SlideToSlider.objects.filter(sld=self).order_by('num'))
        html = HTMLSlider(self.pk)
        [html.aggregate(sts.slde.label, sts.slde.descr, sts.slde.img.image.url) for sts in sts_list]
        self.content = html.gen()
        self.save(force_update=True)

    def get_absolute_url(self):
        return f'/slider/{self.pk}'


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

    def render_slider_init(self):
        new_pk = Slider.objects.last().pk + 1
        html = HTMLSlider(new_pk)
        html.aggregate(self.label, self.descr, self.img.image.url)
        new_slider = Slider(pk=new_pk, content=html.gen())
        new_slider.save()
        s_to_s = SlideToSlider(sld=new_slider, slde=self, num=0)
        s_to_s.save()
        return new_slider

    def remove_from_slider(self, slider) -> str:
        sts_list = list(SlideToSlider.objects.filter(sld=slider).order_by('num'))
        if len(sts_list) > 1:
            [sts.delete() for sts in sts_list if sts.slde.pk == self.pk]
            slider.refresh()
            return slider.get_absolute_url()
        else:
            slider.delete()
            return '/slider'


class SlideToSlider(models.Model):
    sld = models.ForeignKey(Slider, null=False, blank=False, on_delete=models.CASCADE, related_name='slider_slides')
    slde = models.ForeignKey(Slide, null=False, blank=False, on_delete=models.CASCADE, related_name='sliders')
    num = models.IntegerField(verbose_name='Номер слайда', null=False, editable=True)

    def __str__(self):
        return f'{self.num} {self.sld}'

