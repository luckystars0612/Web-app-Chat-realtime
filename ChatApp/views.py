
from django.shortcuts import render,redirect
# Create your views here.

def homepage(request, **kwargs):
    return render(request,"homepage.html")
