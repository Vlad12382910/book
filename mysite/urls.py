from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth

from users.views import signup
from books import views as v


urlpatterns = [
    path("admin/", admin.site.urls),

    path("signup/", signup, name="signup"),
    path("login/", auth.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("password/", auth.PasswordChangeView.as_view(
        template_name="password_change.html", success_url="/",
    ), name="password_change"),

    path("", v.book_list, name="book_list"),
    path("api/books/", v.book_json, name="book_json"),

    path("book/new/", v.book_form, name="book_create"),
    path("book/<int:pk>/", v.book_detail, name="book_detail"),
    path("book/<int:pk>/edit/", v.book_form, name="book_edit"),
    path("book/<int:pk>/delete/", v.book_delete, name="book_delete"),

    path("request/<int:pk>/", v.make_request_view, name="make_request"),
    path("my/", v.my_requests, name="my_requests"),
    path("cancel/<int:pk>/", v.cancel_request_view, name="cancel"),
    path("confirm/<int:pk>/", v.confirm_request_view, name="confirm"),

    path("stats/", v.stats, name="stats"),
    path("export.csv", v.export_csv, name="export_csv"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)