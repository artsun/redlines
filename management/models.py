from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django_resized import ResizedImageField

import editor

import json
from re import sub as rsub
from collections import OrderedDict
from datetime import datetime


class IndexArticleFresh(models.Model):
    article = models.ForeignKey('editor.Article', null=True, on_delete=models.CASCADE, related_name='index_fresh')
    position = models.PositiveIntegerField(null=True, editable=True, unique=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f'{self.position} -> {self.article.title}'


class IndexArticleHot(models.Model):
    article = models.ForeignKey('editor.Article', null=True, on_delete=models.CASCADE, related_name='index_hot')
    position = models.IntegerField(null=True, editable=True, unique=True, validators=[MinValueValidator(1), MaxValueValidator(3)])

    def __str__(self):
        return f'{self.position} -> {self.article.title}'


class Author(models.Model):
    fname = models.CharField(verbose_name='Имя', max_length=64, null=False, editable=True)
    lname = models.CharField(verbose_name='Фамилия', max_length=64, null=False, editable=True)
    login = models.CharField(verbose_name='Логин', max_length=64, null=False, editable=True)
    short = models.CharField(verbose_name='Подпись', max_length=512, null=True, blank=True, editable=True, default="")
    avatar = ResizedImageField(size=[400, 400], crop=['middle', 'center'], quality=100, upload_to='images/', blank=True, null=True)

    def __str__(self):
        return f'{self.fname} {self.lname}'
