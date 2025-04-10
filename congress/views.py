from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership
from django.db.models import Prefetch, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def congress(request):
    context = {
        "congresses": Congress.objects.all(),
    }
    return render(request, "congress/congress.html", context)


def house_not_home(request):
    congress_id = request.GET.get("congress")
    page = request.GET.get("page")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber = "House of Representatives"
    house_members = (
        Member.objects.filter(
            membership__congress=congress_id, membership__chamber=chamber
        )
        .distinct("name")
        .order_by("name")
        if congress
        else []
    )

    p = Paginator(house_members, 10)
    try:
        members_page = p.page(page)
    except PageNotAnInteger:
        members_page = p.page(1)
    except EmptyPage:
        members_page = p.page(p.num_pages)

    context = {
        "congress_number": congress.congress_number if congress else "Unknown",
        "house_members": members_page,
        "congress_id": congress_id,
    }

    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html", context)
    return render(request, "congress/house.html", context)


def i_am_the_senate(request):
    congress_id = request.GET.get("congress")
    page = request.GET.get("page")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber = "Senate"
    senate_members = (
        Member.objects.filter(
            membership__congress=congress_id, membership__chamber=chamber
        )
        .distinct("name")
        .order_by("name")
        if congress
        else []
    )

    p = Paginator(senate_members, 10)
    try:
        members_page = p.page(page)
    except PageNotAnInteger:
        members_page = p.page(1)
    except EmptyPage:
        members_page = p.page(p.num_pages)

    context = {
        "congress_number": congress.congress_number if congress else "Unknown",
        "senate_members": members_page,
        "congress_id": congress_id,
    }
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/senate_partial.html", context)
    return render(request, "congress/senate.html", context)
