from rest_framework import serializers
from .models import AuthUser, Insurance, Driver, Driver_Insurance



class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined']


class InsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insurance
        fields = [
                    'id', 'type', 'certificate_number', 
                    'certificate_series', 'date_creation', 'date_begin', 'date_end', 
                    'date_completion', 'car_brand', 'car_model', 'car_region', 
                    'status', 'creator', 'moderator', 'average_experience'
            ]
        

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
                    'id', 'name', 'certificate_number', 'license', 
                    'experience', 'image_url', 'characteristics', 'status',
            ]
        

class DriverInsuranceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Driver_Insurance
        fields = ['id', 'driver', 'insurance', 'owner']