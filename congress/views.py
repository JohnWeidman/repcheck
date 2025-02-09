from django.shortcuts import render

# Create your views here.

def house_not_home(request):
    return render(request, "congress/house.html")

def i_am_the_senate(request):
    return render(request, "congress/senate.html")