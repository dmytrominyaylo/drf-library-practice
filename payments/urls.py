from rest_framework import routers
from django.urls import path, include
from payments.views import PaymentViewSet
from .views import CreateStripeSessionView

app_name = "payments"

router = routers.DefaultRouter()
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("", include(router.urls)),
    path("create-checkout-session/", CreateStripeSessionView.as_view(), name="create-checkout-session"),
]
