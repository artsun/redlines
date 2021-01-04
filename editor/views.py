from django.shortcuts import render
from django.contrib import messages

from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User, Group

import json

from .models import Image, Slide, Slider, SlideToSlider



#class Editor(LoginRequiredMixin, View):
class Editor(View):
    #login_url = '/login/'

    def get(self, request):
        #instance = Image.objects.get(image='images/c0495392_web_NHqSbRu.jpg')
        sliders = Slider.objects.all()
        #print(instance.image.url)
        context = {'sliders': sliders}

        return render(request, 'editform.html', context)


class SliderMake(View):
    #login_url = '/login/'

    def get(self, request, spk=None):
        print('GET PK', spk)
        if spk is None:
            context = {'slides': [(sl, 0) for sl in Slide.objects.all()],
                       'slider_instance': ""}
        else:
            if not Slider.objects.filter(pk=spk).exists():
                return redirect(f'/slider')

            slider_instance = Slider.objects.get(pk=spk)
            used_slides = set([s.slde for s in SlideToSlider.objects.filter(sld=slider_instance)])
            context = {'slides': [(sl, 1) if sl in used_slides else (sl, 0) for sl in Slide.objects.all()],
                       'slider_instance': slider_instance}


        return render(request, 'sliderpage.html', context)

    def post(self, request, spk=None):
        print('POST, PK', spk)
        post_heads = request.POST.keys()
        slider_exists = Slider.objects.filter(pk=spk).exists()

        if request.POST.get('delBtn'):
            slide = Slide.objects.get(pk=request.POST.get('delBtn'))
            #sliders = SlideToSlider.objects.filter(slde=slide)
            [slide.remove_from_slider(sl) for sl in set(Slider.objects.filter(slider_slides__slde=slide).all())]
            slide.delete()
            return redirect(f'/slider/{spk}') if Slider.objects.filter(pk=spk).exists() else redirect('/slider')

        elif request.POST.get('remBtn') and slider_exists:
            slide = Slide.objects.get(pk=request.POST.get('remBtn'))
            return redirect(slide.remove_from_slider(Slider.objects.get(pk=spk)))

        elif request.POST.get('insBtn'):
            if slider_exists:
                slider = Slider.objects.get(pk=spk)
                slider.update_with_slide(Slide.objects.get(pk=request.POST.get('insBtn')))
                return redirect(f'/slider/{slider.pk}')
            else:
                slide = Slide.objects.get(pk=request.POST.get('insBtn'))
                new_slider = slide.render_slider_init()
                return redirect(f'/slider/{new_slider.pk}')

        elif request.FILES.get('photo') and request.POST.get('name'):
            Slide.objects.get(pk=request.POST.get('name')).img.commit(request.FILES.get('photo'), force_update=True)
            if slider_exists:
                Slider.objects.get(pk=spk).refresh()
        elif request.POST.get('name') and request.POST.get('class') and 'val' in post_heads:
            Slide.objects.get(pk=request.POST.get('name')).upd(request.POST.get('class'), request.POST.get('val'))
            if slider_exists:
                Slider.objects.get(pk=spk).refresh()
        elif request.FILES.get('file'):
            img = Image()
            img.commit(request.FILES.get('file'))
            Slide(img=img, label=request.POST.get('label'), descr=request.POST.get('descr')).save()

        return redirect(f'/slider') if spk is None else redirect(f'/slider/{spk}')


class Uploader(View):

    def post(self, request):
        print('POST UPLOADER', request.FILES['image'].name)
        img = Image()
        img.commit(request.FILES.get('image'))
        return JsonResponse(
            {"success": 1,
             "file": {
                 "url": img.image.url}
             })
