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

from .models import Image, Slide, Slider, Rubric, Article, SliderToArticle, ArticleToRubric, EditBlock, Icon


class ArtListPage(View):
    #login_url = '/login/'

    def get(self, request):
        context = {'artlist': Article.objects.all().order_by('-updated'),}
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
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/')

        article = Article.objects.get(trans_title=trans_title)
        if request.GET.get('preview'):
            context = {'article': article,
                        'linkback': 1}
            return render(request, 'newspage.html', context)

        
        rubric = ArticleToRubric.objects.get(art=article).rubric
        sliders_in_rubric = Slider.objects.filter(rubric=ArticleToRubric.objects.get(art=article).rubric).order_by('pk')

        context = {'sliders': [(sl.pk, json.loads(sl.content)) for sl in sliders_in_rubric],  # right panel
                   'sliders_in_content': [[s.edit_block_num, s.slider.pk] for s in SliderToArticle.objects.filter(art=article).order_by('edit_block_num')],
                   'article': article,
                   'rubric': rubric,
                   'eblocks': EditBlock.objects.filter(art=article).order_by('edit_block_num'), }

        return render(request, 'editpage.html', context)

    def post(self, request, trans_title=None):
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')

        article = Article.objects.get(trans_title=trans_title)
        if request.POST.get('getContent'):
            parts = [x.data for x in EditBlock.objects.filter(art=article).order_by('edit_block_num')]
            return JsonResponse({'parts': json.dumps(parts)})
        elif request.POST.get('artUpd'):
            title = json.loads(request.POST.get('artUpd'))
            if len(title) < 120:
                article.update_title(title)
            return JsonResponse({'url': f'/editor/{article.trans_title}'})
        elif None not in [request.POST.get(x) for x in ('parts', 'sliders', 'htmls')]:
            args = [request.POST.get(x) for x in ('parts', 'sliders', 'htmls', 'artUpdates')]
            article.full_update(*args)
            return JsonResponse({'url': f'/editor/{article.trans_title}?preview=1'})
        elif request.POST.get('dropArticle'):
            article.delete()
        return JsonResponse({'url': f'/editor/{article.trans_title}'})


class SliderMake(View):
    #login_url = '/login/'

    def get(self, request):
        trans_title, spk = request.GET.get('article'), request.GET.get('spk')
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')
        article = Article.objects.get(trans_title=trans_title)
        article_edit_url = f"/editor/{trans_title}"
        rubric = ArticleToRubric.objects.get(art=article).rubric
        if spk is None:
            context = {'slides': Slide.objects.filter(rubric=rubric).order_by('pk'),
                       'article_edit_url': article_edit_url,
                       'article': article,
                       }
        else:
            if not Slider.objects.filter(pk=spk).exists():  # inside qs incorrect query
                return redirect(f'/editor/slider?article={trans_title}')

            slider_instance = Slider.objects.get(pk=spk)
            context = {'slides': Slide.objects.filter(rubric=rubric).order_by('pk'),
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
        rubric = ArticleToRubric.objects.get(art=article).rubric

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

class IconMake(View):
    #login_url = '/login/'

    def get(self, request):
        trans_title = request.GET.get('article')
        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')
        article = Article.objects.get(trans_title=trans_title)
        rubric = ArticleToRubric.objects.get(art=article).rubric
        article_edit_url = f"/editor/{trans_title}"
        icons = Icon.objects.filter(rubric=rubric).order_by('pk')

        context = {'icons': icons,
                   'article': article, }

        return render(request, 'iconpage.html', context)

    def post(self, request):
        trans_title = request.GET.get('article')
        post_heads = request.POST.keys()

        if not Article.objects.filter(trans_title=trans_title).exists():
            return redirect('/editor')
        article = Article.objects.get(trans_title=trans_title)
        rubric = ArticleToRubric.objects.get(art=article).rubric

        if request.POST.get('delIcon'):
            Icon.objects.get(pk=request.POST.get('delIcon')).delete()
            return redirect(f'/editor/icon?article={trans_title}')
        elif request.FILES.get('image') and request.POST.get('ipk'):
            Icon.objects.get(pk=request.POST.get('ipk')).upd_image(request.FILES.get('image'))
        elif request.FILES.get('file'):
            icon = Icon(img=request.FILES.get('file'), rubric=rubric, label=request.POST.get('label'), short=request.POST.get('descr'))
            icon.save()
        elif request.POST.get('ipk') and request.POST.get('class') and 'val' in post_heads:
            Icon.objects.get(pk=request.POST.get('ipk')).upd(request.POST.get('class'), request.POST.get('val'))
        elif request.POST.get('iconStruct'):
            article.set_icon(json.loads(request.POST.get('iconStruct')))
        return redirect(f'/editor/icon?article={trans_title}')



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
