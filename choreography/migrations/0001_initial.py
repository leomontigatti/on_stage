import datetime

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import academy.models
import choreography.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academy", "0001_initial"),
        ("event", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Choreography",
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
                ("name", models.CharField(max_length=60, verbose_name="name")),
                ("duration", models.DurationField(verbose_name="duration")),
                (
                    "is_locked",
                    models.BooleanField(default=False, verbose_name="is locked"),
                ),
                (
                    "is_disqualified",
                    models.BooleanField(default=False, verbose_name="is disqualified"),
                ),
                (
                    "show_awards",
                    models.BooleanField(default=False, verbose_name="show awards"),
                ),
                (
                    "order_number",
                    models.PositiveSmallIntegerField(
                        blank=True, null=True, verbose_name="order number"
                    ),
                ),
                (
                    "music_track",
                    models.FileField(
                        blank=True,
                        help_text="Allowed audio extensions: mp3, avi or wav up to 10 MB.",
                        null=True,
                        upload_to=choreography.models.track_path,
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["mp3", "avi", "wav"],
                                message="The selected file does not have a valid audio extension.",
                            ),
                            academy.models.MaxFileSizeValidator(10485760),
                        ],
                        verbose_name="music track",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "academy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="academy.academy",
                        verbose_name="academy",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="event.category",
                        verbose_name="category",
                    ),
                ),
                (
                    "dance_mode",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="event.dancemode",
                        verbose_name="dance mode",
                    ),
                ),
                (
                    "dancers",
                    models.ManyToManyField(
                        related_name="choreographies",
                        to="academy.dancer",
                        verbose_name="dancers",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
                (
                    "price",
                    models.ForeignKey(
                        help_text="Per dancer.",
                        limit_choices_to={
                            "event__end_date__gte": datetime.date(2024, 1, 16)
                        },
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="event.price",
                        verbose_name="price",
                    ),
                ),
                (
                    "professors",
                    models.ManyToManyField(
                        related_name="choreographies",
                        to="academy.professor",
                        verbose_name="professors",
                    ),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="choreographies",
                        to="event.schedule",
                        verbose_name="schedule",
                    ),
                ),
            ],
            options={
                "verbose_name": "choreography",
                "verbose_name_plural": "choreographies",
                "ordering": ["order_number"],
            },
        ),
        migrations.CreateModel(
            name="Award",
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
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        limit_choices_to={"groups__name__in": ["Judge", "Admin"]},
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="awards",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="assigned by",
                    ),
                ),
                (
                    "award_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="awards",
                        to="event.awardtype",
                        verbose_name="award type",
                    ),
                ),
                (
                    "choreography",
                    models.ForeignKey(
                        limit_choices_to={"is_disqualified": False},
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="awards",
                        to="choreography.choreography",
                        verbose_name="choreography",
                    ),
                ),
            ],
            options={
                "verbose_name": "award",
                "verbose_name_plural": "awards",
                "ordering": ["choreography__order_number"],
            },
        ),
        migrations.CreateModel(
            name="Discount",
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
                ("amount", models.FloatField(default=0, verbose_name="amount")),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "choreography",
                    models.ForeignKey(
                        limit_choices_to={
                            "event__end_date__gte": datetime.date(2024, 1, 16)
                        },
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="discounts",
                        to="choreography.choreography",
                        verbose_name="choreography",
                    ),
                ),
            ],
            options={
                "verbose_name": "discount",
                "verbose_name_plural": "discounts",
                "ordering": ["choreography"],
            },
        ),
        migrations.CreateModel(
            name="Payment",
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
                    "amount",
                    models.PositiveSmallIntegerField(default=0, verbose_name="amount"),
                ),
                (
                    "payment_method",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Cash"),
                            (2, "Wire"),
                            (3, "Deposit"),
                            (4, "Credit card"),
                            (5, "Other"),
                        ],
                        default=1,
                        verbose_name="Payment method",
                    ),
                ),
                (
                    "date",
                    models.DateField(default=datetime.date.today, verbose_name="date"),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "choreography",
                    models.ForeignKey(
                        limit_choices_to={
                            "event__end_date__gte": datetime.date(2024, 1, 16)
                        },
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="payments",
                        to="choreography.choreography",
                        verbose_name="choreography",
                    ),
                ),
            ],
            options={
                "verbose_name": "payment",
                "verbose_name_plural": "payments",
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="Score",
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
                    "value",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MaxValueValidator(
                                limit_value=100,
                                message="The value cannot be higher than 100.",
                            )
                        ],
                        verbose_name="value",
                    ),
                ),
                (
                    "is_locked",
                    models.BooleanField(default=False, verbose_name="is locked"),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "choreography",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="scores",
                        to="choreography.choreography",
                        verbose_name="choreography",
                    ),
                ),
                (
                    "judge",
                    models.ForeignKey(
                        limit_choices_to={"groups__name": "Judge"},
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="scores",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="judge",
                    ),
                ),
            ],
            options={
                "verbose_name": "score",
                "verbose_name_plural": "scores",
                "ordering": ["choreography__order_number"],
            },
        ),
        migrations.CreateModel(
            name="Feedback",
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
                    "audio_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=choreography.models.feedback_path,
                        verbose_name="audio file",
                    ),
                ),
                (
                    "score",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="choreography.score",
                        verbose_name="score",
                    ),
                ),
            ],
            options={
                "verbose_name": "feedback",
                "verbose_name_plural": "feedbacks",
                "ordering": ["score__choreography__order_number"],
            },
        ),
        migrations.AddConstraint(
            model_name="award",
            constraint=models.UniqueConstraint(
                fields=("choreography", "assigned_by", "award_type"),
                name="default_award_uniqueness",
            ),
        ),
    ]
