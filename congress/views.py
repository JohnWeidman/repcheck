from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator


# Create your views here.
def congress(request):
    unique_members = Member.objects.order_by("name").prefetch_related(
        Prefetch("membership_set", queryset=Membership.objects.distinct())
    )

    paginator = Paginator(unique_members, 10)  # Show 10 members per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "congresses": Congress.objects.all(),
        "members": page_obj,
        "membership": Membership.objects.all(),
    }

    return render(request, "congress/congress.html", context)


def house_not_home(request):
    congress_id = request.GET.get("congress")
    print("Congress ID:", congress_id)
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber= "House of Representatives"
    house_members = (
        Member.objects.filter(
            membership__congress=congress_id, membership__chamber=chamber
        ).order_by("name")
        if congress
        else []
    )
    # house_members = [
    #     {"name": "John Doe", "state": "CA"},
    #     {"name": "Jane Smith", "state": "NY"},
    # ]
    print("House Members Query:", house_members.query)
    print("House Members Results:", list(house_members))
    context = {
        "congress_number": congress.congress_number if congress else "Unknown",
        "house_members": house_members,
    }

    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html", context)
    return render(request, "congress/house.html", context)


def i_am_the_senate(request):
    congress_id = request.GET.get("congress")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    context = {"congress_number": congress.congress_number if congress else "Unknown"}
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/senate_partial.html", context)
    return render(request, "congress/senate.html", context)
