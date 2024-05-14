from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

from project.apps.profile.models import User
from .validators import phone_regex_validator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    # phone_number = serializers.CharField(
    #         validators=[phone_regex_validator, UniqueValidator(queryset=User.objects.all())]
    #         )
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    # profile_image = serializers.ImageField(allow_empty_file=True)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email', 'first_name',
                  'last_name', 'phone_number', 'profile_image']

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            profile_image=validated_data['profile_image']
        )

        user.set_password(validated_data['password1'])
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=True, validators=[UnicodeUsernameValidator])
    password = serializers.CharField(write_only=True, required=True)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_image']


class ChangePasswordSerializer(serializers.Serializer):
    old_pass = serializers.CharField(write_only=True, required=True)
    new_pass = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_pass_repeat = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_pass'] == attrs['old_pass']:
            raise serializers.ValidationError({"Same password": "New Password and old password must not be the same."})

        if attrs['new_pass'] != attrs['new_pass_repeat']:
            raise serializers.ValidationError({"Confirmation error": "New Password fields didn't match."})

        return attrs
