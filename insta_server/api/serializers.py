from pip import main
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class ProfileSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(read_only=True, source='user.username')
    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, profile, validated_data):
        username = self.context.get('username')
        new_username = self.context.get('new_username')
        user = User.objects.get(username=username)
        user_data = {'username': new_username}
        user_serializer = UserSerializer(
            instance=user, data=user_data, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()
        for (key, value) in validated_data.items():
            setattr(profile, key, value)
        profile.save()
        return profile

class PostSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

