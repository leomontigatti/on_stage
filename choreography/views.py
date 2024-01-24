import json
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST
from weasyprint import HTML

from academy.models import Dancer, Professor
from academy.views import has_academy, is_judge, is_owner, is_soundman
from choreography.forms import ChoreographyForm
from choreography.models import Award, Choreography, Feedback, Payment, Score
from event.models import AwardType, Event, Price, Schedule
from seminar.models import SeminarRegistration

OSUser = get_user_model()


@login_required
def event_list_view(request, sender):
    queryset = Event.objects.all()
    model = {
        "choreography": Choreography,
        "award": Award,
        "payment": Payment,
        "score": Score,
        "seminarregistration": SeminarRegistration,
        "music": "music",
    }
    context = {
        "model": model.get(sender),
        "event_list": queryset,
        "title": _("Event list"),
    }
    return render(request, "choreography/event_list.html", context)


# region Choreography


@login_required
@user_passes_test(has_academy)
def choreography_list_view(request, event_pk):
    """
    Display a list of Choreography instances related to the logged-in user's academy
    and the selected event. Display a GET method searching form and a paginator that shows
    up to ten items per page.

    **Context:**

    ``model``
        The Choreography class.
    ``event``
        The selected Event instance.
    ``page_obj``
        A Page instance.
    ``search_input``
        A string with the user search parameters if any.
    ``search_text``
        A string to fill the HTML input element.

    **Template:**

    :template:`choreography/choreography_list.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    queryset = Choreography.objects.filter(academy=request.user.academy, event=event)
    search_input = request.GET.get("search_input", "")

    if search_input:
        queryset = queryset.filter(
            Q(name__icontains=search_input)
            | Q(dance_mode__name__icontains=search_input)
            | Q(professors__first_name__icontains=search_input)
            | Q(professors__last_name__icontains=search_input)
            | Q(category__name__icontains=search_input)
            | Q(category__type__icontains=search_input)
        )

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Choreography,
        "event": event,
        "page_obj": page_obj,
        "search_input": search_input,
        "search_text": _("Search by dance mode, category or professor."),
        "title": _("Choreography list"),
    }
    return render(request, "choreography/choreography_list.html", context)


@login_required
@user_passes_test(has_academy)
def choreography_create_view(request, event_pk):
    """
    Display a form to create a new Choreography instance.

    **Context:**

    ``model``
        The Choreography class.
    ``dancers_age``
        A list that contains all fetched dancers age.
    ``form``
        A ChoreographyForm instance.

    **Template:**

    :template:`choreography/choreography_form.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    if event.registration_ended:
        messages.warning(
            request,
            _("Registration for the selected event has ended."),
        )
        return redirect("event_list")

    dancers_age = [
        dancer.age
        for dancer in Dancer.objects.filter(academy=request.user.academy).order_by(
            "-birth_date"
        )
    ]

    form = ChoreographyForm(
        request.POST or None,
        request.FILES or None,
        academy=request.user.academy,
        event=event,
    )

    context = {
        "model": Choreography,
        "dancers_age": dancers_age,
        "form": form,
        "title": _("Add choreography"),
    }

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        form.instance.event = event
        form.instance.is_locked = True

        # Set the price according to the selected category.
        category = form.cleaned_data.get("category")
        price = Price.objects.filter(
            event=event,
            category_type=category.type,
            due_date__gte=timezone.now().date(),
        ).first()
        if price:
            form.instance.price = price
        else:
            messages.error(
                request,
                _(
                    "The system could not add a new choreography since there is no price set for it."
                ),
            )
            return redirect("choreography_list", event_pk=event.pk)

        # Set the schedule according to the selected dance mode and event.
        dance_mode = form.cleaned_data.get("dance_mode")
        schedule = Schedule.objects.filter(
            event=event,
            dance_mode=dance_mode,
        ).first()
        if schedule:
            form.instance.schedule = schedule
        else:
            messages.error(
                request,
                _(
                    "The system could not add a new choreography since there is no schedule set for it."
                ),
            )
            return redirect("choreography_list", event_pk=event.pk)

        form.save()
        messages.success(request, _("Successfully added a new choreography!"))
        return redirect("choreography_list", event_pk=event.pk)

    return render(request, "choreography/choreography_form.html", context)


@login_required
@user_passes_test(has_academy)
def choreography_detail_view(request, choreography_pk):
    """
    Display a single Choreography instance.
    Redirect the user if the Choreography instance is not related.

    **Context:**

    ``model``
        The Choreography class.
    ``object``
        A Choreography instance.

    **Template:**

    :template:`choreography/choreography_detail.html`
    """

    choreography = get_object_or_404(Choreography, pk=choreography_pk)

    if not is_owner(request, choreography):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    context = {
        "model": Choreography,
        "object": choreography,
        "title": _("Choreography detail"),
    }
    return render(request, "choreography/choreography_detail.html", context)


@login_required
@user_passes_test(has_academy)
def choreography_update_view(request, choreography_pk):
    """
    Display a form to update an existing Choreography instance.
    Redirect the user if the Choreography instance is not related.

    **Context:**

    ``model``
        The Choreography class.
    ``dancers_age``
        A list that contains all fetched dancers age.
    ``object``
        A Choreography instance.
    ``form``
        A ChoreographyForm instance.

    **Template:**

    :template:`choreography/choreography_form.html`
    """

    choreography = get_object_or_404(Choreography, pk=choreography_pk)
    event = choreography.event

    if any([not is_owner(request, choreography), event.ended]):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    dancers_age = [
        dancer.age for dancer in Dancer.objects.filter(academy=request.user.academy)
    ]

    form = ChoreographyForm(
        request.POST or None,
        request.FILES or None,
        academy=request.user.academy,
        event=event,
        instance=choreography,
    )

    context = {
        "model": Choreography,
        "dancers_age": dancers_age,
        "object": choreography,
        "form": form,
        "title": _("Update choreography")
        if not choreography.is_locked
        else _("Complete choreography"),
        "event": event,
    }

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        form.instance.event = event
        form.instance.is_locked = True

        # Set the price according to the selected category if changed.
        if "category" in form.changed_data:
            category = form.cleaned_data.get("category")
            price = Price.objects.filter(
                event=event,
                category_type=category.type,
                due_date__gte=timezone.now().date(),
            ).first()
            if price:
                form.instance.price = price
            else:
                messages.error(
                    request,
                    _(
                        "The system could not add a new choreography since there is no price set for it."
                    ),
                )
                return redirect("choreography_list", event_pk=event.pk)

        # Set the schedule according to the selected dance mode and event if changed.
        if "dance_mode" in form.changed_data:
            dance_mode = form.cleaned_data.get("dance_mode")
            schedule = Schedule.objects.filter(
                event=event,
                dance_mode=dance_mode,
            ).first()
            if schedule:
                form.instance.schedule = schedule
            else:
                messages.error(
                    request,
                    _(
                        "The system could not add a new choreography since there is no schedule set for it."
                    ),
                )
                return redirect("choreography_list", event_pk=event.pk)

        form.save()
        messages.success(
            request, _("Successfully updated the choreography information!")
        )
        return redirect("choreography_list", event_pk=event.pk)

    return render(request, "choreography/choreography_form.html", context)


@login_required
@require_POST
def set_order_number(request):
    choreographies_dict = json.loads(request.POST.get("choreographies_json"))
    updated = 0

    if "set_new_order" in request.POST:
        for key, value in choreographies_dict.items():
            if value:
                choreography = Choreography.objects.get(pk=key)
                choreography.order_number = int(value)
                choreography.save(update_fields=["order_number"])
                updated += 1

    elif "set_default_order" in request.POST:
        ids_list = [key for key, value in choreographies_dict.items()]
        queryset = Choreography.objects.filter(pk__in=ids_list)
        updated = queryset.update(order_number=None)
        ordered_list = queryset.filter(
            event__end_date__gte=timezone.now().date()
        ).order_by("schedule__date", "schedule__time", "category__max_age")

        i = 1
        for choreography in ordered_list:
            choreography.order_number = i
            choreography.save()
            i += 1

    message = ngettext(
        "Successfully updated %(count)d choreography order number!",
        "Successfully updated %(count)d choreographies order number!",
        updated,
    ) % {"count": updated}
    messages.info(request, message)
    return redirect("admin:choreography_choreography_changelist")


# endregion
# region Award


@login_required
@user_passes_test(has_academy)
def award_list_view(request, event_pk):
    """
    Display a list of Choreography instances related to the logged-in user's academy
    and the selected event. Display a GET method searching form and a paginator that shows
    up to ten items per page.

    **Context:**

    ``model``
        The Award class.
    ``event``
        The selected Event instance.
    ``page_obj``
        A Page instance.
    ``search_input``
        A string with the user search parameters if any.
    ``search_text``
        A string to fill the HTML input element.

    **Template:**

    :template:`choreography/award_list.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    queryset = Choreography.objects.filter(academy=request.user.academy, event=event)
    search_input = request.GET.get("search_input", "")

    if search_input:
        queryset = queryset.filter(
            Q(name__icontains=search_input)
            | Q(dance_mode__name__icontains=search_input)
            | Q(professors__first_name__icontains=search_input)
            | Q(professors__last_name__icontains=search_input)
            | Q(category__name__icontains=search_input)
            | Q(category__type__icontains=search_input)
        )

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Award,
        "event": event,
        "page_obj": page_obj,
        "search_input": search_input,
        "search_text": _("Search by dance mode, category or professor."),
        "title": _("Award list"),
    }
    return render(request, "choreography/award_list.html", context)


