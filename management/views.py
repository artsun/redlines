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
            return redirect('/editor') if not request.POST.get('next') else redirect(request.POST.get('next'))
        else:
            return redirect('/login')


class LogoutPage(View):
    def get(self, request):
        logout(request)
        return redirect('/')
