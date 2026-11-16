from django.db import models
from django.contrib.auth.models import User


GENRES = [
    ("fantasy", "Фантастика"),
    ("classic", "Классика"),
    ("detective", "Детектив"),
    ("other", "Другое"),
]


class Copy(models.Model):
    STATUS_CHOICES = [
        ("available", "Доступна"),
        ("reserved", "Резерв"),
        ("gone", "Передана"),
    ]
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    genre = models.CharField(max_length=20, choices=GENRES, default="other")
    city = models.CharField(max_length=100)
    condition = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="books/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="copies")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} — {self.title}"


class SwapRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("done", "Завершена"),
        ("cancelled", "Отменена"),
    ]
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name="requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    method = models.CharField(max_length=20, blank=True)
    track = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заявка {self.id} → {self.copy.title}"