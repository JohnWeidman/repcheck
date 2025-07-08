from django.shortcuts import render, get_object_or_404
from .models import Congress, Member, Membership, MemberDetails
from django.db.models import OuterRef, Subquery, Prefetch, Q
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache


def congress(request):
    context = {
        "congresses": Congress.objects.all(),
    }
    return render(request, "congress/congress.html", context)


def house_not_home(request):
    congress_id = request.GET.get("congress")
    page = request.GET.get("page")
    sort_by = request.GET.get("sort", "state_name")
    search_query = request.GET.get("search", "").strip()

    sort_options = {
        "name": ["name"],
        "state_name": ["state", "name"],
        "party": ["party", "state", "name"],
        "state_district": ["state", "district"],
    }

    order_by = sort_options.get(sort_by, sort_options["state_name"])
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber = "House of Representatives"

    cache_key_parts = [f"congress_{congress_id}_house_members"]
    if search_query:
        cache_key_parts.append(f"search_{hash(search_query)}")
    cache_key_parts.append(f"sort_{sort_by}")
    congress_cache_key = "_".join(cache_key_parts)

    cached_data = cache.get(congress_cache_key)

    if cached_data is not None:
        house_members = cached_data["queryset"]
    elif congress:
        membership_qs = Membership.objects.filter(
            congress=congress_id, chamber=chamber, member=OuterRef("pk")
        ).order_by("-start_year")

        house_members = (
            Member.objects.filter(
                membership__congress=congress_id,
                membership__chamber=chamber,
            )
            .select_related("memberdetails")
            .prefetch_related(
                Prefetch(
                    "membership_set",
                    queryset=Membership.objects.filter(
                        congress=congress_id
                    ).select_related("congress"),
                    to_attr="congress_memberships",
                )
            )
            .annotate(
                party=Subquery(membership_qs.values("party")[:1]),
                district=Subquery(membership_qs.values("district")[:1]),
                leadership_role=Subquery(membership_qs.values("leadership_role")[:1]),
            )
        )

        if search_query:
            house_members = house_members.annotate(
                search=SearchVector("name", "state", "district", "party")
            ).filter(search=SearchQuery(search_query, search_type="websearch"))

        house_members = house_members.order_by(*order_by)
        cache_data = {"queryset": list(house_members)}
        cache.set(congress_cache_key, cache_data, 60 * 60 * 6)
        
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
        "current_sort": sort_by,
        "sort_options": sort_options.keys(),
        "search_query": search_query,
        "cache_key": congress_cache_key,
    }

    if request.headers.get("HX-Request"):
        return render(request, "congress/partials/house_partial.html", context)
    return render(request, "congress/house.html", context)


def i_am_the_senate(request):
    congress_id = request.GET.get("congress")
    page = request.GET.get("page")
    sort_by = request.GET.get("sort", "state_name")
    search_query = request.GET.get("search", "").strip()

    sort_options = {
        "name": ["name"],
        "state_name": ["state", "name"],
        "party": ["party", "state", "name"],
    }

    order_by = sort_options.get(sort_by, sort_options["state_name"])
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    chamber = "Senate"

    cache_key_parts = [f"congress_{congress_id}_senate_members"]
    if search_query:
        cache_key_parts.append(f"search_{hash(search_query)}")
    cache_key_parts.append(f"sort_{sort_by}")
    congress_cache_key = "_".join(cache_key_parts)

    cached_data = cache.get(congress_cache_key)

    if cached_data is not None:
        senate_members = cached_data["queryset"]
    elif congress:
        membership_qs = Membership.objects.filter(
            congress=congress_id, chamber=chamber, member=OuterRef("pk")
        ).order_by("-start_year")

        senate_members = (
            Member.objects.filter(
                membership__congress=congress_id,
                membership__chamber=chamber,
            )
            .select_related("memberdetails")
            .prefetch_related(
                Prefetch(
                    "membership_set",
                    queryset=Membership.objects.filter(
                        congress=congress_id
                    ).select_related("congress"),
                    to_attr="congress_memberships",
                )
            )
            .annotate(
                party=Subquery(membership_qs.values("party")[:1]),
                leadership_role=Subquery(membership_qs.values("leadership_role")[:1]),
            )
        )

        if search_query:
            senate_members = senate_members.annotate(
                search=SearchVector("name", "state", "party")
            ).filter(search=SearchQuery(search_query, search_type="websearch"))

        senate_members = senate_members.order_by(*order_by)
        cache_data = {"queryset": list(senate_members)}
        cache.set(congress_cache_key, cache_data, 60 * 60 * 6)
    else:
        senate_members = Member.objects.none()

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
        "current_sort": sort_by,
        "sort_options": sort_options.keys(),
        "search_query": search_query,
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
