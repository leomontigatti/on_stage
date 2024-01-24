from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext as _

from academy.forms import DancerForm, OSUserRegistrationForm, ProfessorForm
from academy.models import Academy, Dancer, Professor
from choreography.tasks import send_confirmation_email_task
from event.models import Contact, Event

OSUser = get_user_model()


def has_academy(user):
    # Check if a user has a related academy.
    return hasattr(user, "academy")


def is_admin(user):
    # Check if a user belongs to the 'Admin' permissions group.
    return user.groups.filter(name="Admin").exists()


def is_judge(user):
    # Check if a user belongs to the 'Judge' permissions group.
    return user.groups.filter(name="Judge").exists()


def is_soundman(user):
    # Check if a user belongs to the 'Soundman' permissions group.
    return user.groups.filter(name="Soundman").exists()


def is_owner(request, obj):
    # Check if the object belongs to the logged user.
    return request.user.academy == obj.academy


@login_required
def home(request):
    """
    Redirect the logged-in user.

    **Context:**

    ``model``
        A string for setting the active tab in the navbar HTML element.

    **Template:**

    :template:`home.html`
    """

    if is_admin(request.user) or request.user.is_superuser:
        return redirect("admin:index")
    elif is_judge(request.user):
        return redirect("event_list", sender="score")
    elif is_soundman(request.user):
        return redirect("event_list", sender="music")
    elif has_academy(request.user):
        return render(request, "home.html", {"model": "Home", "title": _("Home")})

    messages.error(
        request,
        _(
            "The logged user does not have a related academy. Try another one or contact us."
        ),
    )
    logout(request)
    return redirect("login")


def whatsapp_message(request, contact_pk):
    """
    Redirect the user to the Whatsapp API with a contact phone number.
    """

    contact = get_object_or_404(Contact, pk=contact_pk)
    phone_number = contact.phone_number
    return redirect(f"https://wa.me/54{phone_number}")


# region Dancer


@login_required
@user_passes_test(has_academy)
def dancer_list_view(request):
    """
    Display a list of Dancer instances related to the logged-in user's academy,
    a GET method searching form and a paginator that shows up to ten items per page.

    **Context:**

    ``model``
        The Dancer class.
    ``page_obj``
        A Page instance.
    ``search_input``
        A string with the user search parameters if any.
    ``search_text``
        A string to fill the HTML input element.

    **Template:**

    :template:`academy/dancer_list.html`
    """

    queryset = Dancer.objects.filter(academy=request.user.academy)

    search_input = request.GET.get("search_input", "")
    if search_input:
        queryset = queryset.filter(
            Q(identification_number__icontains=search_input)
            | Q(first_name__icontains=search_input)
            | Q(last_name__icontains=search_input)
        )

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Dancer,
        "page_obj": page_obj,
        "search_input": search_input,
        "search_text": _("Search by identification number, first or last name."),
        "title": _("Dancers list"),
    }
    return render(request, "academy/dancer_list.html", context)


@login_required
@user_passes_test(has_academy)
def dancer_create_view(request):
    """
    Display a form to create a new Dancer instance.

    **Context:**

    ``model``
        The Dancer class.
    ``form``
        A DancerForm instance.

    **Template:**

    :template:`academy/dancer_form.html`
    """

    form = DancerForm(request.POST or None, request.FILES or None)

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        try:
            form.save()
            messages.success(request, _("Successfully added a new dancer!"))
        except IntegrityError:
            messages.error(
                request,
                _("A dancer with that identification type and number already exists."),
            )
        return redirect("dancer_list")

    context = {"model": Dancer, "form": form, "title": _("Add dancer")}
    return render(request, "academy/dancer_form.html", context)


