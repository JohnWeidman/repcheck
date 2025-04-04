from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership
from django.db.models import Prefetch

# Create your views here.
def congress(request):
    unique_members = Member.objects.prefetch_related(
        Prefetch("membership_set", queryset=Membership.objects.order_by("-member").distinct())
    )
    with open("membership_set.txt", "w") as file:
        for member in unique_members:
            file.write(f"{member}\n")
    context = {
        "congresses": Congress.objects.all(),
        "members": unique_members,
        "membership": Membership.objects.all(),
    }

    with open("debug_membership.txt", "w") as file:
        for membership in context["membership"]:
            file.write(f"{membership}\n")
        file.write("\n\n\n")
        for member in context["members"]:
            file.write(f"{member}\n")
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