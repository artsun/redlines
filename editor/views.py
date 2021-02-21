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

from .models import Image, Slide, Slider, Rubric, Article, SliderToArticle, EditBlock, Icon,\
    ARTICLE_STATUS_CHOICES, ARTICLE_STATUS_CHOICES_KEYS
from management.models import Author

class ArtListPage(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        context = {'artlist': Article.objects.select_related('icon', 'author', 'rubric').all().order_by('-updated'),}
        return render(request, 'artlistpage.html', context)


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
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')

        article = Article.objects.get(trans_title=trans_title)
        if request.GET.get('preview'):
            context = {'article': article,
                        'linkback': 1}
            return render(request, 'editorNewspage.html', context)

        sliders_in_rubric = Slider.objects.filter(rubric=article.rubric).order_by('pk')

        if 'setAuth' in request.GET.keys() and request.GET['setAuth'] != '' and Author.objects.filter(pk=request.GET['setAuth']).exists():
            article.author = Author.objects.get(pk=request.GET['setAuth'])
            article.save()
            return redirect(article.get_edit_url())
        elif 'setRub' in request.GET.keys() and request.GET['setRub'] != '' and Rubric.objects.filter(pk=request.GET['setRub']).exists():
            article.rubric = Rubric.objects.get(pk=request.GET['setRub'])
            article.save()
            return redirect(article.get_edit_url())
        elif 'setStatus' in request.GET.keys() and request.GET['setStatus'] in ARTICLE_STATUS_CHOICES_KEYS:
            if request.GET['setStatus'] != 'approved':
                article.active = False
            article.status = request.GET['setStatus']
            article.save()
            return redirect(article.get_edit_url())
        elif 'setActive' in request.GET.keys() and request.GET['setActive'] in ('1', '0'):
            if article.status == 'approved' and request.GET['setActive'] == '1':
                article.active = True
            else:
                article.active = False
            article.save()
            return redirect(article.get_edit_url())

        context = {'sliders': [(sl.pk, json.loads(sl.content)) for sl in sliders_in_rubric],  # right panel
                   'sliders_in_content': [[s.edit_block_num, s.slider.pk] for s in SliderToArticle.objects.filter(art=article).order_by('edit_block_num')],
                   'article': article,
                   'rubric': article.rubric,
                   'eblocks': EditBlock.objects.filter(art=article).order_by('edit_block_num'),
                   'authors': Author.objects.all(),
                   'rubrics': Rubric.objects.all(),
                   'status_choices': ARTICLE_STATUS_CHOICES}

        return render(request, 'editpage.html', context)

    def post(self, request, trans_title=None):
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')

        article = Article.objects.get(trans_title=trans_title)
        if request.POST.get('getContent'):
            parts = [x.data for x in EditBlock.objects.filter(art=article).order_by('edit_block_num')]
            return JsonResponse({'parts': json.dumps(parts)})
        elif request.POST.get('parts') and request.POST.get('sliders') and request.POST.get('htmls'):
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
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')
        article = Article.objects.get(trans_title=trans_title)
        article_edit_url = f"/editor/{trans_title}"
        if spk is None:
            context = {'slides': Slide.objects.filter(rubric=article.rubric).order_by('pk'),
                       'article_edit_url': article_edit_url,
                       'article': article,
                       }
        else:
            if not Slider.objects.filter(pk=spk).exists():  # inside qs incorrect query
                return redirect(f'/editor/slider?article={trans_title}')

            slider_instance = Slider.objects.get(pk=spk)
            context = {'slides': Slide.objects.filter(rubric=article.rubric).order_by('pk'),
                       'slider_struct': json.dumps(slider_instance.compouse_struct()),
                       'article_edit_url': article_edit_url,
                       'article': article,
                       }

        return render(request, 'sliderpage.html', context)

    def post(self, request):
        trans_title, spk = request.GET.get('article'), request.GET.get('spk')
        post_heads = request.POST.keys()
        slider_exists = Slider.objects.filter(pk=spk).exists()
        if not Article.objects.filter(trans_title=trans_title).exists():    # only for url
            return redirect('/editor')
        article = Article.objects.get(trans_title=trans_title)  # only for url, because edit only from article ## ???
        rubric = article.rubric

        if request.POST.get('delSlide'):
            slide = Slide.objects.get(pk=request.POST.get('delSlide'))
            [slide.remove_from_slider(sl) for sl in set(Slider.objects.filter(slider_slides__slde=slide).all())]
            slide.delete()
            return redirect(f'/editor/slider?article={trans_title}') if spk is None else redirect(f'/editor/slider?article={trans_title}&spk={spk}')

        elif request.POST.get("updSlider") and request.POST.get("sliderContent"):
            struct = json.loads(request.POST.get("updSlider"), object_pairs_hook=OrderedDict)
            if slider_exists:
                slider = Slider.objects.get(pk=spk)
                if len(struct) < 1:
                    slider.delete()
                    return JsonResponse({'url': f'/editor/slider?article={trans_title}'})
            else:
                if len(struct) < 1:
                    return JsonResponse({'url': f'/editor/slider?article={trans_title}'})
                slider = Slider()
                slider.save()  # not force update
            
            slider.from_struct_and_content(struct, request.POST.get("sliderContent"), rubric)
            return JsonResponse({'url': f'/editor/slider?article={trans_title}&spk={slider.pk}'})

        elif request.FILES.get('photo') and request.POST.get('name'):
            Slide.objects.get(pk=request.POST.get('name')).img.commit(request.FILES.get('photo'), force_update=True)

        elif request.POST.get('name') and request.POST.get('class') and 'val' in post_heads:
            Slide.objects.get(pk=request.POST.get('name')).upd(request.POST.get('class'), request.POST.get('val'))

        elif request.FILES.get('file'):
            print(request.FILES.get('file'))
            sl = Slide(img=request.FILES.get('file'), label=request.POST.get('label'), descr=request.POST.get('descr'), rubric=rubric)
            sl.save()

        return redirect(f'/editor/slider?article={trans_title}') if spk is None else redirect(f'/editor/slider?article={trans_title}&spk={spk}')


class IconMake(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        article = list(Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=request.GET.get('article')))
        if not article:
            return redirect('/editor')
        article = article[0]
        context = {'article': article}
        return render(request, 'iconpage.html', context)

    def post(self, request):
        article = list(Article.objects.filter(trans_title=request.GET.get('article')))
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
