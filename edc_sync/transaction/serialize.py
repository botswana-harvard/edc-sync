from django.core import serializers


def serialize(objects=None):
    return serializers.serialize(
        'json', objects,
        ensure_ascii=True,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=False)
