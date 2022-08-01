from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect


def redirect2admin(request):
    return HttpResponseRedirect(reverse('admin:index'))
