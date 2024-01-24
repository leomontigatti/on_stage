from django.urls import include, path

from academy import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.user_registration, name="signup"),
    path("terms/", views.terms, name="terms"),
    path("activate/<str:uidb64>/<str:token>/", views.activate, name="activate"),
    path(
        "whatsapp_message/<int:contact_pk>/",
        views.whatsapp_message,
        name="whatsapp_message",
    ),
    path(
        "dancer/",
        include(
            [
                path("list/", views.dancer_list_view, name="dancer_list"),
                path("create/", views.dancer_create_view, name="dancer_create"),
                path(
                    "detail/<int:dancer_pk>/",
                    views.dancer_detail_view,
                    name="dancer_detail",
                ),
                path(
                    "update/<int:dancer_pk>/",
                    views.dancer_update_view,
                    name="dancer_update",
                ),
            ]
        ),
    ),
    path(
        "professor/",
        include(
            [
                path("list/", views.professor_list_view, name="professor_list"),
                path(
                    "create/",
                    views.professor_create_view,
                    name="professor_create",
                ),
                path(
                    "detail/<int:professor_pk>/",
                    views.professor_detail_view,
                    name="professor_detail",
                ),
                path(
                    "update/<int:professor_pk>/",
                    views.professor_update_view,
                    name="professor_update",
                ),
            ]
        ),
    ),
]
