from django.shortcuts import render

# Create your views here.
def congress(request):
    return render(request, "congress/congress.html")

def house_not_home(request):
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html")
    return render(request, "congress/house.html")

def i_am_the_senate(request):
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/senate_partial.html")
    return render(request, "congress/senate.html")