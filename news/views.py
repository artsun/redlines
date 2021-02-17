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
from management.models import IndexArticleFresh, IndexArticleHot


class IndexPage(View):

    def get(self, request, trans_title=None):

        flist, hlist, pklist, nlist = [], [], [], []
        for x in IndexArticleFresh.objects.all().order_by('position'):
            flist.append(x)
            pklist.append(x.article.pk)
        for x in IndexArticleHot.objects.all().order_by('position'):
            hlist.append(x)
            pklist.append(x.article.pk)
        temp = []
        for x in Article.objects.all().exclude(pk__in=pklist).order_by('updated')[:10]:
            temp.append(x)
            if len(temp) == 2:
                nlist.append(temp)
                temp = []
        context = {
            'flist': flist,
            'hlist': hlist,
            'nlist': nlist,
            'statistics': Rubric.statistics(),
        }
        context.update(Rubric.navbar_catalogs())
        return render(request, 'indexpage.html', context)


class NewsPage(View):

    def get(self, request, trans_title=None):
        if not Article.objects.filter(trans_title=trans_title):
            return redirect('/')
        article = Article.objects.get(trans_title=trans_title)
        rubric = article.rub.first().rubric
        prev = Article.objects.filter(rub__rubric=rubric, updated__lt=article.updated).first()
        next = Article.objects.filter(rub__rubric=rubric, updated__gt=article.updated).first()
        you_may_also_like = [a.article for a in IndexArticleHot.objects.exclude(article=article) if a.article != prev and a.article != next]
        also_like_one = you_may_also_like[0] if len(you_may_also_like) > 0 else []
        also_like_two = you_may_also_like[1] if len(you_may_also_like) > 1 else []
        print(article.comments.count())

        context = {
            'article': article,
            'similar': Article.objects.filter(rub__rubric=rubric).exclude(pk=article.pk).order_by('updated')[:5],
            'news': Article.objects.order_by('updated').exclude(rub__rubric=rubric)[:5],
            'statistics': Rubric.statistics(),
            'prev': prev,
            'next': next,
            'also_like_one': also_like_one,
            'also_like_two': also_like_two
        }
        context.update(Rubric.navbar_catalogs())
        return render(request, 'newspage.html', context)


class NewsSorter(View):

    def get(self, request):
        if not request.GET.get('rubric') or not Rubric.objects.filter(codename=request.GET.get('rubric')).exists():
            return redirect('/')
        rubric = Rubric.objects.get(codename=request.GET.get('rubric'))
        rubric_news = [a.art for a in ArticleToRubric.objects.filter(rubric=rubric).order_by('art__updated')]

        print(rubric)
        context = {
            'rubric': rubric,
            'rubric_news': rubric_news,
            'statistics': Rubric.statistics(),
            'news': Article.objects.order_by('updated').exclude(rub__rubric=rubric)[:5],
        }
        context.update(Rubric.navbar_catalogs())
        return render(request, 'byRubric.html', context)
