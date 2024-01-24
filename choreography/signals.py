from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from choreography.models import Award, Choreography, Score
from choreography.tasks import send_confirmation_email_task
from event.models import AwardType


@receiver(post_save, sender=Choreography, weak=False)
def set_default_award(sender, instance, created, **kwargs):
    if created:
        award_type, new = AwardType.objects.get_or_create(
            is_special=False,
            min_average_score=None,
            max_average_score=None,
            defaults={"name": _("Default award")},
        )
        award_type.event.add(instance.event)

        Award.objects.create(
            choreography=instance, assigned_by_id=1, award_type=award_type
        )


@receiver(post_save, sender=Score, weak=False)
def update_award_type(sender, instance, **kwargs):
    choreography = instance.choreography

    try:
        award_type = AwardType.objects.get(
            event=choreography.event,
            is_special=False,
            min_average_score__lte=choreography.average_score,
            max_average_score__gte=choreography.average_score,
        )
    except AwardType.DoesNotExist:
        award_type = AwardType.objects.get(
            event=choreography.event,
            is_special=False,
            min_average_score=None,
            max_average_score=None,
        )

    default_award = choreography.awards.get(assigned_by_id=1)
    default_award.award_type = award_type
    default_award.save()


@receiver(post_save, sender=Choreography, weak=False)
def send_choreography_email(sender, instance, created, **kwargs):
    if created and not settings.DEBUG:
        recipient = instance.event.contact.email
        subject = _("New registered choreography")
        message = render_to_string(
            "choreography/choreography_registered_email.html",
            {
                "choreography": instance,
            },
        )
        send_confirmation_email_task.delay(
            subject, message, None, [recipient], _("choreography")
        )
