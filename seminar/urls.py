from django.urls import include, path

from seminar import views

urlpatterns = [
    path(
        "seminar_registration/",
        include(
            [
                path(
                    "list/<int:event_pk>/",
                    views.seminar_registration_list_view,
                    name="seminarregistration_list",
                ),
                path(
                    "create/<int:seminar_pk>/",
                    views.seminar_registration_create_view,
                    name="seminarregistration_create",
                ),
                path(
                    "delete/<int:seminar_registration_pk>/",
                    views.seminar_registration_delete_view,
                    name="seminarregistration_delete",
                ),
            ]
        ),
    ),
]
