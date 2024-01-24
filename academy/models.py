from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


class IdentificationTypeChoices(models.TextChoices):
    ID = "ID", _("ID")
    PASSPORT = "PASSPORT", _("Passport")


def numeric_string_validator(value):
    """Validate the given string has numeric characters only."""
    if not value.isnumeric():
        raise ValidationError(_("Only numeric characters are allowed."))


@deconstructible
class MaxFileSizeValidator(object):
    def __init__(self, max_size):
        self.max_size = max_size

    def __call__(self, file):
        """Validate the given File instance size is not over the max_size set in bytes."""
        if file.size > self.max_size:
            raise ValidationError(
                _("The file you are trying to upload is over %(max_size)s MB.")
                % {"max_size": self.max_size / 1024 / 1024}
            )


def id_front_picture_path(instance, filename):
    """Given an image file and its name, return the location and a formatted file name."""
    ext = filename.split(".")[-1]
    academy_name_snaked = instance.academy.name.replace(" ", "_")
    instance_model_name = instance._meta.model.__name__
    return f"{academy_name_snaked}/{instance_model_name}/{instance.identification_number}_front.{ext}"


def id_back_picture_path(instance, filename):
    """Given an image file and its name, return the location and a formatted file name."""
    ext = filename.split(".")[-1]
    academy_name_snaked = instance.academy.name.replace(" ", "_")
    instance_model_name = instance._meta.model.__name__
    return f"{academy_name_snaked}/{instance_model_name}/{instance.identification_number}_back.{ext}"


class OSUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class OSUser(AbstractUser):
    username = None
    email = models.EmailField(verbose_name=_("email address"), unique=True)

    objects = OSUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        if all([self.first_name, self.last_name]):
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email


class Academy(models.Model):
    """
    Store a single Academy instance, related to :model:`academy.OSUser`, :model:`academy.Professor`,
    :model:`academy.Dancer`, :model:`choreography.Choreography` and :model:`seminar.SeminarRegistration`.
    """

    user = models.OneToOneField(
        OSUser,
        models.RESTRICT,
        limit_choices_to={"is_staff": False},
        verbose_name=_("user"),
    )
    name = models.CharField(verbose_name=_("name"), max_length=50, unique=True)
    phone_number = models.CharField(
        verbose_name=_("phone number"),
        max_length=10,
        validators=[MinLengthValidator(10), numeric_string_validator],
    )
    city = models.CharField(verbose_name=_("city"), max_length=100)
    state = models.CharField(verbose_name=_("state"), max_length=100)
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("academy")
        verbose_name_plural = _("academies")
        ordering = ["name"]

    def __str__(self):
        return self.name.title()

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super().save(*args, **kwargs)


class Dancer(models.Model):
    """
    Store a single Dancer instance, related to :model:`academy.Academy`, :model:`choreography.Choreography`,
    and :model:`seminar.SeminarRegistration`.
    """

    academy = models.ForeignKey(
        Academy,
        models.RESTRICT,
        related_name="dancers",
        verbose_name=_("academy"),
    )
    first_name = models.CharField(verbose_name=_("first name"), max_length=100)
    last_name = models.CharField(verbose_name=_("last name"), max_length=100)
    birth_date = models.DateField(verbose_name=_("birth date"))
    is_verified = models.BooleanField(verbose_name=_("is verified"), default=False)
    identification_type = models.CharField(
        verbose_name=_("identification type"),
        max_length=50,
        default=IdentificationTypeChoices.ID,
        choices=IdentificationTypeChoices.choices,
    )
    identification_number = models.CharField(
        verbose_name=_("identification number"), max_length=20
    )
    identification_front_image = models.ImageField(
        verbose_name=_("identification front image"),
        upload_to=id_front_picture_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    identification_back_image = models.ImageField(
        verbose_name=_("identification back image"),
        upload_to=id_back_picture_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("dancer")
        verbose_name_plural = _("dancers")
        ordering = ["last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academy", "identification_type", "identification_number"],
                name="dancer_uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def save(self, *args, **kwargs):
        """Title the dancer's first and last name before saving."""
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get a string that can be used to refer to the instance detail view."""
        return reverse("dancer_detail", kwargs={"dancer_pk": self.pk})

    def get_update_url(self):
        """Get a string that can be used to refer to the instance update view."""
        return reverse("dancer_update", kwargs={"dancer_pk": self.pk})

    @property
    def age(self):
        """Calculate a dancer's age."""
        today = timezone.now().date()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def id_front_image_name(self):
        return self.identification_front_image.name.split("/")[-1]

    @property
    def id_back_image_name(self):
        return self.identification_back_image.name.split("/")[-1]


class Professor(models.Model):
    """
    Store a single Professor instance, related to :model:`academy.Academy` and
    :model:`choreography.Choreography`.
    """

    academy = models.ForeignKey(
        Academy,
        models.RESTRICT,
        related_name="professors",
        verbose_name=_("academy"),
    )
    first_name = models.CharField(verbose_name=_("first name"), max_length=100)
    last_name = models.CharField(verbose_name=_("last name"), max_length=100)
    identification_type = models.CharField(
        verbose_name=_("identification type"),
        max_length=50,
        default=IdentificationTypeChoices.ID,
        choices=IdentificationTypeChoices.choices,
    )
    identification_number = models.CharField(
        verbose_name=_("identification number"), max_length=20
    )
    identification_front_image = models.ImageField(
        verbose_name=_("identification front image"),
        upload_to=id_front_picture_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    identification_back_image = models.ImageField(
        verbose_name=_("identification back image"),
        upload_to=id_back_picture_path,
        null=True,
        blank=True,
        validators=[MaxFileSizeValidator(10485760)],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    change_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("professor")
        verbose_name_plural = _("professors")
        ordering = ["last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academy", "identification_type", "identification_number"],
                name="professor_uniqueness",
            )
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def save(self, *args, **kwargs):
        """Title the professor's first and last name before saving."""
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get a string that can be used to refer to the instance detail view."""
        return reverse("professor_detail", kwargs={"professor_pk": self.pk})

    def get_update_url(self):
        """Get a string that can be used to refer to the instance update view."""
        return reverse("professor_update", kwargs={"professor_pk": self.pk})

    @property
    def id_front_image_name(self):
        return self.identification_front_image.name.split("/")[-1]

    @property
    def id_back_image_name(self):
        return self.identification_back_image.name.split("/")[-1]