@login_required
@user_passes_test(has_academy)
def award_detail_view(request, choreography_pk):
    """
    Display a single Choreography instance.
    Redirect the user if the Award instance is not related.

    **Context:**

    ``model``
        The Award class.
    ``object``
        A Choreography instance.
    ``awards_qs``
        A queryset with all Choreography instance related awards.

    **Template:**

    :template:`choreography/award_detail.html`
    """

    choreography = get_object_or_404(Choreography, pk=choreography_pk)

    if any([not is_owner(request, choreography), not choreography.show_awards]):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    context = {
        "model": Award,
        "object": choreography,
        "awards_qs": choreography.awards.order_by("assigned_by"),
        "title": _("Award detail"),
    }
    return render(request, "choreography/award_detail.html", context)


@login_required
def award_certificate(request, choreography_pk, sender, sender_pk):
    """
    Render a PDF file with the award information.

    **Context:**

    ``choreography``
        A Choreography instance.
    ``award``
        An Award instance.
    ``awarded``
        A Professor or a Dancer instance.
    ``event``
        An Event instance.
    ``judges_list``
        A list containing the event related judges.

    **Template:**

    :template:`choreography/award_certificate.html`
    """

    choreography = get_object_or_404(Choreography, pk=choreography_pk)
    superuser = OSUser.objects.filter(is_superuser=True).first()
    award = choreography.awards.get(assigned_by=superuser)

    if sender == "professor":
        awarded = get_object_or_404(Professor, pk=sender_pk)
    elif sender == "dancer":
        awarded = get_object_or_404(Dancer, pk=sender_pk)

    judges_list = [judge.__str__() for judge in choreography.event.judge.all()]

    context = {
        "choreography": choreography,
        "award": award,
        "awarded": awarded,
        "event": choreography.event,
        "judges_list": judges_list,
    }

    html_string = render_to_string(
        "choreography/award_certificate.html", context, request
    )
    pdf_file = HTML(
        string=html_string, base_url=request.build_absolute_uri()
    ).write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    return response


