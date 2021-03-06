from rest_framework import serializers

from edc_rest.binary_field import BinaryField
from edc_rest.serializers import BaseModelSerializerMixin

from .choices import ACTIONS
from .models import IncomingTransaction, OutgoingTransaction


class BaseTransactionSerializer(BaseModelSerializerMixin, serializers.Serializer):

    pk = serializers.UUIDField(read_only=True)

    tx = BinaryField()

    tx_name = serializers.CharField(
        max_length=64)

    tx_pk = serializers.UUIDField()

    producer = serializers.CharField(max_length=200)

    action = serializers.ChoiceField(
        choices=ACTIONS)

    timestamp = serializers.CharField(
        max_length=50)

    consumed_datetime = serializers.DateTimeField(
        allow_null=True,
        default=None)

    consumer = serializers.CharField(
        max_length=200,
        allow_null=True,
        allow_blank=True)

    is_ignored = serializers.BooleanField(
        default=False)

    is_error = serializers.BooleanField(
        default=False)

    error = serializers.CharField(
        max_length=1000,
        allow_null=True,
        allow_blank=True)


class IncomingTransactionSerializer(BaseTransactionSerializer):

    model_class = IncomingTransaction

    is_consumed = serializers.BooleanField(
        default=False)


class OutgoingTransactionSerializer(BaseTransactionSerializer):

    model_class = OutgoingTransaction

    is_consumed_server = serializers.BooleanField(
        default=False)

    is_consumed_middleman = serializers.BooleanField(
        default=False)


# class SyncConfirmationSerializer(
#         BaseModelSerializerMixin, serializers.Serializer):
#
#     model_class = SyncConfirmation
