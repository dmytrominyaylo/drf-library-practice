from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from books.tests import sample_book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer

BORROWING_URL = reverse("borrowings:borrowings-list-create")


def sample_borrowing(**params) -> Borrowing:
    book = sample_book()
    defaults = {
        "borrow_date": "2025-01-10",
        "expected_return_date": "2025-01-20",
        "actual_return_date": None,
        "book": book,
        "user": params.get("user")
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


class UnauthenticatedBorrowingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test", password="testpassword"
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@test.test", password="otherpassword"
        )
        self.borrowing1 = sample_borrowing(user=self.user)
        self.borrowing2 = sample_borrowing(user=self.user)
        self.borrowing3 = sample_borrowing(user=self.user)
        self.borrowing4 = sample_borrowing(user=self.other_user)
        self.client.force_authenticate(self.user)

    def test_create_borrowing(self):
        book = sample_book()
        payload = {
            "borrow_date": "2025-01-10",
            "expected_return_date": "2025-01-20",
            "book": book.id,
        }
        res = self.client.post(BORROWING_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_borrowing_detail(self):
        borrowing = sample_borrowing(user=self.user)
        url = detail_url(borrowing.id)
        res = self.client.get(url)
        serializer = BorrowingSerializer(borrowing)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_cannot_see_others_borrowings(self):
        self.client.force_login(self.user)
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        for borrowing in res.data:
            self.assertEqual(borrowing["user"], self.user.id)

    def test_authenticated_user_can_filter_active_borrowings(self):
        self.client.force_login(self.user)
        res = self.client.get(BORROWING_URL, {"is_active": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        res = self.client.get(BORROWING_URL, {"is_active": "false"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)


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
        self.borrowing2 = sample_borrowing(user=self.user)
        self.borrowing3 = sample_borrowing(user=self.user)
        self.borrowing4 = sample_borrowing(
            user=self.other_user, actual_return_date="2025-01-12"
        )
        self.client.force_authenticate(self.admin)

    def test_admin_user_sees_all_borrowings(self):
        self.client.force_login(self.admin)
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 4)

    def test_admin_user_filters_by_user_id(self):
        self.client.force_login(self.admin)
        res = self.client.get(BORROWING_URL, {"user_id": self.user.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(res.data[0]["user"], self.user.id)

    def test_is_active_filter(self):
        self.client.force_login(self.admin)
        res = self.client.get(BORROWING_URL, {"is_active": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        res = self.client.get(BORROWING_URL, {"is_active": "false"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
