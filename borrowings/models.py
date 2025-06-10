from django.conf import settings
from django.db import models
from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowing"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowing"
    )

    @property
    def is_returned(self):
        return self.actual_return_date is not None

    def __str__(self):
        return f"{self.user} borrowed {self.book.title}"
