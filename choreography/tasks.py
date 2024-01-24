from celery import Task, shared_task, states
from celery.exceptions import NotRegistered
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from choreography.models import Choreography
from event.models import Price

logger = get_task_logger(__name__)


class BaseTaskWithRetry(Task):
    autoretry_for = (NotRegistered, KeyError, Exception)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = 10


@shared_task(bind=True, base=BaseTaskWithRetry, name="send_confirmation_email")
def send_confirmation_email_task(
    self, subject, message, from_email, recipients_list, class_name
):
    sent = send_mail(subject, message, from_email, recipients_list)
    if sent:
        self.update_state(
            state=states.SUCCESS,
            meta=_("Sent new %(value)s registration email.") % {"value": class_name},
        )
        logger.info(_("Sent new %(value)s registration email.") % {"value": class_name})
    else:
        self.update_state(
            state=states.FAILURE,
            meta=_("Failed trying to send a new %(value)s registration email.")
            % {"value": class_name},
        )
        logger.info(
            _("Failed trying to send a new %(value)s registration email.")
            % {"value": class_name}
        )


@shared_task(bind=True, base=BaseTaskWithRetry, name="update_choreography_price")
def update_choreography_price(self):
    updated = 0
    choreographies_qs = Choreography.objects.filter(
        event__end_date__gte=timezone.now().date()
    )
    if choreographies_qs.exists():
        no_deposit_choreographies_pk = [
            choreography.id
            for choreography in choreographies_qs
            if not choreography.deposit_paid
        ]
        no_deposit_choreographies_qs = choreographies_qs.filter(
            id__in=no_deposit_choreographies_pk
        )
        if no_deposit_choreographies_qs.exists():
            for choreography in no_deposit_choreographies_qs:
                price = (
                    Price.objects.filter(
                        event=choreography.event,
                        category_type=choreography.category.type,
                        due_date__gte=timezone.now().date(),
                    )
                    .order_by("due_date")
                    .first()
                )
                choreography.price = price
                choreography.save()
                updated += 1

    if updated:
        message = ngettext(
            "Successfully updated %(count)d choreography price!",
            "Successfully updated %(count)d choreographies price!",
            updated,
        ) % {"count": updated}
        self.update_state(state=states.SUCCESS, meta=message)
        logger.info(message)

    else:
        self.update_state(
            state=states.SUCCESS,
            meta=_("No choreography price was updated today."),
        )
        logger.info(_("No choreography price was updated today."))
