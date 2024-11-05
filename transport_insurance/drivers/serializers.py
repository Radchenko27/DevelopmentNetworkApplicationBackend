from rest_framework import serializers
from .models import  Insurance, Driver, Driver_Insurance, CustomUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
# class AuthUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AuthUser
#         fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
                    'id', 'name', 'certificate_number', 'license', 
                    'experience', 'image_url', 'characteristics', 'status',
            ]
        

class DriverInsuranceSerializers(serializers.ModelSerializer):
    driver = DriverSerializer()
    class Meta:
        model = Driver_Insurance
        fields = ['id', 'driver', 'insurance', 'owner']


class InsuranceSerializer(serializers.ModelSerializer):

    drivers = DriverInsuranceSerializers(many=True, source='driver_insurance_set') 
    date_creation = serializers.DateTimeField(format='%Y-%m-%dT%H:%M', read_only=True)
    date_formation = serializers.DateTimeField(format='%Y-%m-%dT%H:%M', allow_null=True, required=False)
    date_creation = serializers.DateTimeField(format='%Y-%m-%dT%H:%M', allow_null=True, required=False)
    date_begin = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
    date_end = serializers.DateField(format='%Y-%m-%d', allow_null=True, required=False)
    
    class Meta:
        model = Insurance
        fields = [
                    'id', 'type', 'certificate_number', 
                    'certificate_series', 'date_creation', 'date_begin', 'date_end', 'date_formation',
                    'date_completion', 'car_brand', 'car_model', 'car_region', 
                    'status', 'creator', 'moderator', 'average_experience', 'drivers'
            ]

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', None)
        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field) 
        super(InsuranceSerializer, self).__init__(*args, **kwargs)  


class CustomUserSerializer(serializers.ModelSerializer):

    is_staff = serializers.BooleanField(default=True, required=False)
    is_superuser = serializers.BooleanField(default=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']

    def create(self, validated_data):
    # Хешируем пароль перед сохранением
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    # Метод для обновления пользователя
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)
    
    def authenticate_user(self, username, password):
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        return user

         