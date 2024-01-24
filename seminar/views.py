from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from academy.views import has_academy, is_owner
from event.models import Event
from seminar.forms import SeminarRegistrationFormSet
from seminar.models import Seminar, SeminarRegistration

# region SeminarRegistration


@login_required
@user_passes_test(has_academy)
def seminar_registration_list_view(request, event_pk):
    """
    Display a list of available Seminar instances and a GET method select form to filter
    by event.

    **Context:**

    ``model``
        The SeminarRegistration model class.
    ``event``
        The selected Event instance.
    ``seminar_list``
        A Seminar queryset.

    **Template:**

    :template:`seminar/seminar_list.html`
    """

    event = get_object_or_404(Event, pk=event_pk)

    queryset = Seminar.objects.filter(event=event)

    context = {
        "model": SeminarRegistration,
        "event": event,
        "seminar_list": queryset,
        "title": _("Seminar list"),
    }
    return render(request, "seminar/seminar_list.html", context)


@login_required
@user_passes_test(has_academy)
def seminar_registration_create_view(request, seminar_pk):
    """
    Display the selected Seminar instance information and a formset to add new SeminarRegistration instances.

    **Context:**

    ``model``
        The SeminarRegistration class.
    ``seminar``
        The selected Seminar instance.
    ``formset``
        A SeminarRegistrationFormSet instance.

    **Template:**

    :template:`seminar/seminar_registration_form.html`
    """

    seminar = get_object_or_404(Seminar, pk=seminar_pk)

    queryset = SeminarRegistration.objects.filter(
        academy=request.user.academy, seminar=seminar
    )

    formset = SeminarRegistrationFormSet(
        request.POST or None,
        prefix="seminar_registration",
        queryset=queryset,
        form_kwargs={"academy": request.user.academy},
    )

    context = {
        "model": SeminarRegistration,
        "seminar": seminar,
        "formset": formset,
        "event": seminar.event,
        "title": _("Seminar registrations"),
    }

    if all([request.method == "POST", formset.is_valid()]):
        if any([seminar.registration_ended, seminar.is_full]):
            messages.warning(
                request,
                _(
                    "Registration for the selected seminar has ended or seminar is full."
                ),
            )
            return redirect("seminarregistration_list", event_pk=seminar.event.pk)

        for form in formset:
            form.instance.academy = request.user.academy
            form.instance.seminar = seminar

            try:
                registration = form.save(commit=False)
                registration.save(update_fields=["academy", "seminar", "dancer"])
            except ValueError:
                try:
                    form.save()
                except IntegrityError:
                    messages.warning(
                        request,
                        _("You must select at least one dancer."),
                    )
                    return redirect("seminarregistration_create", seminar.pk)

        messages.success(
            request, _("Successfully added a new registration for the seminar!")
        )
        return redirect("seminarregistration_list", event_pk=seminar.event.pk)

    return render(request, "seminar/seminar_registration_form.html", context)


@login_required
@user_passes_test(has_academy)
def seminar_registration_delete_view(request, seminar_registration_pk):
    seminar_registration = get_object_or_404(
        SeminarRegistration, pk=seminar_registration_pk
    )

    if not is_owner(request, seminar_registration):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    if seminar_registration.seminar_payments.exists():
        messages.warning(
            request,
            _(
                "The registration could not be deleted because it has at least one related payment. Please contact us."
            ),
        )
        return redirect(
            "seminarregistration_create", seminar_pk=seminar_registration.seminar.pk
        )

    seminar_registration.delete()
    messages.success(request, _("Successfully deleted a registration for the seminar!"))
    return redirect(
        "seminarregistration_create", seminar_pk=seminar_registration.seminar.pk
    )


# endregion
