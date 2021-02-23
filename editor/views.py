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

from .models import Image, Slide, Slider, Rubric, Article, EditBlock, Icon, ARTICLE_STATUS_CHOICES, ARTICLE_STATUS_CHOICES_KEYS
from management.models import Author


class ArtListPage(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        artlist = Article.objects.select_related('icon', 'author', 'rubric').defer('content').all().order_by('-updated')
        return render(request, 'artlistpage.html', {'artlist': artlist})


class RubricPage(LoginRequiredMixin, View):
    login_url = '/login'

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
                    return redirect(new_art.get_edit_url())
                msg = 'Статья с таким именем существует!'  # дошли сюда если не было redirect раньше
        rubrics = Rubric.objects.select_related('logo', 'background').all().order_by('pk')
        context = {'rubrics': rubrics,
                   'msg': msg}
        return render(request, 'rubricpage.html', context)


class Editor(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request, trans_title=None):
        article = Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=trans_title)[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        if request.GET.get('preview'):
            return render(request, 'editorNewspage.html', {'article': article})

        sliders_of_article = Slider.objects.filter(article=article).order_by('pk')

        if 'setAuth' in request.GET.keys() and request.GET['setAuth'] != '' and Author.objects.filter(pk=request.GET['setAuth']).exists():
            article.author = Author.objects.get(pk=request.GET['setAuth'])
            article.save(update_fields=['author'], force_update=True)
            return redirect(article.get_edit_url())
        elif 'setRub' in request.GET.keys() and request.GET['setRub'] != '' and Rubric.objects.filter(pk=request.GET['setRub']).exists():
            article.rubric = Rubric.objects.get(pk=request.GET['setRub'])
            article.save(update_fields=['rubric'], force_update=True)
            return redirect(article.get_edit_url())
        elif 'setStatus' in request.GET.keys() and request.GET['setStatus'] in ARTICLE_STATUS_CHOICES_KEYS:
            if request.GET['setStatus'] != 'approved':
                article.active = False
            article.status = request.GET['setStatus']
            article.save(update_fields=['status', 'active'], force_update=True)
            return redirect(article.get_edit_url())
        elif 'setActive' in request.GET.keys() and request.GET['setActive'] in ('1', '0'):
            if article.status == 'approved' and request.GET['setActive'] == '1':
                article.active = True
            else:
                article.active = False
            article.save(update_fields=['active'], force_update=True)
            return redirect(article.get_edit_url())

        context = {'sliders': [(sl.pk, json.loads(sl.content)) for sl in sliders_of_article],  # right panel
                   'sliders_in_content': [[s.edit_block_num, s.pk] for s in Slider.objects.filter(article=article, inserted=True).defer('content').order_by('edit_block_num')],
                   'article': article,
                   'eblocks': EditBlock.objects.select_related('art').filter(art=article).order_by('edit_block_num'),
                   'authors': Author.objects.defer('login', 'short', 'avatar').all(),
                   'rubrics': Rubric.objects.defer('codename', 'logo', 'background').all(),
                   'status_choices': ARTICLE_STATUS_CHOICES}

        return render(request, 'editpage.html', context)

    def post(self, request, trans_title=None):
        article = Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=trans_title)[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        if request.POST.get('parts') and request.POST.get('sliders') and request.POST.get('htmls'):
            parts, sliders, htmls = request.POST.get('parts'), request.POST.get('sliders'), request.POST.get('htmls')
            if request.POST.get('partSave'):
                article.part_update(parts, sliders, htmls, request.POST.get('artTitle'))
                if not request.POST.get('artTitle'):  # url not changing
                    return JsonResponse({'url': request.POST.get('url')})
            else:
                article.full_update(parts, sliders, htmls, request.POST.get('artTitle'))
                return JsonResponse({'url': f'/editor/{article.trans_title}?preview=1'})
        elif request.POST.get('dropArticle'):
            article.delete()
        return JsonResponse({'url': f'/editor/{article.trans_title}'})


class SliderMake(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        trans_title, spk = request.GET.get('article'), request.GET.get('spk')
        article = Article.objects.select_related('icon', 'author', 'rubric').defer('content').filter(trans_title=trans_title)[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        if spk is None:  # create slider and redirect
            slider = Slider(article=article)
            slider.save()
            return redirect(slider.get_edit_url())

        else:  # edit existing slider
            slider = Slider.objects.filter(pk=spk)[:1]
            if not slider.exists():  # inside qs incorrect query
                return redirect(article.get_edit_url())  # go article edit
            slider = slider[0]

            context = {'slides': Slide.objects.filter(slider=slider).order_by('pk'),
                       'slider_struct': json.dumps(slider.compouse_struct()),
                       'article': article,
                       }

        return render(request, 'sliderpage.html', context)

    def post(self, request):
        trans_title, spk = request.GET.get('article'), request.GET.get('spk')

        article = Article.objects.select_related('icon', 'author', 'rubric').defer('content').filter(trans_title=trans_title)[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        slider = Slider.objects.filter(pk=spk)
        if not slider:
            return redirect(article.get_edit_url())
        slider = slider[0]

        if request.POST.get('delSlide'):
            slide = Slide.objects.filter(pk=request.POST.get('delSlide'))[:1]
            if slide:
                slide[0].delete()
            return redirect(slider.get_edit_url())
        elif request.FILES.get('file'):  # new slide
            sl = Slide(img=request.FILES.get('file'), label=request.POST.get('label'), descr=request.POST.get('descr'), slider=slider)
            sl.save()

        elif request.POST.get("updSlider") and request.POST.get("sliderContent"):  # saving slider
            struct = json.loads(request.POST.get("updSlider"), object_pairs_hook=OrderedDict)
            if len(struct) < 1:  # save empty slider -> delete and redirect
                slider.delete()
                return JsonResponse({'url': article.get_edit_url()})
            slider.from_struct_and_content(struct, request.POST.get("sliderContent"))
            return JsonResponse({'url': f'/editor/slider?article={trans_title}&spk={slider.pk}'})

        elif request.FILES.get('photo') and request.POST.get('name'):
            Slide.update_if_exists(request.POST.get('name'), 'photo', request.FILES.get('photo'))

        elif request.POST.get('name') and request.POST.get('class') and 'val' in request.POST.keys():
            Slide.update_if_exists(request.POST.get('name'), request.POST.get('class'), request.POST.get('val'))

        return redirect(slider.get_edit_url())


class IconMake(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        article = Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=request.GET.get('article'))[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        context = {'article': article}
        return render(request, 'iconpage.html', context)

    def post(self, request):
        article = Article.objects.filter(trans_title=request.GET.get('article'))[:1]
        if not article:
            return redirect('/editor')
        article = article[0]

        if request.FILES.get('image') and request.POST.get('image_type'):
            article.icon.set_image(request.FILES.get('image'), request.POST.get('image_type'), save=True)
        elif request.FILES.get('file'):
            article.icon.set_all_images(request.FILES.get('file'))
        elif 'short' in request.POST.keys():
            article.icon_short = request.POST['short']
            article.icon.save(update_fields=['short'], force_update=True)
        return redirect(f'/editor/icon?article={article.trans_title}')


class Uploader(LoginRequiredMixin, View):
    login_url = '/login'

    def post(self, request):
        print('POST UPLOADER', request.FILES['image'].name)
        img = Image()
        img.commit(request.FILES.get('image'))
        return JsonResponse(
            {"success": 1,
             "file": {
                 "url": img.image.url}
             })