# endregion
# region Payment


@login_required
@user_passes_test(has_academy)
def payment_list_view(request, event_pk):
    """
    Display a list of Choreography instances related to the logged-in user's academy
    and the selected event. Display a GET method searching form and a paginator that shows
    up to ten items per page.

    **Context:**

    ``model``
        The Payment class.
    ``event``
        The selected Event instance.
    ``page_obj``
        A Page instance.
    ``search_input``
        A string with the user search parameters if any.
    ``search_text``
        A string to fill the HTML input element.

    **Template:**

    :template:`choreography/payment_list.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    queryset = Choreography.objects.filter(academy=request.user.academy, event=event)
    search_input = request.GET.get("search_input", "")

    if search_input:
        queryset = queryset.filter(
            Q(name__icontains=search_input) | Q(category__name__icontains=search_input)
        )

    amount_total, balance_total, deposit_total = 0, 0, 0
    for choreography in queryset:
        amount_total += choreography.total_price
        deposit_total += choreography.deposit_amount
        balance_total += choreography.balance

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Payment,
        "event": event,
        "page_obj": page_obj,
        "search_input": search_input,
        "search_text": _("Search by category or choreography name."),
        "choreographies_amount": queryset.count(),
        "amount_total": amount_total,
        "deposit_total": deposit_total,
        "balance_total": balance_total,
        "title": _("Payment list"),
    }
    return render(request, "choreography/payment_list.html", context)


@login_required
@user_passes_test(has_academy)
def payment_detail(request, choreography_pk):
    """
    Display a single Choreography instance.
    Redirect the user if the Choreography instance is not related.

    **Context:**

    ``model``
        The Choreography class.
    ``event``
        The selected Event instance.
    ``object``
        A Choreography instance.
    ``next_due_date``
        A date object with the next due date information.

    **Template:**

    :template:`choreography/choreography_detail.html`
    """

    choreography = get_object_or_404(Choreography, pk=choreography_pk)
    if not is_owner(request, choreography):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    event = choreography.event
    price = Price.objects.filter(event=event, due_date__gte=date.today()).first()
    if price:
        next_due_date = price.due_date
    else:
        next_due_date = Price.objects.filter(event=event).last().due_date

    context = {
        "model": Payment,
        "event": event,
        "object": choreography,
        "next_due_date": next_due_date,
        "title": _("Payment detail"),
    }
    return render(request, "choreography/payment_detail.html", context)


@login_required
@require_POST
def manage_payments_view(request):
    selected_choreographies_id = request.POST.get("selected_choreographies_id")
    if not selected_choreographies_id:
        messages.warning(request, _("Select at least one choreography."))
        return redirect("admin:choreography_choreography_changelist")

    choreographies_id_list = list(selected_choreographies_id.split(","))
    choreographies_qs = Choreography.objects.filter(pk__in=choreographies_id_list)

    selected_payment_method_id = request.POST.get("payment_method")
    if not selected_payment_method_id:
        messages.warning(request, _("Select a valid payment method."))
        return redirect("admin:choreography_choreography_changelist")

    selected_payment_method = int(request.POST.get("payment_method"))

    payment_date_str = request.POST.get("payment_date")
    if not payment_date_str:
        messages.warning(request, _("Select a valid payment date."))
        return redirect("admin:choreography_choreography_changelist")

    payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()

    if payment_date > timezone.now().date():
        messages.warning(request, _("The payment date cannot be later than today."))
        return redirect("admin:choreography_choreography_changelist")

    created = 0

    if "pay_deposit_amount" in request.POST:
        for choreography in choreographies_qs:
            if not choreography.deposit_paid:
                Payment.objects.create(
                    choreography=choreography,
                    amount=choreography.deposit_amount,
                    type=selected_payment_method,
                    date=payment_date,
                )
                created += 1
    elif "pay_balance_amount" in request.POST:
        for choreography in choreographies_qs:
            Payment.objects.create(
                choreography=choreography,
                amount=choreography.balance,
                type=selected_payment_method,
                date=payment_date,
            )
            created += 1

    message = ngettext(
        "Successfully created %(count)d payment!",
        "Successfully created %(count)d payments!",
        created,
    ) % {"count": created}
    messages.info(request, message)
    return redirect("admin:choreography_choreography_changelist")


# endregion
# region Score


@login_required
@user_passes_test(is_judge)
def score_list_view(request, event_pk):
    """
    Display a list of Score instances related to the logged-in user
    and the selected event. Display a paginator that shows up to ten items per page.

    **Context:**

    ``model``
        The Score class.
    ``event``
        The selected Event instance.
    ``page_obj``
        A Page instance.

    **Template:**

    :template:`choreography/score_list.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    score_qs = Score.objects.filter(
        judge=request.user,
        choreography__event=event,
        choreography__schedule__date=timezone.now().date(),
    ).order_by("choreography__order_number")

    if request.method == "POST":
        score_pk = request.POST.get("score_pk")
        score = get_object_or_404(Score, pk=score_pk)
        if score.is_locked:
            messages.warning(
                request, _("You don't have permissions to perform this action.")
            )
            return redirect("home")

        score_feedback = request.FILES.get("score_feedback")
        if score_feedback:
            Feedback.objects.update_or_create(
                score=score, defaults={"audio_file": score_feedback}
            )

        score_value = request.POST.get("score_value")
        score.value = score_value if score_value else 0
        score.save()

    paginator = Paginator(score_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Score,
        "event": event,
        "page_obj": page_obj,
        "title": _("Score list"),
    }
    return render(request, "choreography/score_list.html", context)


@login_required
@user_passes_test(is_judge)
def toggle_disqualified(request, choreography_pk):
    choreography = get_object_or_404(Choreography, pk=choreography_pk)
    choreography.is_disqualified = not choreography.is_disqualified
    choreography.save(update_fields=["is_disqualified"])

    # Set proper award type if the choreography was qualified back.
    if not choreography.is_disqualified:
        try:
            award_type = AwardType.objects.get(
                event=choreography.event,
                is_special=False,
                min_average_score__lte=choreography.average_score,
                max_average_score__gte=choreography.average_score,
            )
        except AwardType.DoesNotExist:
            pass

    # Set default award type if the choreography was disqualified.
    else:
        award_type = AwardType.objects.get(
            event=choreography.event,
            is_special=False,
            min_average_score=None,
            max_average_score=None,
        )

    superuser = OSUser.objects.filter(is_superuser=True).first()

    default_award = choreography.awards.get(assigned_by=superuser)
    default_award.award_type = award_type
    default_award.save(update_fields=["award_type"])

    page_number = request.GET.get("page", "")
    response = redirect("score_list", event_pk=choreography.event.pk)
    if page_number:
        response["Location"] += f"?page={page_number}"
    return response


@login_required
@user_passes_test(is_judge)
def lock_scores(request, event_pk):
    event = get_object_or_404(Event, pk=event_pk)
    scores_qs = Score.objects.filter(
        judge=request.user,
        choreography__event=event,
        choreography__schedule__date=timezone.now().date(),
    )
    locked_scores = scores_qs.update(is_locked=True)

    if locked_scores:
        message = ngettext(
            "Successfully locked %(count)d score!",
            "Successfully locked %(count)d scores!",
            locked_scores,
        ) % {"count": locked_scores}
        messages.success(request, message)
    else:
        messages.info(request, _("No scores were found to lock."))
    return redirect("score_list", event_pk=event.pk)


@login_required
@user_passes_test(is_judge)
def feedback_delete_view(request, score_pk):
    score = get_object_or_404(Score, pk=score_pk)
    if score.is_locked:
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    if hasattr(score, "feedback"):
        feedback = score.feedback
        feedback.delete()
        messages.success(request, _("Feedback successfully deleted."))

    page_number = request.GET.get("page", "")
    response = redirect("score_list", event_pk=score.choreography.event.pk)
    if page_number:
        response["Location"] += f"?page={page_number}"
    return response


# endregion
# region Soundman


def get_event_schedule_list(event):
    schedule_list = []
    dates_list = []
    for schedule in Schedule.objects.filter(event=event):
        if schedule.date not in dates_list:
            dates_list.append(schedule.date)
            schedule_list.append(schedule)
    return schedule_list


@login_required
@user_passes_test(is_soundman)
def music_list(request, event_pk):
    event = get_object_or_404(Event, pk=event_pk)

    choreography_qs = Choreography.objects.filter(event=event).exclude(
        order_number__isnull=True
    )

    context = {
        "model": "music",
        "event": event,
        "title": _("Music list"),
        "schedule_list": get_event_schedule_list(event),
    }

    selected_schedule = request.GET.get("schedule_filter")
    if selected_schedule:
        schedule = get_object_or_404(Schedule, pk=selected_schedule)
        choreography_qs = choreography_qs.filter(schedule__date=schedule.date)
        context["selected_schedule"] = schedule

    paginator = Paginator(choreography_qs, 10)
    page_number = request.GET.get("page", "")
    page_obj = paginator.get_page(page_number)
    context["page_obj"] = page_obj

    return render(request, "choreography/music_list.html", context)


# endregion
