from django.urls import include, path

from choreography import views

urlpatterns = [
    path("event/<str:sender>/", views.event_list_view, name="event_list"),
    path(
        "choreography/",
        include(
            [
                path(
                    "list/<int:event_pk>/",
                    views.choreography_list_view,
                    name="choreography_list",
                ),
                path(
                    "create/<int:event_pk>/",
                    views.choreography_create_view,
                    name="choreography_create",
                ),
                path(
                    "detail/<int:choreography_pk>/",
                    views.choreography_detail_view,
                    name="choreography_detail",
                ),
                path(
                    "update/<int:choreography_pk>/",
                    views.choreography_update_view,
                    name="choreography_update",
                ),
                path(
                    "manage_payments/",
                    views.manage_payments_view,
                    name="manage_payments_view",
                ),
                path(
                    "set_order_number/",
                    views.set_order_number,
                    name="set_order_number",
                ),
            ]
        ),
    ),
    path(
        "award/",
        include(
            [
                path("list/<int:event_pk>/", views.award_list_view, name="award_list"),
                path(
                    "detail/<int:choreography_pk>/",
                    views.award_detail_view,
                    name="award_detail",
                ),
                path(
                    "certificate/<int:choreography_pk>/<str:sender>/<int:sender_pk>/",
                    views.award_certificate,
                    name="award_certificate",
                ),
            ]
        ),
    ),
    path(
        "payment/",
        include(
            [
                path(
                    "list/<int:event_pk>/", views.payment_list_view, name="payment_list"
                ),
                path(
                    "detail/<int:choreography_pk>/",
                    views.payment_detail,
                    name="payment_detail",
                ),
            ]
        ),
    ),
    path(
        "score/",
        include(
            [
                path("list/<int:event_pk>/", views.score_list_view, name="score_list"),
                path(
                    "toggle_disqualified/<int:choreography_pk>",
                    views.toggle_disqualified,
                    name="toggle_disqualified",
                ),
                path(
                    "lock_scores/<int:event_pk>/", views.lock_scores, name="lock_scores"
                ),
                path(
                    "delete_feedback/<int:score_pk>/",
                    views.feedback_delete_view,
                    name="delete_feedback",
                ),
            ]
        ),
    ),
    path(
        "music/",
        include(
            [
                path("list/<int:event_pk>/", views.music_list, name="music_list"),
            ]
        ),
    ),
]
