from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework import serializers

from .models import Doctor, Patient, PatientDoctorMapping, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('name', 'email', 'password')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')
        attrs['email'] = email
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError('Invalid email or password.')
        attrs['user'] = user
        return attrs


class PatientSerializer(serializers.ModelSerializer):
    GENDER_ALIASES = {
        'm': 'M',
        'male': 'M',
        'f': 'F',
        'female': 'F',
        'o': 'O',
        'other': 'O',
    }

    class Meta:
        model = Patient
        fields = (
            'id', 'name', 'age', 'gender', 'address', 'phone',
            'created_by', 'created_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at')

    def validate_gender(self, value):
        if value is None:
            return value
        key = str(value).strip().lower()
        if key in self.GENDER_ALIASES:
            return self.GENDER_ALIASES[key]
        if value in ('M', 'F', 'O'):
            return value
        raise serializers.ValidationError(
            'Use M/F/O or Male/Female/Other.'
        )


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialization', 'phone', 'email', 'created_at')
        read_only_fields = ('id', 'created_at')


class PatientDoctorMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDoctorMapping
        fields = ('id', 'patient', 'doctor', 'assigned_at')
        read_only_fields = ('id', 'assigned_at')

    def validate_patient(self, value):
        request = self.context.get('request')
        if request and value.created_by != request.user:
            raise serializers.ValidationError('Patient not found.')
        return value

    def validate(self, attrs):
        patient = attrs.get('patient') or getattr(self.instance, 'patient', None)
        doctor = attrs.get('doctor') or getattr(self.instance, 'doctor', None)
        if patient and doctor:
            qs = PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    'This doctor is already assigned to this patient.'
                )
        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                'This doctor is already assigned to this patient.'
            )
