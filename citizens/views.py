from django.shortcuts import render

# Create your views here.
def citizen_home(request):
    return render(request, "citizens/index.html")

def citizen_resources(request):
    return render(request, "citizens/citizen_resources.html")
