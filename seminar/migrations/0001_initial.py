import datetime

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import academy.models
import seminar.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academy", "0001_initial"),
        ("event", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeminarPrice",
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
                    "type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Special"), (2, "Normal")],
                        verbose_name="price type",
                    ),
                ),
                (
                    "one_registration_price",
                    models.PositiveSmallIntegerField(
                        verbose_name="one registration price"
                    ),
                ),
                (
                    "two_registrations_price",
                    models.PositiveSmallIntegerField(
                        verbose_name="two registrations price"
                    ),
                ),
                (
                    "more_registrations_price",
                    models.PositiveSmallIntegerField(
                        verbose_name="more registrations price"
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "seminar price",
                "verbose_name_plural": "seminar prices",
                "ordering": ["type"],
            },
        ),
        migrations.CreateModel(
            name="Seminar",
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
                ("teacher", models.CharField(max_length=200, verbose_name="teacher")),
                (
                    "quota",
                    models.PositiveBigIntegerField(default=1, verbose_name="quota"),
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
                (
                    "teacher_picture",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=seminar.models.teacher_picture_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="teacher picture",
                    ),
                ),
                (
                    "registration_end_date",
                    models.DateField(verbose_name="registration end date"),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="seminaries",
                        to="event.event",
                        verbose_name="event",
                    ),
                ),
                (
                    "price",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="seminars",
                        to="seminar.seminarprice",
                        verbose_name="price",
                    ),
                ),
            ],
            options={
                "verbose_name": "seminar",
                "verbose_name_plural": "seminars",
                "ordering": ["teacher", "date", "time"],
            },
        ),
        migrations.CreateModel(
            name="SeminarRegistration",
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
                    "academy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="seminar_registrations",
                        to="academy.academy",
                        verbose_name="academy",
                    ),
                ),
                (
                    "dancer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seminar_registrations",
                        to="academy.dancer",
                        verbose_name="dancer",
                    ),
                ),
                (
                    "seminar",
                    models.ForeignKey(
                        limit_choices_to={
                            "registration_end_date__gte": datetime.date(2024, 1, 16)
                        },
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seminar_registrations",
                        to="seminar.seminar",
                        verbose_name="seminar",
                    ),
                ),
            ],
            options={
                "verbose_name": "seminar registration",
                "verbose_name_plural": "seminar registrations",
                "ordering": ["seminar"],
            },
        ),
        migrations.CreateModel(
            name="SeminarPayment",
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
                        verbose_name="payment method",
                    ),
                ),
                (
                    "date",
                    models.DateField(default=datetime.date.today, verbose_name="date"),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "seminar_registration",
                    models.ForeignKey(
                        limit_choices_to={
                            "seminar__registration_end_date__gte": datetime.date(
                                2024, 1, 16
                            )
                        },
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="seminar_payments",
                        to="seminar.seminarregistration",
                        verbose_name="seminar registration",
                    ),
                ),
            ],
            options={
                "verbose_name": "seminar payment",
                "verbose_name_plural": "seminar payments",
                "ordering": ["-date"],
            },
        ),
        migrations.AddConstraint(
            model_name="seminar",
            constraint=models.UniqueConstraint(
                fields=("event", "teacher", "date", "time", "price"),
                name="seminar_uniqueness",
            ),
        ),
        migrations.AddConstraint(
            model_name="seminarregistration",
            constraint=models.UniqueConstraint(
                fields=("seminar", "dancer"), name="seminar_registration_uniqueness"
            ),
        ),
    ]
