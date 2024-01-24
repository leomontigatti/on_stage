import os
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pydub import AudioSegment

from academy.models import Academy, Dancer, MaxFileSizeValidator, Professor
from event.models import AwardType, Category, DanceMode, Event, Price, Schedule

OSUser = get_user_model()


class PaymentMethodChoices(models.IntegerChoices):
    CASH = 1, _("Cash")
    WIRE = 2, _("Wire")
    DEPOSIT = 3, _("Deposit")
    CREDIT_CARD = 4, _("Credit card")
    OTHER = 5, _("Other")


def track_path(instance, filename):
    """Given a music file and its name, return the location and a formatted file name."""
    ext = filename.split(".")[-1]
    academy_name_snaked = instance.academy.name.replace(" ", "_")
    choreography_name_lowered = instance.name.lower().strip().replace('"', "")
    choreography_name_snaked = choreography_name_lowered.replace(" ", "_")
    if instance.order_number:
        return f"{academy_name_snaked}/music_track/{instance.order_number:05d}_{choreography_name_snaked}.{ext}"
    return f"{academy_name_snaked}/music_track/{choreography_name_snaked}.{ext}"


def feedback_path(instance, filename):
    """Given an audio file and its name, return the location and a formatted file name."""
    ext = filename.split(".")[-1]
    score = instance.score
    academy_name_snaked = score.choreography.academy.name.replace(" ", "_")
    choreography_name_lowered = score.choreography.name.strip().lower().replace('"', "")
    choreography_name_snaked = choreography_name_lowered.replace(" ", "_")
    judge_name = score.judge.__str__()
    return (
        f"{academy_name_snaked}/feedback/{choreography_name_snaked}/{judge_name}.{ext}"
    )


