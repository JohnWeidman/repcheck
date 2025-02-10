from django.shortcuts import render

def legislation_landing_page(request):
    return render(request, 'legislation/legislation.html')

def im_just_a_bill(request):
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/bills_partial.html")
    return render(request, "legislation/bills.html")

def laws(request):
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/laws_partial.html")
    return render(request, "legislation/laws.html")