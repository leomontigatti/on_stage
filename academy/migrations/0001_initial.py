import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import academy.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="OSUser",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="email address"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", academy.models.OSUserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Academy",
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
                    models.CharField(max_length=50, unique=True, verbose_name="name"),
                ),
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
                ("city", models.CharField(max_length=100, verbose_name="city")),
                ("state", models.CharField(max_length=100, verbose_name="state")),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"is_staff": False},
                        on_delete=django.db.models.deletion.RESTRICT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "academy",
                "verbose_name_plural": "academies",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Dancer",
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
                ("birth_date", models.DateField(verbose_name="birth date")),
                (
                    "is_verified",
                    models.BooleanField(default=False, verbose_name="is verified"),
                ),
                (
                    "identification_type",
                    models.CharField(
                        choices=[("ID", "ID"), ("PASSPORT", "Passport")],
                        default="ID",
                        max_length=50,
                        verbose_name="identification type",
                    ),
                ),
                (
                    "identification_number",
                    models.CharField(
                        max_length=20, verbose_name="identification number"
                    ),
                ),
                (
                    "identification_front_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=academy.models.id_front_picture_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="identification front image",
                    ),
                ),
                (
                    "identification_back_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=academy.models.id_back_picture_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="identification back image",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "academy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="dancers",
                        to="academy.academy",
                        verbose_name="academy",
                    ),
                ),
            ],
            options={
                "verbose_name": "dancer",
                "verbose_name_plural": "dancers",
                "ordering": ["last_name"],
            },
        ),
        migrations.CreateModel(
            name="Professor",
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
                (
                    "identification_type",
                    models.CharField(
                        choices=[("ID", "ID"), ("PASSPORT", "Passport")],
                        default="ID",
                        max_length=50,
                        verbose_name="identification type",
                    ),
                ),
                (
                    "identification_number",
                    models.CharField(
                        max_length=20, verbose_name="identification number"
                    ),
                ),
                (
                    "identification_front_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=academy.models.id_front_picture_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="identification front image",
                    ),
                ),
                (
                    "identification_back_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=academy.models.id_back_picture_path,
                        validators=[academy.models.MaxFileSizeValidator(10485760)],
                        verbose_name="identification back image",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("change_date", models.DateTimeField(auto_now=True)),
                (
                    "academy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="professors",
                        to="academy.academy",
                        verbose_name="academy",
                    ),
                ),
            ],
            options={
                "verbose_name": "professor",
                "verbose_name_plural": "professors",
                "ordering": ["last_name"],
            },
        ),
        migrations.AddConstraint(
            model_name="dancer",
            constraint=models.UniqueConstraint(
                fields=("academy", "identification_type", "identification_number"),
                name="dancer_uniqueness",
            ),
        ),
        migrations.AddConstraint(
            model_name="professor",
            constraint=models.UniqueConstraint(
                fields=("academy", "identification_type", "identification_number"),
                name="professor_uniqueness",
            ),
        ),
    ]