class Choreography(models.Model):
    """
    Store a single Choreography instance, related to :model:`event.Event`, :model:`event.DanceMode`,
    :model:`event.Category`, :model:`event.Price`, :model:`event.Schedule`, :model:`academy.Academy`,
    :model:`academy.Dancer`, :model:`academy.Professor`, :model:`academy.Award`, :model:`academy.Score`,
    :model:`academy.Payment` and :model:`choreography.Discount`.
    """

    academy = models.ForeignKey(
        Academy,
        models.RESTRICT,
        related_name="choreographies",
        verbose_name=_("academy"),
    )
    event = models.ForeignKey(
        Event,
        models.RESTRICT,
        related_name="choreographies",
        verbose_name=_("event"),
    )
    dance_mode = models.ForeignKey(
        DanceMode,
        models.RESTRICT,
        related_name="choreographies",
        verbose_name=_("dance mode"),
    )
    category = models.ForeignKey(
        Category,
        models.RESTRICT,
        related_name="choreographies",
        verbose_name=_("category"),
    )
    price = models.ForeignKey(
        Price,
        models.RESTRICT,
        related_name="choreographies",
        limit_choices_to={"event__end_date__gte": timezone.now().date()},
        verbose_name=_("price"),
        help_text=_("Per dancer."),
    )
    schedule = models.ForeignKey(
        Schedule,
        models.RESTRICT,
        related_name="choreographies",
        verbose_name=_("schedule"),
    )
    dancers = models.ManyToManyField(
        Dancer, related_name="choreographies", verbose_name=_("dancers")
    )
    professors = models.ManyToManyField(
        Professor,
        related_name="choreographies",
        verbose_name=_("professors"),
    )
    _name = None
    name = models.CharField(verbose_name=_("name"), max_length=60)
    duration = models.DurationField(verbose_name=_("duration"))
    is_locked = models.BooleanField(verbose_name=_("is locked"), default=False)
    is_disqualified = models.BooleanField(
        verbose_name=_("is disqualified"), default=False
    )
    show_awards = models.BooleanField(verbose_name=_("show awards"), default=False)
    _order_number = None
    order_number = models.PositiveSmallIntegerField(
        verbose_name=_("order number"), blank=True, null=True
    )
    _music_track = None
    music_track = models.FileField(
        verbose_name=_("music track"),
        upload_to=track_path,
        blank=True,
        null=True,
        help_text=_("Allowed audio extensions: mp3, avi or wav up to 10 MB."),
        validators=[
            FileExtensionValidator(
                allowed_extensions=["mp3", "avi", "wav"],
                message=_("The selected file does not have a valid audio extension."),
            ),
            MaxFileSizeValidator(10485760),
        ],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = self.name
        self._order_number = self.order_number
        self._music_track = self.music_track

    class Meta:
        verbose_name = _("choreography")
        verbose_name_plural = _("choreographies")
        ordering = ["order_number"]

    def __str__(self):
        return f"{self.academy} | {self.name}"

    def save(self, *args, **kwargs):
        # Change music track path and name if instance name or order number changed.
        if self.music_track:
            if any(
                [
                    self.name != self._name,
                    self.order_number != self._order_number,
                ]
            ):
                self.rename_music_track()

            # Change duration if music track changed.
            if self.music_track != self._music_track:
                audio = AudioSegment.from_file(self.music_track)
                duration_in_seconds = len(audio) / 1000
                self.duration = timedelta(seconds=duration_in_seconds)
        else:
            self.duration = self.category.max_duration

        super().save(*args, **kwargs)
        self._name = self.name
        self._order_number = self.order_number
        self._music_track = self.music_track

    def get_absolute_url(self):
        """Get a string that can be used to refer to the instance detail view."""
        return reverse("choreography_detail", kwargs={"choreography_pk": self.pk})

    def get_update_url(self):
        """Get a string that can be used to refer to the instance update view."""
        return reverse("choreography_update", kwargs={"choreography_pk": self.pk})

    def get_award_url(self):
        """Get a string that can be used to refer to the instance's award detail view."""
        return reverse("award_detail", kwargs={"choreography_pk": self.pk})

    @property
    def deposit_paid(self):
        return self.deposit_amount <= self.paid_amount

    @property
    def fully_paid(self):
        return self.balance == 0

    @property
    def music_track_name(self):
        return self.music_track.name.split("/")[-1]

    @property
    def discount_amount(self):
        """Get all related Discount instances amount."""
        total = 0
        if self.discounts.exists():
            for discount in self.discounts.all():
                total += discount.amount
        return total

    @property
    def total_price(self):
        return self.price.amount * self.dancers.count() - self.discount_amount

    @property
    def total_price_without_discounts(self):
        return self.price.amount * self.dancers.count()

    @property
    def deposit_amount(self):
        return self.total_price * (self.event.deposit_percentage / 100)

    @property
    def paid_amount(self):
        """Get all related Payment instances amount."""
        amount_paid = 0
        for payment in self.payments.all():
            if payment:
                amount_paid += payment.amount
        return amount_paid

    @property
    def balance(self):
        return self.total_price - self.paid_amount

    @property
    def balance_without_discounts(self):
        return self.total_price_without_discounts - self.paid_amount

    @property
    def average_score(self):
        scores_not_none, scores_total = 0, 0
        for score in self.scores.all():
            if score.value is not None:
                scores_total += score.value
                scores_not_none += 1
        if scores_not_none != 0:
            return round(scores_total / scores_not_none, 2)
        return scores_total

    def rename_music_track(self):
        """Rename the audio file if music track and order number exist."""
        ext = self.music_track.name.split(".")[-1]
        academy_name_snaked = self.academy.name.replace(" ", "_")
        choreography_name_lowered = self.name.lower().strip().replace('"', "")
        choreography_name_snaked = choreography_name_lowered.replace(" ", "_")
        if self.order_number:
            new_name = f"{academy_name_snaked}/music_track/{self.order_number:05d}_{choreography_name_snaked}.{ext}"
        else:
            new_name = (
                f"{academy_name_snaked}/music_track/{choreography_name_snaked}.{ext}"
            )
        self.music_track = new_name

        path = f"{settings.MEDIA_ROOT}/{academy_name_snaked}/music_track/"
        # Check if the choreography name matches the stashed music track and rename.
        _music_track = self._music_track.name.split("/")[-1]
        for root, dirs, files in os.walk(path):
            if _music_track in files:
                os.rename(self._music_track.path, f"{settings.MEDIA_ROOT}/{new_name}")


class Award(models.Model):
    """
    Store a single Award instance, related to :model:`event.AwardType`,
    :model:`choreography.Choreography` and :model:`academy.OSUser`.
    """

    choreography = models.ForeignKey(
        Choreography,
        models.RESTRICT,
        related_name="awards",
        limit_choices_to={"is_disqualified": False},
        verbose_name=_("choreography"),
    )
    assigned_by = models.ForeignKey(
        OSUser,
        models.RESTRICT,
        related_name="awards",
        limit_choices_to={"groups__name__in": ["Judge", "Admin"]},
        verbose_name=_("assigned by"),
    )
    award_type = models.ForeignKey(
        AwardType,
        models.RESTRICT,
        related_name="awards",
        verbose_name=_("award type"),
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("award")
        verbose_name_plural = _("awards")
        ordering = ["choreography__order_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["choreography", "assigned_by", "award_type"],
                name="default_award_uniqueness",
            )
        ]

    def __str__(self):
        return self.award_type.__str__()


class Discount(models.Model):
    """
    Store a single Discount instance, related to :model:`choreography.Choreography`.
    """

    choreography = models.ForeignKey(
        Choreography,
        models.RESTRICT,
        related_name="discounts",
        limit_choices_to={"event__end_date__gte": timezone.now().date()},
        verbose_name=_("choreography"),
    )
    amount = models.FloatField(verbose_name=_("amount"), default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("discount")
        verbose_name_plural = _("discounts")
        ordering = ["choreography"]

    def __str__(self):
        return f"{self.choreography} | ${self.amount}"


class Payment(models.Model):
    """
    Store a single Payment instance, related to :model:`choreography.Choreography`.
    """

    choreography = models.ForeignKey(
        Choreography,
        models.RESTRICT,
        related_name="payments",
        limit_choices_to={"event__end_date__gte": timezone.now().date()},
        verbose_name=_("choreography"),
    )
    amount = models.PositiveSmallIntegerField(verbose_name=_("amount"), default=0)
    payment_method = models.PositiveSmallIntegerField(
        verbose_name=_("Payment method"),
        choices=PaymentMethodChoices.choices,
        default=1,
    )
    date = models.DateField(verbose_name=_("date"), default=date.today)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.choreography} | ${self.amount}"


class Score(models.Model):
    """
    Store a single Score instance, related to :model:`academy.User` and
    :model:`choreography.Choreography`.
    """

    choreography = models.ForeignKey(
        Choreography,
        models.RESTRICT,
        related_name="scores",
        verbose_name=_("choreography"),
    )
    judge = models.ForeignKey(
        OSUser,
        models.RESTRICT,
        related_name="scores",
        limit_choices_to={"groups__name": "Judge"},
        verbose_name=_("judge"),
    )
    value = models.PositiveSmallIntegerField(
        verbose_name=_("value"),
        blank=True,
        null=True,
        validators=[
            MaxValueValidator(
                limit_value=100, message=_("The value cannot be higher than 100.")
            )
        ],
    )
    is_locked = models.BooleanField(verbose_name=_("is locked"), default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("score")
        verbose_name_plural = _("scores")
        ordering = ["choreography__order_number"]

    def __str__(self):
        return f"{self.choreography} | {self.value}"


class Feedback(models.Model):
    """
    Store a single Feedback instance, related to :model:`choreography.Score`.
    """

    score = models.OneToOneField(
        Score,
        models.CASCADE,
        verbose_name=_("score"),
    )
    audio_file = models.FileField(
        verbose_name=_("audio file"),
        upload_to=feedback_path,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("feedback")
        verbose_name_plural = _("feedbacks")
        ordering = ["score__choreography__order_number"]

    def __str__(self):
        return f"{self.score.choreography} | {self.score.judge}"
