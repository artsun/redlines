from django.shortcuts import render
from django.contrib import messages

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

from .models import Image, Slide, Slider, Rubric, Article, ArticleToImage, SliderToArticle, ArticleToRubric


class ArtListPage(View):
    #login_url = '/login/'

    def get(self, request):
        print(request.GET)
        artlist = []
        for a in Article.objects.all().order_by('pk'):
            if ArticleToImage.objects.filter(art=a).exists():
                artlist.append((a, ArticleToImage.objects.get(art=a).img.image.url))
            else:
                artlist.append((a, '/images/question.jpg'))

        context = {'artlist': artlist,}
        return render(request, 'artlistpage.html', context)


#class Editor(LoginRequiredMixin, View):
class RubricPage(View):
    #login_url = '/login/'

    def get(self, request):
        msg = ''
        if 'title' in request.GET.keys() or 'rubric' in request.GET.keys():
            title, rubric = request.GET.get('title'), request.GET.get('rubric')
            title = title.strip()
            if None in (title, rubric) or not title:
                msg = 'Введены некорректные данные'
            else:
                new_art = Article()
                if new_art.create(rubric, title):
                    print(f'REDIRECT {new_art.get_edit_url()}')
                    return redirect(new_art.get_edit_url())
                msg = 'Статья с таким именем существует!'  # дощли сюда если не было redirect раньше
        rubrics = Rubric.objects.all().order_by('pk')
        context = {'rubrics': rubrics,
                   'msg': msg}
        return render(request, 'rubricpage.html', context)


#class Editor(LoginRequiredMixin, View):
class Editor(View):
    #login_url = '/login/'

    def get(self, request, trans_title=None):
        print(trans_title)
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')

        article = Article.objects.get(trans_title=trans_title)
        rubric = ArticleToRubric.objects.get(art=article).rubric
        icon = ArticleToImage.objects.get(art=article) if ArticleToImage.objects.filter(art=article).exists() else None

        sliders = [s.slider for s in SliderToArticle.objects.filter(art=article)]

        context = {'sliders': json.dumps([[x.pk, x.compouse_struct()] for x in sliders]),
                   'article': article,
                   'rubric': rubric,
                   'icon': icon}

        return render(request, 'editpage.html', context)

    def post(self, request, trans_title=None):
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')

        article = Article.objects.get(trans_title=trans_title)

        if request.POST.get('artUpd'):
            artUpd = json.loads(request.POST.get('artUpd'))
            if len(artUpd) != 2:
                return JsonResponse({'url': f'/editor/{article.trans_title}'})
            short, title = artUpd
            if len(short) < 126 and len(title) < 120:
                article.update_title(title)
                article.update_short(short)
            return JsonResponse({'url': f'/editor/{article.trans_title}'})
        elif request.FILES.get('icon'):
            if ArticleToImage.objects.filter(art=article).exists():
                ai = ArticleToImage.objects.get(art=article)
                ai.update_with_image(article, request.FILES.get('icon'))
                ai.save(force_update=True)
            else:
                ai = ArticleToImage()
                ai.update_with_image(article, request.FILES.get('icon'))
                ai.save()

        return JsonResponse({'url': f'/editor/{article.trans_title}'})


class SliderMake(View):
    #login_url = '/login/'

    def get(self, request, trans_title=None, spk=None):
        print('GET PK', spk)
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')
        article = Article.objects.get(trans_title=trans_title)
        article_edit_url = article.get_edit_url()
        if spk is None:
            context = {'slides': Slide.objects.all().order_by('pk'),
                       'article_edit_url': article.get_edit_url()
                       }
        else:
            if not Slider.objects.filter(pk=spk).exists():
                return redirect(f'slider')

            slider_instance = Slider.objects.get(pk=spk)
            context = {'slides': Slide.objects.all().order_by('pk'),
                       'slider_struct': json.dumps(slider_instance.compouse_struct()),
                       'article_edit_url': article.get_edit_url(),
                       }

        return render(request, 'sliderpage.html', context)

    def post(self, request, trans_title=None, spk=None):
        print('POST, PK', spk)
        post_heads = request.POST.keys()
        slider_exists = Slider.objects.filter(pk=spk).exists()
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')
        article = Article.objects.get(trans_title=trans_title)

        if request.POST.get('delSlide'):
            slide = Slide.objects.get(pk=request.POST.get('delSlide'))
            [slide.remove_from_slider(sl) for sl in set(Slider.objects.filter(slider_slides__slde=slide).all())]
            slide.delete()
            return redirect(f'/editor/{trans_title}/slider/{spk}') if Slider.objects.filter(pk=spk).exists() else redirect('slider')

        elif request.POST.get("updSlider"):
            struct = json.loads(request.POST.get("updSlider"), object_pairs_hook=OrderedDict)
            if slider_exists:
                slider = Slider.objects.get(pk=spk)
                if len(struct) < 1:
                    slider.delete()
                    return JsonResponse({'url': f'/editor/{trans_title}/slider'})
            else:
                if len(struct) < 1:
                    return JsonResponse({'url': f'/editor/{trans_title}/slider'})
                slider = Slider()
                slider.save()
                sta = SliderToArticle(slider=slider, art=article)
                sta.save()
            slider.from_struct(struct)
            return JsonResponse({'url': f'/editor/{trans_title}/slider/{slider.pk}'})

        elif request.FILES.get('photo') and request.POST.get('name'):
            Slide.objects.get(pk=request.POST.get('name')).img.commit(request.FILES.get('photo'), force_update=True)

        elif request.POST.get('name') and request.POST.get('class') and 'val' in post_heads:
            Slide.objects.get(pk=request.POST.get('name')).upd(request.POST.get('class'), request.POST.get('val'))

        elif request.FILES.get('file'):
            img = Image()
            img.commit(request.FILES.get('file'))
            Slide(img=img, label=request.POST.get('label'), descr=request.POST.get('descr')).save()

        return redirect(f'/editor/{trans_title}/slider') if spk is None else redirect(f'/editor/{trans_title}/slider/{spk}')


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
