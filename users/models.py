from django.db import models
from django.contrib.auth.models import User
from books.models import Copy


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, blank=True)
    points = models.IntegerField(default=0)
    frozen = models.IntegerField(default=0)
    wishlist = models.ManyToManyField(Copy, blank=True)

    def __str__(self):
        return self.user.username