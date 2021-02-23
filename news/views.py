from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse

from editor.models import Image, Slide, Slider, Rubric, Article
from management.models import IndexArticleFresh, IndexArticleHot, Author
from news.models import NewsComment


class IndexPage(View):

    def get(self, request, trans_title=None):

        flist, hlist, pklist, nlist = [], [], [], []
        for x in IndexArticleFresh.objects.select_related('article__icon', 'article__rubric').all().order_by('position'):
            flist.append(x)
            pklist.append(x.article_id)
        for x in IndexArticleHot.objects.select_related('article__icon', 'article__rubric').defer('article__content').all().order_by('position'):
            hlist.append(x)
            pklist.append(x.article_id)
        temp = []
        for x in Article.objects.all().exclude(pk__in=pklist).select_related('icon', 'author', 'rubric').defer('content').order_by('updated')[:10]:
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
        render(request, 'indexpage.html', context)
        return render(request, 'indexpage.html', context)


class NewsPage(View):

    def get(self, request, trans_title=None):
        article = Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=trans_title)
        if not article:
            return redirect('/')
        article = article[0]

        prev = Article.objects.select_related('icon', 'author').filter(rubric=article.rubric, updated__lt=article.updated).first()
        next = Article.objects.select_related('icon', 'author').filter(rubric=article.rubric, updated__gt=article.updated).first()
        you_may_also_like = [a.article for a in IndexArticleHot.objects.select_related('article__icon', 'article__author', 'article__rubric').exclude(article=article) if a.article != prev and a.article != next]
        also_like_one = you_may_also_like[0] if len(you_may_also_like) > 0 else []
        also_like_two = you_may_also_like[1] if len(you_may_also_like) > 1 else []
        #print(article.comments.count())

        context = {
            'article': article,
            'similar': Article.objects.select_related('icon', 'author').filter(rubric=article.rubric).exclude(pk=article.pk).order_by('updated')[:5],
            'news': Article.objects.select_related('icon', 'author').order_by('updated').exclude(rubric=article.rubric)[:5],
            'statistics': Rubric.statistics(),
            'prev': prev,
            'next': next,
            'also_like_one': also_like_one,
            'also_like_two': also_like_two
        }
        context.update(Rubric.navbar_catalogs())
        return render(request, 'newspage.html', context)

    def post(self, request, trans_title=None):
        article = Article.objects.select_related('icon', 'author', 'rubric').filter(trans_title=trans_title)
        if not article:
            return redirect('/')
        article = article[0]
        NewsComment.create(article, request.POST.get('commName'), request.POST.get('commMail'), request.POST.get('commTXT'))
        return JsonResponse({'res': 'ok'})


class NewsSorter(View):

    def get(self, request):
        if request.GET.get('rubric'):
            rubric = Rubric.objects.filter(codename=request.GET.get('rubric'))[:1]
            if rubric:
                rubric = rubric[0]
                rubric_news = rubric.arts.select_related('icon', 'author').all().order_by('updated')
                context = {
                    'rubric': rubric,
                    'rubric_news': rubric_news,
                    'news': Article.objects.select_related('icon', 'author').order_by('updated').exclude(rubric=rubric)[:5],
                }
                html_templ = 'byRubric.html'
            else:
                return redirect('/')
        elif request.GET.get('date'):
            context = Article.by_datetime(request.GET.get('date'))
            html_templ = 'byDate.html'
        elif request.GET.get('author') and request.GET.get('author').isdigit():
            author = Author.objects.filter(pk=request.GET.get('author'))
            if author:
                author = author[0]
                context = {
                    'author': author,
                    'articles': Article.objects.select_related('icon', 'rubric', 'author').filter(author=author).order_by('updated'),
                    'news': Article.objects.select_related('icon', 'rubric').exclude(author=author).order_by('updated')[:5],
                }
                html_templ = 'byAuthor.html'
            else:
                return redirect('/')
        else:
            return redirect('/')

        context.update(Rubric.navbar_catalogs())
        context.update({'statistics': Rubric.statistics()})
        return render(request, html_templ, context)
