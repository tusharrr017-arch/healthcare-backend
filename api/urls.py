from django.urls import path

from .views import (
    DoctorDetailView,
    DoctorListCreateView,
    LoginView,
    MappingListCreateView,
    MappingPatientDoctorsView,
    PatientDetailView,
    PatientListCreateView,
    RegisterView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('patients/', PatientListCreateView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('doctors/', DoctorListCreateView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('mappings/', MappingListCreateView.as_view(), name='mapping-list'),
    path('mappings/<int:pk>/', MappingPatientDoctorsView.as_view(), name='mapping-patient-or-delete'),
]
