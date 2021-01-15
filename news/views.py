from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password
from django.utils.safestring import SafeString
from django.contrib.auth.models import User, Group

import json
from collections import OrderedDict

from editor.models import Image, Slide, Slider, Rubric, Article, SliderToArticle, ArticleToRubric


class IndexPage(View):

    def get(self, request, trans_title=None):
        artlist, temp = [], []
        for x in Article.objects.all().order_by('updated'):
            temp.append(x)
            if len(temp) == 5:
                artlist.append(temp)
                temp = []
                
        #print(artlist)
        context = {'artlist': artlist}
        return render(request, 'indexpage.html', context)


class NewsPage(View):

    def get(self, request, trans_title=None):
        if not Article.objects.filter(trans_title=trans_title):
            return redirect('/')
        article = Article.objects.get(trans_title=trans_title)

        context = {'article': article}
        return render(request, 'newspage.html', context)
