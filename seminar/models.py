from datetime import date, time

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from academy.models import Academy, Dancer, MaxFileSizeValidator
from choreography.models import PaymentMethodChoices
from event.models import Event


class PriceTypeChoices(models.IntegerChoices):
    SPECIAL = 1, _("Special")
    NORMAL = 2, _("Normal")


def teacher_picture_path(instance, filename):
    """Given an image file and its name, return the location and a formatted file name."""
    ext = filename.split(".")[-1]
    teacher_name_lowered = instance.teacher.strip().lower()
    teacher_name_snaked = teacher_name_lowered.replace(" ", "_")
    return f"seminar/{teacher_name_snaked}.{ext}"


class SeminarPrice(models.Model):
    """
    Store a single SeminarPrice instance, related to :model:`seminar.Seminar`.
    """

    type = models.PositiveSmallIntegerField(
        verbose_name=_("price type"), choices=PriceTypeChoices.choices
    )
    one_registration_price = models.PositiveSmallIntegerField(
        verbose_name=_("one registration price")
    )
    two_registrations_price = models.PositiveSmallIntegerField(
        verbose_name=_("two registrations price")
    )
    more_registrations_price = models.PositiveSmallIntegerField(
        verbose_name=_("more registrations price")
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("seminar price")
        verbose_name_plural = _("seminar prices")
        ordering = ["type"]

    def __str__(self):
        return f"{self.get_type_display()}: {self.one_registration_price} | {self.two_registrations_price} | {self.more_registrations_price}"


class Seminar(models.Model):
    """
    Store a single Seminar instance, related to :model:`event.Event`,
    :model:`seminar.SeminarRegistration`, :model:`seminar.SeminarPrice`
    and :model:`seminar.SeminarPayment`.
    """

    event = models.ForeignKey(
        Event,
        models.RESTRICT,
        related_name="seminaries",
        verbose_name=_("event"),
    )
    teacher = models.CharField(verbose_name=_("teacher"), max_length=200)
    quota = models.PositiveBigIntegerField(verbose_name=_("quota"), default=1)
    price = models.ForeignKey(
        SeminarPrice,
        models.RESTRICT,
        related_name="seminars",
        verbose_name=_("price"),
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
    date = models.DateField(verbose_name=_("date"), default=date.today)
    time = models.TimeField(
        verbose_name=_("time"),
        help_text=_("Time format must be hh:mm."),
        default=time(12),
    )
    teacher_picture = models.ImageField(
        verbose_name=_("teacher picture"),
        upload_to=teacher_picture_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    registration_end_date = models.DateField(verbose_name=_("registration end date"))
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("seminar")
        verbose_name_plural = _("seminars")
        ordering = ["teacher", "date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "teacher", "date", "time", "price"],
                name="seminar_uniqueness",
            ),
        ]

    def __str__(self):
        return f"{self.teacher} | {self.date}"

    @property
    def available_space(self):
        """Check how many places are left."""
        deposit_paid_registrations = 0
        for seminar_registration in self.seminar_registrations.all():
            deposit_paid_registrations += 1 if seminar_registration.deposit_paid else 0
        return self.quota - deposit_paid_registrations

    @property
    def is_full(self):
        """Check if the seminar quota is full."""
        deposit_paid_registrations = 0
        for seminar_registration in self.seminar_registrations.all():
            deposit_paid_registrations += 1 if seminar_registration.deposit_paid else 0
        return self.quota <= deposit_paid_registrations

    @property
    def registration_ended(self):
        """Check if registration for the event has ended."""
        return self.registration_end_date < timezone.now().date()


class SeminarRegistration(models.Model):
    """
    Store a single SeminarRegistration instance, related to :model:`academy.Academy`,
    :model:`academy.Dancer`, :model:`seminar.Seminar` and :model:`seminar.SeminarPayment`.
    """

    academy = models.ForeignKey(
        Academy,
        models.RESTRICT,
        related_name="seminar_registrations",
        verbose_name=_("academy"),
    )
    dancer = models.ForeignKey(
        Dancer,
        models.CASCADE,
        related_name="seminar_registrations",
        verbose_name=_("dancer"),
    )
    seminar = models.ForeignKey(
        Seminar,
        models.CASCADE,
        related_name="seminar_registrations",
        limit_choices_to={"registration_end_date__gte": timezone.now().date()},
        verbose_name=_("seminar"),
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("seminar registration")
        verbose_name_plural = _("seminar registrations")
        ordering = ["seminar"]
        constraints = [
            models.UniqueConstraint(
                fields=["seminar", "dancer"],
                name="seminar_registration_uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.seminar} | {self.dancer}"

    @property
    def deposit_paid(self):
        return self.deposit_amount <= self.paid_amount

    @property
    def fully_paid(self):
        return self.balance == 0

    @property
    def total_price(self):
        dancer = self.dancer
        registrations_amount = dancer.seminar_registrations.count()

        if dancer.choreographies.filter(event=self.seminar.event).exists():
            if registrations_amount == 1:
                return self.seminar.price.one_registration_price
            elif registrations_amount == 2:
                return self.seminar.price.two_registrations_price
            elif registrations_amount >= 3:
                return self.seminar.price.more_registrations_price
        else:
            if registrations_amount == 1:
                return self.seminar.price.one_registration_price
            elif registrations_amount == 2:
                return self.seminar.price.two_registrations_price
            elif registrations_amount >= 3:
                return self.seminar.price.more_registrations_price

    @property
    def deposit_amount(self):
        return self.total_price * (self.seminar.deposit_percentage / 100)

    @property
    def paid_amount(self):
        amount_paid = 0
        for payment in self.seminar_payments.all():
            if payment:
                amount_paid += payment.amount
        return amount_paid

    @property
    def balance(self):
        return self.total_price - self.paid_amount


class SeminarPayment(models.Model):
    """
    Store a single SeminarPayment instance, related to :model:`seminar.SeminarRegistration`.
    """

    seminar_registration = models.ForeignKey(
        SeminarRegistration,
        models.RESTRICT,
        related_name="seminar_payments",
        limit_choices_to={"seminar__registration_end_date__gte": timezone.now().date()},
        verbose_name=_("seminar registration"),
    )
    amount = models.FloatField(verbose_name=_("amount"), default=0)
    payment_method = models.PositiveSmallIntegerField(
        verbose_name=_("payment method"),
        choices=PaymentMethodChoices.choices,
        default=1,
    )
    date = models.DateField(verbose_name=_("date"), default=date.today)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("seminar payment")
        verbose_name_plural = _("seminar payments")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.seminar_registration} | ${self.amount}"