@login_required
@user_passes_test(has_academy)
def dancer_update_view(request, dancer_pk):
    """
    Display a form to update an existing Dancer instance.
    Redirect the user if the Dancer instance is not related or is verified.

    **Context:**

    ``model``
        The Dancer class.
    ``form``
        A DancerForm instance.
    ``object``
        A Dancer instance.

    **Template:**

    :template:`academy/dancer_form.html`
    """

    dancer = get_object_or_404(Dancer, pk=dancer_pk)
    if not is_owner(request, dancer) or dancer.is_verified:
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    form = DancerForm(request.POST or None, request.FILES or None, instance=dancer)

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        try:
            form.save()
            messages.success(request, _("Successfully updated the dancer information!"))
        except IntegrityError:
            messages.error(
                request,
                _("A dancer with that identification type and number already exists."),
            )
        return redirect("dancer_list")

    context = {
        "model": Dancer,
        "form": form,
        "object": dancer,
        "title": _("Update dancer"),
    }
    return render(request, "academy/dancer_form.html", context)


@login_required
@user_passes_test(has_academy)
def dancer_detail_view(request, dancer_pk):
    """
    Display a single Dancer instance.
    Redirect the user if the Dancer instance is not related.

    **Context:**

    ``model``
        The Dancer class.
    ``object``
        A Dancer instance.
    ``choreographies_qs``
        A queryset containing all Choreography instances the
        Dancer instance is related to.
    ``events_qs``
        A queryset containing all Event instances.
    ``selected_event``
        The selected Event instance fetched from GET request.

    **Template:**

    :template:`academy/dancer_detail.html`
    """

    dancer = get_object_or_404(Dancer, pk=dancer_pk)
    if not is_owner(request, dancer):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    choreographies_qs = dancer.choreographies.all()

    events_qs = Event.objects.all()
    selected_event = request.GET.get("event", "")
    if selected_event:
        event = get_object_or_404(Event, pk=selected_event)
        choreographies_qs = choreographies_qs.filter(event=event)

    context = {
        "model": Dancer,
        "object": dancer,
        "choreographies_qs": choreographies_qs,
        "events_qs": events_qs,
        "selected_event": selected_event,
        "title": _("Dancer detail"),
    }
    return render(request, "academy/dancer_detail.html", context)


# endregion
# region Professor


@login_required
@user_passes_test(has_academy)
def professor_list_view(request):
    """
    Display a list of Professor instances related to the logged-in user's academy,
    a GET method searching form and a paginator that shows up to ten items per page.

    **Context:**

    ``model``
        The professor class.
    ``page_obj``
        A Page instance.
    ``search_input``
        A string with the user search parameters if any.
    ``search_text``
        A string to fill the HTML input element.

    **Template:**

    :template:`academy/professor_list.html`
    """

    queryset = Professor.objects.filter(academy=request.user.academy)

    search_input = request.GET.get("search_input", "")
    if search_input:
        queryset = queryset.filter(
            Q(identification_number__icontains=search_input)
            | Q(first_name__icontains=search_input)
            | Q(last_name__icontains=search_input)
        )

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "model": Professor,
        "page_obj": page_obj,
        "search_input": search_input,
        "search_text": _("Search by identification number, first or last name."),
        "title": _("Professors list"),
    }
    return render(request, "academy/professor_list.html", context)


@login_required
@user_passes_test(has_academy)
def professor_create_view(request):
    """
    Display a form to create a new Professor instance.

    **Context:**

    ``model``
        The professor class.
    ``form``
        A ProfessorForm instance.

    **Template:**

    :template:`academy/professor_form.html`
    """

    form = ProfessorForm(request.POST or None, request.FILES or None)

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        try:
            form.save()
            messages.success(request, _("Successfully added a new professor!"))
        except IntegrityError:
            messages.error(
                request,
                _(
                    "A professor with that identification type and number already exists."
                ),
            )
        return redirect("professor_list")

    context = {"model": Professor, "form": form, "title": _("Add professor")}
    return render(request, "academy/professor_form.html", context)


@login_required
@user_passes_test(has_academy)
def professor_update_view(request, professor_pk):
    """
    Display a form to update an existing Professor instance.
    Redirect the user if the Professor instance is not related.

    **Context:**

    ``model``
        The professor class.
    ``form``
        A ProfessorForm instance.
    ``object``
        A Professor instance.

    **Template:**

    :template:`academy/professor_form.html`
    """

    professor = get_object_or_404(Professor, pk=professor_pk)
    if not is_owner(request, professor):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    form = ProfessorForm(
        request.POST or None, request.FILES or None, instance=professor
    )

    if all([request.method == "POST", form.is_valid()]):
        form.instance.academy = request.user.academy
        try:
            form.save()
        except IntegrityError:
            messages.error(
                request,
                _(
                    "A professor with that identification type and number already exists."
                ),
            )
        messages.success(request, _("Successfully updated the professor information!"))
        return redirect("professor_list")

    context = {
        "model": Professor,
        "form": form,
        "object": professor,
        "title": _("Update professor"),
    }
    return render(request, "academy/professor_form.html", context)


