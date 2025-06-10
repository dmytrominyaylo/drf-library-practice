from rest_framework import serializers
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type_field",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay"
        ]
