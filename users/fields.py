# fields.py
from rest_framework import serializers
from bson import ObjectId

class ObjectIdField(serializers.BaseSerializer):
    def to_representation(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value

    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid ObjectId format.")
