from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Copy, SwapRequest


@transaction.atomic
def make_request(user, copy_id):
    copy = Copy.objects.select_for_update().get(id=copy_id)

    if copy.owner_id == user.id:
        raise ValidationError("Нельзя запросить свою книгу")

    if copy.status != "available":
        raise ValidationError("Книга недоступна")

    profile = user.profile
    if profile.points < 1:
        raise ValidationError("Нужен хотя бы 1 балл. Сначала отдайте книгу")

    profile.points -= 1
    profile.frozen += 1
    profile.save()

    req = SwapRequest.objects.create(copy=copy, requester=user)
    copy.status = "reserved"
    copy.save()
    return req


@transaction.atomic
def cancel_request(user, req_id):
    req = SwapRequest.objects.select_for_update().get(id=req_id)
    if req.requester_id != user.id:
        raise ValidationError("Не ваша заявка")
    if req.status != "pending":
        raise ValidationError("Заявку нельзя отменить")

    profile = user.profile
    profile.frozen -= 1
    profile.points += 1
    profile.save()

    req.status = "cancelled"
    req.save()
    req.copy.status = "available"
    req.copy.save()


@transaction.atomic
def confirm_request(user, req_id, method, track):
    req = SwapRequest.objects.select_for_update().get(id=req_id)
    if req.copy.owner_id != user.id:
        raise ValidationError("Подтвердить может только владелец")
    if req.status != "pending":
        raise ValidationError("Заявка уже обработана")

    requester_profile = req.requester.profile
    if requester_profile.frozen < 1:
        raise ValidationError("У просящего нет замороженных баллов")

    requester_profile.frozen -= 1
    requester_profile.save()

    owner_profile = user.profile
    owner_profile.points += 1
    owner_profile.save()

    req.status = "done"
    req.method = method
    req.track = track
    req.save()

    req.copy.status = "gone"
    req.copy.save()