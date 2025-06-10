from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from borrowings.tests import sample_borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer

PAYMENT_URL = reverse("payments:payments-list")


def sample_payment(**params) -> Payment:
    defaults = {
        "status": "Paid",
        "type_field": "Payment",
        "session_url": "https://example.com",
        "session_id": "session_id",
        "money_to_pay": 4.00,
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)


def detail_url(payment_id):
    return reverse("payments:payments-detail", args=[payment_id])


class UnauthenticatedPaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="testpassword"
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@test.test", password="otherpassword"
        )
        self.borrowing1 = sample_borrowing(user=self.user)
        self.borrowing2 = sample_borrowing(user=self.other_user)
        self.payment1 = sample_payment(borrowing=self.borrowing1)
        self.payment2 = sample_payment(borrowing=self.borrowing1)
        self.payment3 = sample_payment(borrowing=self.borrowing2)
        self.client.force_authenticate(self.user)

    def test_create_payment(self):
        borrowing = sample_borrowing(user=self.user)
        payload = {
            "status": "PENDING",
            "type_field": "PAYMENT",
            "borrowing": borrowing.id,
            "session_url": "https://example.com",
            "session_id": "session_id",
            "money_to_pay": 4.00,
        }
        res = self.client.post(PAYMENT_URL, payload)
        if res.status_code != status.HTTP_201_CREATED:
            print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_payment_detail(self):
        borrowing = sample_borrowing(user=self.user)
        payment = sample_payment(borrowing_id=borrowing.id)
        url = detail_url(payment.id)
        res = self.client.get(url)
        serializer = PaymentSerializer(payment)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_cannot_see_others_payments(self):
        self.client.force_login(self.user)
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_other_user_payments_not_accessible(self):
        res = self.client.get(PAYMENT_URL)
        self.assertFalse(any(payment["id"] == self.payment3.id for payment in res.data))


class AdminBorrowingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@admin.test", password="testpassword", is_staff=True,
        )
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="testpassword"
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@test.test", password="otherpassword"
        )
        self.borrowing1 = sample_borrowing(user=self.user)
        self.borrowing2 = sample_borrowing(user=self.other_user)
        self.payment1 = sample_payment(borrowing=self.borrowing1)
        self.payment2 = sample_payment(borrowing=self.borrowing1)
        self.payment3 = sample_payment(borrowing=self.borrowing2)
        self.client.force_authenticate(self.admin)

    def test_admin_can_see_all_payments(self):
        res = self.client.get(PAYMENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
