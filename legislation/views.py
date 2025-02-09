from django.shortcuts import render

# Create your views here.

def legislation_landing_page(request):
    return render(request, 'legislation/legislation.html')

def im_just_a_bill(request):
    return render(request, 'legislation/bills.html')

def laws(request):
    return render(request, 'legislation/laws.html')