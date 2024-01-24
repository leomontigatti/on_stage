from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from event.forms import (
    AwardTypeAdminForm,
    CategoryAdminForm,
    DanceModeAdminForm,
    PriceAdminForm,
    ScheduleAdminForm,
)
from event.models import AwardType, Category, Contact, DanceMode, Event, Price, Schedule


@admin.register(AwardType)
class AwardTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_special", "min_average_score", "max_average_score"]
    list_filter = ["event", "is_special"]
    list_display_links = ["name"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "event",
                    ("name", "is_special", "color"),
                    ("min_average_score", "max_average_score"),
                )
            },
        ),
    )

    filter_horizontal = ["event"]

    form = AwardTypeAdminForm


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "min_age", "max_age"]
    list_filter = ["event", "type"]
    list_display_links = ["name"]
    search_fields = ["id", "name", "type"]
    search_help_text = _("Search by PK, category or type")
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "event",
                    ("name", "type"),
                    ("min_age", "max_age"),
                    "max_duration",
                )
            },
        ),
    )

    filter_horizontal = ["event"]

    form = CategoryAdminForm


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "phone_number"]
    list_display_links = ["id", "email"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("first_name", "last_name"),
                    "email",
                    ("phone_number",),
                    "bank_name",
                    ("account_owner", "account_owner_id_number"),
                    ("account_type", "routing_number", "alias"),
                )
            },
        ),
    )


@admin.register(DanceMode)
class DanceModeAdmin(admin.ModelAdmin):
    list_display = ["name", "sub_mode"]
    list_filter = ["event", "name"]
    list_display_links = ["name"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = ((None, {"fields": ("event", ("name", "sub_mode"))}),)

    filter_horizontal = ["event"]

    form = DanceModeAdminForm


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "start_date", "end_date", "ongoing"]
    list_filter = ["name"]
    list_display_links = ["id", "name"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("name",),
                    ("start_date", "end_date", "registration_end_date"),
                    ("city", "state", "country"),
                    "judge",
                    ("contact", "deposit_percentage"),
                )
            },
        ),
    )

    filter_horizontal = ["judge"]

    @admin.display(boolean=True, description=_("Ongoing"))
    def ongoing(self, obj):
        return obj.started and not obj.ended

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or obj and not obj.ended


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ["event", "name", "category_type", "due_date", "amount"]
    list_filter = ["event", "category_type", "due_date"]
    list_display_links = ["due_date", "amount"]
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("event",),
                    ("name", "category_type"),
                    ("amount", "due_date"),
                )
            },
        ),
    )

    form = PriceAdminForm

    def get_readonly_fields(self, request, obj):
        return (
            ["event", "name", "category_type"]
            if not request.user.is_superuser and obj
            else []
        )

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or obj and not obj.event.ended


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["event", "dance_mode", "date", "time"]
    list_filter = ["event", "dance_mode__name"]
    list_display_links = ["date", "time"]
    search_fields = ["id", "date", "time"]
    search_help_text = _("Search by PK, date or time.")
    show_facets = admin.ShowFacets.ALWAYS

    fieldsets = ((None, {"fields": ("event", "dance_mode", ("date", "time"))}),)

    form = ScheduleAdminForm

    def get_readonly_fields(self, request, obj):
        return ["event", "dance_mode"] if not request.user.is_superuser and obj else []

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or obj and not obj.event.ended
