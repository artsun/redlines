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
from django.contrib.auth import authenticate, login, logout

from .forms import PickyAuthenticationForm

from editor.models import Rubric

class LoginPage(View):

    def get(self, request):
        context = {
            'form': PickyAuthenticationForm(),
            'statistics': Rubric.statistics(),
            'next': request.GET.get('next')
        }
        if request.user.is_authenticated:
            return redirect('/editor')
        context.update(Rubric.navbar_catalogs())
        return render(request, 'login.html', context)

    def post(self, request):
        #print(User.objects.filter(username=request.POST.get('username')).exists())
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            if request.POST.get('next') is None or request.POST.get('next') == 'None':
                return redirect('/editor')
            return redirect('/editor') if not request.POST.get('next') else redirect(request.POST.get('next'))
        else:
            return redirect('/login')


class LogoutPage(View):
    def get(self, request):
        logout(request)
        return redirect('/')


from django.core.mail import EmailMessage


class SubscribePage(View):
    def get(self, request):
        #print(request.GET)
        return redirect('/')

    def post(self, request):
        print(request.POST)
        email = EmailMessage(
            'Hello',
            'Body goes here',
            '',
            [],
            [],  # bcc  - black carbon copy
            reply_to=[],
            headers={},
        )
        email.send()
        return redirect('/')
