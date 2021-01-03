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

from .models import Image, Slide



#class Editor(LoginRequiredMixin, View):
class Editor(View):
    #login_url = '/login/'

    def get(self, request):
        instance = Image.objects.get(image='images/c0495392_web_NHqSbRu.jpg')
        #print(instance.image.url)
        context = {'instance': instance}

        return render(request, 'editform.html', context)


class SliderMake(View):
    #login_url = '/login/'

    def get(self, request, pk=None):
        print('PK', pk)
        context = {'slides': Slide.objects.all()}

        return render(request, 'sliderpage.html', context)

    def post(self, request):
        post_heads = request.POST.keys()
        if request.POST.get('delBtn'):
            Slide.objects.filter(pk=request.POST.get('delBtn')).delete()
        elif request.FILES.get('photo') and request.POST.get('name'):
            Slide.objects.get(pk=request.POST.get('name')).img.commit(request.FILES.get('photo'), force_update=True)
        elif request.POST.get('name') and request.POST.get('class') and 'val' in post_heads:
            Slide.objects.get(pk=request.POST.get('name')).upd(request.POST.get('class'), request.POST.get('val'))
        elif request.FILES.get('file'):
            img = Image()
            img.commit(request.FILES.get('file'))
            Slide(img=img, label=request.POST.get('label'), descr=request.POST.get('descr')).save()

        return redirect(f'/slider')


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
