from django.shortcuts import render

# Create your views here.

def citizen_home(request):
    return render(request, "citizens/index.html")