@login_required
@user_passes_test(has_academy)
def professor_detail_view(request, professor_pk):
    """
    Display a single Professor instance.
    Redirect the user if the Professor instance is not related.

    **Context:**

    ``model``
        The Professor class.
    ``object``
        A Professor instance.
    ``choreographies_qs``
        A queryset containing all Choreography instances the
        Professor instance is related to.
    ``events_qs``
        A queryset containing all Event instances.
    ``selected_event``
        The selected Event instance fetched from GET request.

    **Template:**

    :template:`academy/professor_detail.html`
    """

    professor = get_object_or_404(Professor, pk=professor_pk)
    if not is_owner(request, professor):
        messages.warning(
            request, _("You don't have permissions to perform this action.")
        )
        return redirect("home")

    choreographies_qs = professor.choreographies.all()

    events_qs = Event.objects.all()
    selected_event = request.GET.get("event", "")
    if selected_event:
        event = get_object_or_404(Event, pk=selected_event)
        choreographies_qs = choreographies_qs.filter(event=event)

    context = {
        "model": Professor,
        "object": professor,
        "choreographies_qs": choreographies_qs,
        "events_qs": events_qs,
        "selected_event": selected_event,
        "title": _("Professor detail"),
    }
    return render(request, "academy/professor_detail.html", context)


# endregion
# region Registration


token_generator = PasswordResetTokenGenerator()


def user_registration(request):
    """
    Display a form for creating a new OSUser instance.
    If the information is valid, create a new Academy instance related to the user and
    send an activation email to the given one.

    **Context:**

    ``model``
        A string for setting the active tab in the navbar HTML element.
    ``form``
        An OSUserRegistrationForm instance.
    ``email``
        A string with the created user email.

    **Template:**

    :template:`academy/registration/signup.html`
    """

    form = OSUserRegistrationForm(request.POST or None)

    if request.user.is_authenticated:
        return redirect("home")

    if all([request.method == "POST", form.is_valid()]):
        if not settings.DEBUG:
            form.instance.is_active = False
            user = form.save()

            Academy.objects.create(
                user=user,
                name=form.cleaned_data.get("academy_name"),
                phone_number=form.cleaned_data.get("phone_number"),
                city=form.cleaned_data.get("city").title(),
                state=form.cleaned_data.get("state").title(),
            )

            recipient = form.cleaned_data.get("email")
            # Get the domain of the current site.
            current_site = get_current_site(request)
            subject = "On Stage | " + _("Activation code")
            message = render_to_string(
                "registration/activation_mail_body.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": token_generator.make_token(user),
                },
            )
            send_confirmation_email_task(subject, message, None, [recipient], _("user"))
            return render(
                request, "registration/activation_mail_sent.html", {"email": recipient}
            )
        form.save()
        return render(
            request, "registration/activation_thanks.html", {"title": _("Sign up")}
        )

    context = {"model": "signup", "form": form, "title": _("Sign up")}
    return render(request, "registration/signup.html", context)


def terms(request):
    """
    Display a list of terms and conditions the user must agree in order to use
    the application.

    **Template:**

    :template:`academy/registration/terms.html`
    """

    return render(request, "registration/terms.html")


def activate(request, uidb64, token):
    """
    Try to activate the user instance depending on the parameters given.
    If successful, redirect the user to a 'thank you' template. Otherwise, redirect
    the user to an 'error occurred' template.

    **Template:**

    :template:`academy/registration/activation_thanks.html`
    :template:`academy/registration/activation_failed.html`
    """

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = OSUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, OSUser.DoesNotExist):
        user = None

    if user and token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(
            request, "registration/activation_thanks.html", {"title": _("Sign up")}
        )
    return render(
        request, "registration/activation_failed.html", {"title": _("Sign up")}
    )


# endregion
