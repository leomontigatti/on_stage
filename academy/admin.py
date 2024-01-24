from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from academy.models import Academy, Dancer, Professor
from choreography.models import Choreography

OSUser = get_user_model()


class IsParticipatingFilter(SimpleListFilter):
    title = _("is participating")
    parameter_name = "is_participating"

    def lookups(self, request, model_admin):
        return (
            ("true", _("Yes")),
            ("false", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(
                choreographies__event__end_date__lte=timezone.now().date()
            ).distinct()
        elif self.value() == "false":
            return queryset.exclude(
                choreographies__event__end_date__lte=timezone.now().date()
            ).distinct()
        else:
            return queryset


@admin.register(OSUser)
class OSUserAdmin(UserAdmin):
    list_display = ["email", "first_name", "last_name", "is_staff"]
    list_filter = ["groups", "is_active"]
    list_display_links = ["email"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal information"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(is_superuser=False)
        return queryset

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return [
                "email",
                "is_superuser",
                "last_login",
                "date_joined",
                "user_permissions",
            ]
        return []


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_filter = ("content_type__app_label",)
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description=_("App"))
    def app_label(self, obj):
        return obj.content_type.app_label.title()

    @admin.display(description=_("Model"))
    def model_name(self, obj):
        return obj.content_type.model.title()


@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "user", "phone_number"]
    list_display_links = ["id", "name"]
    search_fields = ["id", "name", "user__email", "user__email"]
    search_help_text = _("Search by ID, academy name or email.")
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "name",
                    "phone_number",
                    ("city", "state"),
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ["user", "name"]
        else:
            return super().get_readonly_fields(request, obj)


@admin.register(Dancer)
class DancerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "__str__",
        "academy",
        "is_participating",
        "has_images",
        "is_verified",
    ]
    list_filter = ["is_verified", IsParticipatingFilter, "academy"]
    list_display_links = ["id", "__str__"]
    search_fields = [
        "id",
        "first_name",
        "last_name",
        "academy__name",
        "identification_number",
    ]
    search_help_text = _(
        "Search by ID, identification number, academy name, first or last name."
    )
    show_facets = admin.ShowFacets.NEVER

    @admin.display(boolean=True, description=_("Has images"))
    def has_images(self, obj):
        return all([obj.identification_front_image, obj.identification_back_image])

    @admin.display(boolean=True, description=_("Is participating"))
    def is_participating(self, obj):
        return obj.choreographies.filter(
            event__end_date__lte=timezone.now().date()
        ).exists()

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "academy",
                    ("first_name", "last_name"),
                    ("birth_date", "is_verified"),
                    ("identification_type", "identification_number"),
                )
            },
        ),
        (
            _("Images"),
            {"fields": (("identification_front_image", "identification_back_image"),)},
        ),
    )

    def get_readonly_fields(self, request, obj):
        if not request.user.is_superuser:
            readonly_fields = [field.name for field in self.model._meta.fields]
            readonly_fields.remove("is_verified")
            return readonly_fields
        return []

    class ParticipatingChoreographies(admin.TabularInline):
        model = Choreography.dancers.through
        extra = 0
        verbose_name_plural = _("choreographies")

        def has_change_permission(self, request, obj=None):
            return False

        def has_add_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    inlines = [ParticipatingChoreographies]


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__", "academy", "is_participating"]
    list_filter = [IsParticipatingFilter, "academy"]
    list_display_links = ["id", "__str__"]
    search_fields = [
        "id",
        "first_name",
        "last_name",
        "academy__name",
        "identification_number",
    ]
    search_help_text = _(
        "Search by ID, identification number, academy name, first or last name."
    )
    show_facets = admin.ShowFacets.NEVER

    @admin.display(boolean=True, description=_("Is participating"))
    def is_participating(self, obj):
        return obj.choreographies.filter(
            event__end_date__lte=timezone.now().date()
        ).exists()

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "academy",
                    ("first_name", "last_name"),
                    ("identification_type", "identification_number"),
                )
            },
        ),
        (
            _("Images"),
            {"fields": (("identification_front_image", "identification_back_image"),)},
        ),
    )

    class ParticipatingChoreographies(admin.TabularInline):
        model = Choreography.professors.through
        extra = 0
        verbose_name_plural = _("choreographies")

        def has_change_permission(self, request, obj=None):
            return False

        def has_add_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    inlines = [ParticipatingChoreographies]
