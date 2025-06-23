from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership, MemberDetails
from django.db.models import OuterRef, Subquery
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

    if congress:
        membership_qs = Membership.objects.filter(
            congress=congress_id, chamber=chamber, member=OuterRef("pk")
        ).order_by("-start_year")

        house_members = (
            Member.objects.filter(
                membership__congress=congress_id, membership__chamber=chamber
            )
            .distinct()
            .annotate(party=Subquery(membership_qs.values("party")[:1]), 
                      district=Subquery(membership_qs.values("district")[:1]),
                      leadership_role=Subquery(membership_qs.values("leadership_role")[:1]))
            .order_by("state", "name")
        )

    else:
        house_members = Member.objects.none()

    p = Paginator(house_members, 12)
    try:
        members_page = p.page(page)
    except PageNotAnInteger:
        members_page = p.page(1)
    except EmptyPage:
        members_page = p.page(p.num_pages)

    current_page_number = members_page.number
    page_range = p.get_elided_page_range(current_page_number, on_each_side=2, on_ends=0)

    context = {
        "congress_number": congress.congress_number if congress else "Unknown",
        "house_members": members_page,
        "congress_id": congress_id,
        "page_range": page_range,
    }

    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html", context)
    return render(request, "congress/house.html", context)


def i_am_the_senate(request):
    congress_id = request.GET.get("congress")
    page = request.GET.get("page")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber = "Senate"

    if congress:
        membership_qs = Membership.objects.filter(
            congress=congress_id, chamber=chamber, member=OuterRef("pk")
        ).order_by("-start_year")

        senate_members = (
            Member.objects.filter(
                membership__congress=congress_id, membership__chamber=chamber
            )
            .distinct()
            .annotate(party=Subquery(membership_qs.values("party")[:1]), 
                      district=Subquery(membership_qs.values("district")[:1]),
                      leadership_role=Subquery(membership_qs.values("leadership_role")[:1]))
            .order_by("state", "name")
        )

    p = Paginator(senate_members, 12)
    try:
        members_page = p.page(page)
    except PageNotAnInteger:
        members_page = p.page(1)
    except EmptyPage:
        members_page = p.page(p.num_pages)
    current_page_number = members_page.number
    page_range = p.get_elided_page_range(current_page_number, on_each_side=2, on_ends=0)

    context = {
        "congress_number": congress.congress_number if congress else "Unknown",
        "senate_members": members_page,
        "page_range": page_range,
        "congress_id": congress_id,
    }
    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/senate_partial.html", context)
    return render(request, "congress/senate.html", context)


def details(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member_details = get_object_or_404(MemberDetails, member=member)
    memberships = Membership.objects.filter(member=member).order_by("-start_year")
    current = any(m.is_current() for m in memberships)

    most_recent_membership = memberships.first() if memberships else None
    memberships.first_year = memberships.last().start_year if memberships else None

    context = {
        "member_details": member_details,
        "member": member,
        "current": current,
        "memberships": memberships,
        "most_recent_membership": most_recent_membership,
    }

    return render(request, "congress/member_detail.html", context)
