from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership

# Create your views here.
def congress(request):
    context = {
        "congresses": Congress.objects.all(),
        "members": Member.objects.all(),
        "membership": Membership.objects.all(),

    }
    return render(request, "congress/congress.html", context)

def house_not_home(request):
    congress_id = request.GET.get("congress")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    context={"congress_number": congress.congress_number if congress else "Unknown"}
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html", context)
    return render(request, "congress/house.html", context)

def i_am_the_senate(request):
    congress_id = request.GET.get("congress")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    context={"congress_number": congress.congress_number if congress else "Unknown"}
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/senate_partial.html", context)
    return render(request, "congress/senate.html", context)