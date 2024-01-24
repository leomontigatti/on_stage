from datetime import date, time

from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from academy.models import MaxFileSizeValidator, numeric_string_validator

OSUser = get_user_model()


class AccountTypeChoices(models.TextChoices):
    SAVINGS = "SAVINGS", _("Savings")
    CHECKING = "CHECKING", _("Checking")


class CategoryTypeChoices(models.IntegerChoices):
    SOLO = 1, _("Solo")
    DUO = 2, _("Duo")
    TRIO = 3, _("Trio")
    GROUP = 4, _("Group")


def event_logo_path(instance, filename):
    """Given an image file and its name, return the location and a formatted file name."""
    event_name_lowered = instance.__str__().strip().lower()
    event_name_snaked = event_name_lowered.replace(" ", "_")
    ext = filename.split(".")[-1]
    return f"event/{event_name_snaked}.{ext}"


class Contact(models.Model):
    """
    Store a single Contact instance related to :model:`event.Event`.
    """

    first_name = models.CharField(verbose_name=_("first name"), max_length=100)
    last_name = models.CharField(verbose_name=_("last name"), max_length=100)
    email = models.EmailField(verbose_name=_("email"), max_length=250)
    phone_number = models.CharField(
        verbose_name=_("phone number"),
        max_length=10,
        validators=[MinLengthValidator(10), numeric_string_validator],
    )
    bank_name = models.CharField(verbose_name=_("bank name"), max_length=200)
    account_owner = models.CharField(verbose_name=_("account owner"), max_length=200)
    account_owner_id_number = models.CharField(
        verbose_name=_("account owner ID number"), max_length=13
    )
    account_type = models.CharField(
        verbose_name=_("account type"),
        max_length=100,
        choices=AccountTypeChoices.choices,
    )
    routing_number = models.CharField(
        verbose_name=_("routing number"),
        max_length=22,
        validators=[MinLengthValidator(22), numeric_string_validator],
    )
    alias = models.CharField(verbose_name=_("alias"), max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Event(models.Model):
    """
    Store a single Event instance, related to :model:`event.Category`, :model:`event.DanceMode`,
    :model:`event.Price`, :model:`event.Schedule`, :model:`event.Contact`, :model:`seminar.Seminar`,
    :model:`choreography.Choreography` and :model:`academy.OSUser`.
    """

    name = models.CharField(verbose_name=_("event name"), max_length=60)
    start_date = models.DateField(verbose_name=_("start date"))
    end_date = models.DateField(verbose_name=_("end date"))
    registration_end_date = models.DateField(verbose_name=_("registration end date"))
    city = models.CharField(verbose_name=_("city"), max_length=100)
    state = models.CharField(verbose_name=_("state"), max_length=100)
    country = models.CharField(verbose_name=_("country"), max_length=100)
    contact = models.ForeignKey(Contact, models.PROTECT, verbose_name=_("contact"))
    logo = models.ImageField(
        verbose_name=_("event logo"),
        upload_to=event_logo_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    judge = models.ManyToManyField(
        OSUser,
        related_name="events",
        limit_choices_to={"groups__name": "Judge"},
        verbose_name="judge",
        blank=True,
    )
    deposit_percentage = models.PositiveSmallIntegerField(
        verbose_name=_("deposit percentage"),
        default=50,
        validators=[
            MaxValueValidator(
                limit_value=100, message=_("The value cannot be higher than 100.")
            )
        ],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["end_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "start_date", "end_date"],
                name="event_uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.start_date.year}"

    def clean(self):
        # Check the event end date is not before its start date.
        if self.start_date > self.end_date:
            raise ValidationError(
                {
                    "end_date": ValidationError(
                        _("The event's end date cannot be before its start date.")
                    ),
                }
            )

    @property
    def started(self):
        """Check if the event has started."""
        return self.start_date <= timezone.now().date()

    @property
    def ended(self):
        """Check if the event has ended."""
        return self.end_date < timezone.now().date()

    @property
    def registration_ended(self):
        """Check if registration for the event has ended."""
        return self.registration_end_date < timezone.now().date()


class Category(models.Model):
    """
    Store a single Category instance, related to :model:`event.Event`, :model:`event.Price`,
    and :model:`choreography.Choreography`.
    """

    event = models.ManyToManyField(
        Event,
        related_name="categories",
        verbose_name=_("event"),
    )
    name = models.CharField(verbose_name=_("category name"), max_length=60)
    type = models.PositiveSmallIntegerField(
        verbose_name=_("category type"), choices=CategoryTypeChoices.choices
    )
    min_age = models.PositiveSmallIntegerField(verbose_name=_("minimum age"))
    max_age = models.PositiveSmallIntegerField(verbose_name=_("maximum age"))
    max_duration = models.DurationField(
        verbose_name=_("max duration"),
        help_text=_("Max duration format must be mm:ss."),
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["max_age", "name", "type"]

    def __str__(self):
        return f"{self.name}, {self.get_type_display()}"

    def clean(self):
        # Check the category minimum age is not greater than the maximum age.
        if self.min_age > self.max_age:
            raise ValidationError(
                {
                    "min_age": ValidationError(
                        _(
                            "The category minimum age cannot be greater than the maximum."
                        )
                    ),
                }
            )


class DanceMode(models.Model):
    """
    Store a single DanceMode instance, related to :model:`event.Event`, :model:`event.Schedule`,
    and :model:`choreography.Choreography`.
    """

    event = models.ManyToManyField(
        Event,
        related_name="dance_modes",
        verbose_name=_("event"),
    )
    name = models.CharField(verbose_name=_("dance mode"), max_length=60)
    sub_mode = models.CharField(
        verbose_name=_("sub mode"), max_length=60, blank=True, null=True
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("dance mode")
        verbose_name_plural = _("dance modes")
        ordering = ["name"]

    def __str__(self):
        if self.sub_mode:
            return f"{self.name}, {self.sub_mode}"
        else:
            return f"{self.name}"


class Price(models.Model):
    """
    Store a single Price instance, related to :model:`event.Event` and :model:`choreography.Choreography`.
    """

    event = models.ForeignKey(
        Event,
        models.RESTRICT,
        related_name="prices",
        verbose_name=_("event"),
    )
    name = models.CharField(verbose_name=_("name"), max_length=50)
    category_type = models.PositiveSmallIntegerField(
        verbose_name=_("category type"), choices=CategoryTypeChoices.choices
    )
    amount = models.FloatField(
        verbose_name=_("amount"), default=0.0, help_text=_("Per dancer.")
    )
    due_date = models.DateField(verbose_name=_("due date"))
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("price")
        verbose_name_plural = _("prices")
        ordering = ["event", "category_type", "due_date"]

    def __str__(self):
        return f"{self.event} | {self.name} | $ {self.amount}"

    def clean(self):
        # Check the price due date is not before nor after the event dates.
        if self.due_date < self.event.start_date:
            raise ValidationError(
                {
                    "due_date": ValidationError(
                        _("The price due date cannot be before the event start date.")
                    ),
                }
            )
        elif self.event.end_date < self.due_date:
            raise ValidationError(
                {
                    "due_date": ValidationError(
                        _("The price due date cannot be after the event end date.")
                    ),
                }
            )


class Schedule(models.Model):
    """
    Store a single Schedule instance, related to :model:`event.Event`, :model:`event.DanceMode`,
    and :model:`choreography.Choreography`.
    """

    event = models.ForeignKey(
        Event,
        models.RESTRICT,
        related_name="schedules",
        verbose_name=_("event"),
    )
    dance_mode = models.ForeignKey(
        DanceMode,
        models.RESTRICT,
        related_name="schedules",
        verbose_name=_("dance mode"),
    )
    date = models.DateField(verbose_name=_("date"), default=date.today)
    time = models.TimeField(
        verbose_name=_("time"),
        help_text=_("Time format must be hh:mm."),
        default=time(12),
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("schedule")
        verbose_name_plural = _("schedules")
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.date} {self.time}hs. | {self.dance_mode}"

    def clean(self):
        # Check the schedule start date is not before nor after the event dates.
        if self.date < self.event.start_date:
            raise ValidationError(
                {
                    "date": ValidationError(
                        _("The schedule date cannot be before the event start date.")
                    ),
                }
            )
        elif self.event.end_date < self.date:
            raise ValidationError(
                {
                    "date": ValidationError(
                        _("The schedule date cannot be after the event end date.")
                    ),
                }
            )


class AwardType(models.Model):
    """
    Store a single AwardType instance, related to :model:`event.Event` and :model:`choreography.Award`.
    """

    event = models.ManyToManyField(
        Event,
        related_name="award_types",
        verbose_name=_("event"),
    )
    name = models.CharField(verbose_name=_("award name"), max_length=50, unique=True)
    is_special = models.BooleanField(verbose_name=_("is special"), default=False)
    color = ColorField(default="#000000")
    min_average_score = models.PositiveSmallIntegerField(
        verbose_name=_("minimum average score"),
        blank=True,
        null=True,
        help_text=_("Leave blank if it's a special award."),
        validators=[
            MaxValueValidator(
                limit_value=100, message=_("The value cannot be higher than 100.")
            )
        ],
    )
    max_average_score = models.PositiveSmallIntegerField(
        verbose_name=_("maximum average score"),
        blank=True,
        null=True,
        help_text=_("Leave blank if it's a special award."),
        validators=[
            MaxValueValidator(
                limit_value=100, message=_("The value cannot be higher than 100.")
            )
        ],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("award type")
        verbose_name_plural = _("award types")
        ordering = ["min_average_score", "max_average_score"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "min_average_score", "max_average_score"],
                name="award_type_uniqueness",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        # Check min and max average score are not None if award type is not special.
        default_award = AwardType.objects.filter(
            is_special=False, min_average_score=None, max_average_score=None
        )
        if all(
            [
                default_award.exists(),
                not self.is_special,
                not self.min_average_score,
                not self.max_average_score,
            ]
        ):
            raise ValidationError(
                {
                    "is_special": ValidationError(
                        _(
                            "There is already a default award set with no average scores: %(value)s."
                        ),
                        code="invalid",
                        params={"value": default_award.first()},
                    )
                }
            )

        # Check the min average score is not greater than the max.
        if all([self.min_average_score, self.max_average_score]):
            if self.min_average_score > self.max_average_score:
                raise ValidationError(
                    {
                        "min_average_score": ValidationError(
                            _(
                                "The minimum average score cannot be greater than the maximum."
                            )
                        ),
                    }
                )

    def save(self, *args, **kwargs):
        # Set min and max average scores to None if it's a special award.
        if all([self.is_special, self.min_average_score, self.max_average_score]):
            self.min_average_score, self.max_average_score = None, None
        super().save(*args, **kwargs)
