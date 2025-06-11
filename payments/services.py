import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_checkout_session(payment):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(payment.money_to_pay * 100),
                "product_data": {
                    "name": f"Fine for {payment.borrowing.book.title}",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:8000/success/",
        cancel_url="http://localhost:8000/cancel/",
        metadata={
            "payment_id": payment.id,
        }
    )
    return session
