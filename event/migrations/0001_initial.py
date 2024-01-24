import datetime

import colorfield.fields
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import academy.models
import event.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Contact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(max_length=100, verbose_name="first name"),
                ),
                (
                    "last_name",
                    models.CharField(max_length=100, verbose_name="last name"),
                ),
                ("email", models.EmailField(max_length=250, verbose_name="email")),
                (
                    "phone_number",
                    models.CharField(
                        max_length=10,
                        validators=[
                            django.core.validators.MinLengthValidator(10),
                            academy.models.numeric_string_validator,
                        ],
                        verbose_name="phone number",
                    ),
                ),
                (
                    "bank_name",
                    models.CharField(max_length=200, verbose_name="bank name"),
                ),
                (
                    "account_owner",
                    models.CharField(max_length=200, verbose_name="account owner"),
                ),
                (
                    "account_owner_id_number",
                    models.CharField(
                        max_length=13, verbose_name="account owner ID number"
                    ),
                ),
                (
                    "account_type",
                    models.CharField(
                        choices=[("SAVINGS", "Savings"), ("CHECKING", "Checking")],
                        max_length=100,
                        verbose_name="account type",
                    ),
                ),
                (
                    "routing_number",
                    models.CharField(
                        max_length=22,
                        validators=[
                            django.core.validators.MinLengthValidator(22),
                            academy.models.numeric_string_validator,
                        ],
                        verbose_name="routing number",
                    ),
                ),
                ("alias", models.CharField(max_length=20, verbose_name="alias")),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=60, verbose_name="event name")),
                ("start_date", models.DateField(verbose_name="start date")),
                ("end_date", models.DateField(verbose_name="end date")),
                (
                    "registration_end_date",
                    models.DateField(verbose_name="registration end date"),
                ),
                ("city", models.CharField(max_length=100, verbose_name="city")),
                ("state", models.CharField(max_length=100, verbose_name="state")),
                ("country", models.CharField(max_length=100, verbose_name="country")),
                (
                    "logo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=event.models.event_logo_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="event logo",
                    ),
                ),
                (
                    "deposit_percentage",
                    models.PositiveSmallIntegerField(
                        default=50,
                        validators=[
                            django.core.validators.MaxValueValidator(
                                limit_value=100,
                                message="The value cannot be higher than 100.",
                            )
                        ],
                        verbose_name="deposit percentage",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="event.contact",
                        verbose_name="contact",
                    ),
                ),
                (
                    "judge",
                    models.ManyToManyField(
                        blank=True,
                        limit_choices_to={"groups__name": "Judge"},
                        related_name="events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="judge",
                    ),
                ),
            ],
            options={
                "verbose_name": "event",
                "verbose_name_plural": "events",
                "ordering": ["end_date"],
            },
        ),
        migrations.CreateModel(
            name="DanceMode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=60, verbose_name="dance mode")),
                (
                    "sub_mode",
                    models.CharField(
                        blank=True, max_length=60, null=True, verbose_name="sub mode"
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ManyToManyField(
                        related_name="dance_modes",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
            ],
            options={
                "verbose_name": "dance mode",
                "verbose_name_plural": "dance modes",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=60, verbose_name="category name")),
                (
                    "type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Solo"), (2, "Duo"), (3, "Trio"), (4, "Group")],
                        verbose_name="category type",
                    ),
                ),
                (
                    "min_age",
                    models.PositiveSmallIntegerField(verbose_name="minimum age"),
                ),
                (
                    "max_age",
                    models.PositiveSmallIntegerField(verbose_name="maximum age"),
                ),
                (
                    "max_duration",
                    models.DurationField(
                        help_text="Max duration format must be mm:ss.",
                        verbose_name="max duration",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ManyToManyField(
                        related_name="categories",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
                "ordering": ["max_age", "name", "type"],
            },
        ),
        migrations.CreateModel(
            name="AwardType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="award name"
                    ),
                ),
                (
                    "is_special",
                    models.BooleanField(default=False, verbose_name="is special"),
                ),
                (
                    "color",
                    colorfield.fields.ColorField(
                        default="#000000", image_field=None, max_length=25, samples=None
                    ),
                ),
                (
                    "min_average_score",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Leave blank if it's a special award.",
                        null=True,
                        validators=[
                            django.core.validators.MaxValueValidator(
                                limit_value=100,
                                message="The value cannot be higher than 100.",
                            )
                        ],
                        verbose_name="minimum average score",
                    ),
                ),
                (
                    "max_average_score",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Leave blank if it's a special award.",
                        null=True,
                        validators=[
                            django.core.validators.MaxValueValidator(
                                limit_value=100,
                                message="The value cannot be higher than 100.",
                            )
                        ],
                        verbose_name="maximum average score",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ManyToManyField(
                        related_name="award_types",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
            ],
            options={
                "verbose_name": "award type",
                "verbose_name_plural": "award types",
                "ordering": ["min_average_score", "max_average_score"],
            },
        ),
        migrations.CreateModel(
            name="Price",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="name")),
                (
                    "category_type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Solo"), (2, "Duo"), (3, "Trio"), (4, "Group")],
                        verbose_name="category type",
                    ),
                ),
                (
                    "amount",
                    models.FloatField(
                        default=0.0, help_text="Per dancer.", verbose_name="amount"
                    ),
                ),
                ("due_date", models.DateField(verbose_name="due date")),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="prices",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
            ],
            options={
                "verbose_name": "price",
                "verbose_name_plural": "prices",
                "ordering": ["event", "category_type", "due_date"],
            },
        ),
        migrations.CreateModel(
            name="Schedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date",
                    models.DateField(default=datetime.date.today, verbose_name="date"),
                ),
                (
                    "time",
                    models.TimeField(
                        default=datetime.time(12, 0),
                        help_text="Time format must be hh:mm.",
                        verbose_name="time",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "dance_mode",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="schedules",
                        to="event.dancemode",
                        verbose_name="dance mode",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="schedules",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
            ],
            options={
                "verbose_name": "schedule",
                "verbose_name_plural": "schedules",
                "ordering": ["date", "time"],
            },
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                fields=("name", "start_date", "end_date"), name="event_uniqueness"
            ),
        ),
        migrations.AddConstraint(
            model_name="awardtype",
            constraint=models.UniqueConstraint(
                fields=("name", "min_average_score", "max_average_score"),
                name="award_type_uniqueness",
            ),
        ),
    ]
