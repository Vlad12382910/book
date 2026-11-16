import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings

from .models import Copy, SwapRequest, GENRES
from .services import make_request, cancel_request, confirm_request


def book_list(request):
    qs = Copy.objects.filter(status="available").select_related("owner")

    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q))

    city = request.GET.get("city", "")
    if city:
        qs = qs.filter(city__icontains=city)

    genre = request.GET.get("genre", "")
    if genre:
        qs = qs.filter(genre=genre)

    condition = request.GET.get("condition", "")
    if condition:
        qs = qs.filter(condition__icontains=condition)

    sort = request.GET.get("sort", "-created_at")
    if sort in ("-created_at", "created_at", "title", "-title", "author", "-author"):
        qs = qs.order_by(sort)

    page = Paginator(qs, 20).get_page(request.GET.get("page", 1))

    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "book_list.html", {
        "page": page,
        "genres": GENRES,
        "q": q,
        "city": city,
        "genre": genre,
        "condition": condition,
        "sort": sort,
        "base_query": params.urlencode(),
    })


def book_json(request):
    q = request.GET.get("q", "")
    qs = Copy.objects.filter(status="available")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q))
    return JsonResponse({
        "items": [
            {"id": c.id, "title": c.title, "author": c.author}
            for c in qs[:10]
        ]
    })


def book_detail(request, pk):
    copy = get_object_or_404(Copy, pk=pk)
    return render(request, "book_detail.html", {"copy": copy})


@login_required
def book_form(request, pk=None):
    copy = None
    if pk:
        copy = get_object_or_404(Copy, pk=pk, owner=request.user)

    if request.method == "POST":
        if copy is None:
            copy = Copy(owner=request.user)

        copy.title = request.POST.get("title", "").strip()
        copy.author = request.POST.get("author", "").strip()
        copy.genre = request.POST.get("genre", "other")
        copy.city = request.POST.get("city", "").strip()
        copy.condition = request.POST.get("condition", "").strip()
        copy.description = request.POST.get("description", "").strip()

        if request.FILES.get("image"):
            f = request.FILES["image"]
            if f.size > 5 * 1024 * 1024:
                messages.error(request, "Файл больше 5 МБ")
                return render(request, "book_form.html",
                              {"copy": copy, "genres": GENRES})
            copy.image = f

        copy.save()
        return redirect("book_detail", pk=copy.pk)

    return render(request, "book_form.html", {"copy": copy, "genres": GENRES})


@login_required
def book_delete(request, pk):
    copy = get_object_or_404(Copy, pk=pk, owner=request.user)
    if request.method == "POST":
        copy.delete()
        return redirect("book_list")
    return render(request, "book_delete.html", {"copy": copy})


@login_required
def make_request_view(request, pk):
    try:
        req = make_request(request.user, pk)
        if req.copy.owner.email:
            send_mail(
                "Книгу запросили",
                f"{req.requester.username} хочет «{req.copy.title}»",
                settings.DEFAULT_FROM_EMAIL,
                [req.copy.owner.email],
                fail_silently=True,
            )
        messages.success(request, "Заявка создана, 1 балл заморожен")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("book_detail", pk=pk)


@login_required
def my_requests(request):
    incoming = SwapRequest.objects.filter(copy__owner=request.user)
    outgoing = SwapRequest.objects.filter(requester=request.user)
    return render(request, "my_requests.html", {
        "incoming": incoming,
        "outgoing": outgoing,
    })


@login_required
def cancel_request_view(request, pk):
    try:
        cancel_request(request.user, pk)
        messages.success(request, "Отменено, балл возвращён")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("my_requests")


@login_required
def confirm_request_view(request, pk):
    req = get_object_or_404(SwapRequest, pk=pk, copy__owner=request.user)

    if request.method == "POST":
        try:
            confirm_request(
                request.user,
                pk,
                request.POST.get("method", "meeting"),
                request.POST.get("track", ""),
            )
            messages.success(request, "Подтверждено, балл начислен")
            return redirect("my_requests")
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, "confirm.html", {"req": req})


def stats(request):
    total = Copy.objects.count()
    available = Copy.objects.filter(status="available").count()
    total_requests = SwapRequest.objects.count()
    done = SwapRequest.objects.filter(status="done").count()
    share = round(done / total_requests * 100, 1) if total_requests else 0
    by_genre = list(Copy.objects.values("genre").annotate(c=Count("id")))

    return render(request, "stats.html", {
        "total": total,
        "available": available,
        "requests": total_requests,
        "done": done,
        "share": share,
        "by_genre": by_genre,
    })


def export_csv(request):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="swaps.csv"'
    w = csv.writer(resp)
    w.writerow(["ID", "Книга", "Отдал", "Получил", "Статус"])
    for r in SwapRequest.objects.select_related("copy__owner", "requester"):
        w.writerow([
            r.id,
            r.copy.title,
            r.copy.owner.username,
            r.requester.username,
            r.get_status_display(),
        ])
    return resp