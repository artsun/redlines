from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django_resized import ResizedImageField
from django.db import models

from datetime import datetime

import editor

class NewsComment(models.Model):
    gname = models.CharField(verbose_name='Имя', max_length=64, null=False, editable=True)
    short = models.CharField(verbose_name='Подпись', max_length=512, null=False, blank=False, editable=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(verbose_name='Почта', null=True, editable=True)
    article = models.ForeignKey('editor.Article', null=False, on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return f'{self.article.title} -> {self.print_timestamp()} -> {self.gname}'

    @staticmethod
    def create(article, commName, commMail, commTXT):
        commName, commMail, commTXT = commName.strip(), commMail.strip(), commTXT.strip()
        if not commName or not commTXT:
            return
        ncomm = NewsComment(gname=commName, short=commTXT, article=article)
        if commMail:
            ncomm.email = commMail

        ncomm.save()

    def print_timestamp(self):
        one_hour = 3600  # sec
        timedelta = (datetime.now() - self.timestamp.replace(tzinfo=None)).seconds
        if timedelta < one_hour:
            return 'Менее часа назад'
        elif one_hour < timedelta < one_hour*2:
            return 'Час назад'
        elif one_hour*2 < timedelta < one_hour*3:
            return 'Два часа назад'
        else:
            dt = self.timestamp.astimezone(timezone.get_default_timezone())
            cal = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}
            return f'{dt.day} {cal[dt.month]} {dt.year}'#dt.strftime(f'%d {cal[dt.month]} %Y ')  # %H:%M
