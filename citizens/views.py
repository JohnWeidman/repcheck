from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import CitizenRegistrationForm


# Create your views here.

def citizen_home(request):
    return render(request, "citizens/index.html")

def citizen_resources(request):
    return render(request, "citizens/citizen_resources.html")

def citizen_registration(request, form_class=CitizenRegistrationForm):
    if request.method == "POST":
        form = form_class(request.POST)
        print(f"Form is valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Form errors: {form.errors}")
    if form.is_valid():
        user = form.save()
        login(request, user)
        return render(request, "citizens/citizen_registration_success.html", {"user": user})
    return render(request, "citizens/citizen_registration.html", {"form": form_class()})