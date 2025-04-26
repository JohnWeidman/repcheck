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
            .annotate(party=Subquery(membership_qs.values("party")[:1]))
            .order_by("state", "name")
        )

    else:
        house_members = Member.objects.none()

    paginator = Paginator(house_members, 10)
    try:
        members_page = paginator.page(page)
    except PageNotAnInteger:
        members_page = paginator.page(1)
    except EmptyPage:
        members_page = paginator.page(paginator.num_pages)

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

    if congress:
        membership_qs = Membership.objects.filter(
            congress=congress_id, chamber=chamber, member=OuterRef("pk")
        ).order_by("-start_year")

        senate_members = (
            Member.objects.filter(
                membership__congress=congress_id, membership__chamber=chamber
            )
            .distinct()
            .annotate(party=Subquery(membership_qs.values("party")[:1]))
            .order_by("state", "name")
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


def details(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member_details = get_object_or_404(MemberDetails, member=member)
    memberships = Membership.objects.filter(member=member).order_by("-start_year")
    current = any(m.is_current() for m in memberships)
    memberships.first_year = memberships.last().start_year if memberships else None
    memberships.last_year = memberships.first().end_year if memberships else None
    memberships.chamber = memberships.first().chamber if memberships else None
    memberships.party = memberships.first().party if memberships else None
    # should probably just load this in the model
    member.last_name = member.name.split(",")[0]
    member.first_name = (
        member.name.split(",")[1] if len(member.name.split(",")) > 1 else ""
    )
    member.full_name = member.first_name + " " + member.last_name

    processed_wiki = (
        member_details.wikipedia.replace(" ", "_") if member_details.wikipedia else None
    )

    member_details.twitter_url = (
        f"https://twitter.com/{member_details.twitter_handle}"
        if member_details.twitter_handle
        else None
    )
    member_details.facebook_url = (
        f"https://www.facebook.com/{member_details.facebook_handle}"
        if member_details.facebook_handle
        else None
    )
    member_details.instagram_url = (
        f"https://www.instagram.com/{member_details.instagram_handle}"
        if member_details.instagram_handle
        else None
    )
    member_details.youtube_url = (
        f"https://www.youtube.com/{member_details.youtube_id}"
        if member_details.youtube_id
        else None
    )
    member_details.open_secrets_url = (
        f"https://www.opensecrets.org/members-of-congress/summary?cid={member_details.open_secrets_id}"
        if member_details.open_secrets_id
        else None
    )
    member_details.wikipedia_url = (
        f"https://en.wikipedia.org/wiki/{processed_wiki}"
        if member_details.wikipedia
        else None
    )

    context = {
        "member_details": member_details,
        "member": member,
        "current": current,
        "memberships": memberships,
    }

    return render(request, "congress/member_detail.html", context)
