from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


def signup(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(
            user=user,
            city=request.POST.get("city", ""),
            points=1,   # стартовый бонус — чтобы сразу можно было попробовать обмен
        )
        return redirect("login")

    return render(request, "signup.html", {"form": form})