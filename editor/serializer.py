
from rest_framework.serializers import ModelSerializer, RelatedField, CharField

from editor.models import Rubric, Article
from management.models import IndexArticleFresh, IndexArticleHot, Author


class ArticleField(RelatedField):
    def to_representation(self, value):
        return {'title': value.title, 'fresh_lg': value.fresh_lg(), 'fresh_med': value.fresh_med(),
                'fresh_sm': value.fresh_sm(), 'get_news_url': value.get_news_url(), 'icon': {'label': value.icon.label},
                'rubric': {'title': value.rubric.title}}


class FreshSerializer(ModelSerializer):
    article = ArticleField(read_only=True)  #ArticleSerializer(many=True, read_only=True) source='article.title',
    class Meta:
        model = IndexArticleFresh
        fields = '__all__'
