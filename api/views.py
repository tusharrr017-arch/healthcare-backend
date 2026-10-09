from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Doctor, Patient, PatientDoctorMapping
from .serializers import (
    DoctorSerializer,
    LoginSerializer,
    PatientDoctorMappingSerializer,
    PatientSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {'message': 'User registered successfully.'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class PatientListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)


class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class MappingListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientDoctorMappingSerializer

    def get_queryset(self):
        return PatientDoctorMapping.objects.select_related('patient', 'doctor').filter(
            patient__created_by=self.request.user,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MappingPatientDoctorsView(APIView):
    """GET: list doctors assigned to patient (pk = patient_id). DELETE: remove mapping (pk = mapping id)."""

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk, created_by=request.user)
        except Patient.DoesNotExist:
            return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)
        mappings = PatientDoctorMapping.objects.filter(patient=patient).select_related('doctor')
        doctors = [m.doctor for m in mappings]
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            mapping = PatientDoctorMapping.objects.select_related('patient').get(pk=pk)
        except PatientDoctorMapping.DoesNotExist:
            return Response({'detail': 'Mapping not found.'}, status=status.HTTP_404_NOT_FOUND)
        if mapping.patient.created_by != request.user:
            return Response({'detail': 'Mapping not found.'}, status=status.HTTP_404_NOT_FOUND)
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
