from django.urls import path
from borrowings.views import (
    BorrowingListCreateView, BorrowingDetail, ReturnBorrowingView
)

app_name = "borrowings"

urlpatterns = [
    path(
        "borrowings/",
        BorrowingListCreateView.as_view(),
        name="borrowings-list-create"
    ),
    path(
        "borrowings/<int:pk>/",
        BorrowingDetail.as_view(),
        name="borrowing-detail"
    ),
    path(
        "borrowings/<int:pk>/return/",
        ReturnBorrowingView.as_view(),
        name="return-borrowing"
    ),
]
