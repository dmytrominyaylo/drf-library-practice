import stripe
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from payments.models import Payment
from borrowings.models import Borrowing
from payments.serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("borrowing")
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(borrowing__user=self.request.user)


class CreateStripeSessionView(View):
    def post(self, request, *args, **kwargs):
        borrowing_id = request.POST.get("borrowing_id")
        try:
            borrowing = Borrowing.objects.get(id=borrowing_id)
        except Borrowing.DoesNotExist:
            return JsonResponse({"error": "Borrowing not found"}, status=404)
        payment = Payment.objects.filter(borrowing=borrowing).first()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(payment.money_to_pay * 100),
                    "product_data": {
                        "name": f"{payment.type_field} for {borrowing.book.title}",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://your-site.com/success",
            cancel_url="https://your-site.com/cancel",
        )
        payment.session_id = session.id
        payment.session_url = session.url
        payment.save()
        return JsonResponse({"checkout_url": session.url})
