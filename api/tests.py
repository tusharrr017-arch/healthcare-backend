from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Doctor, Patient, PatientDoctorMapping

User = get_user_model()


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


class RegistrationTests(APITestCase):
    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post('/api/auth/register/', {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='john@example.com')
        self.assertNotEqual(user.password, 'password123')
        self.assertTrue(user.check_password('password123'))

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            email='john@example.com', password='password123', name='John',
        )
        response = self.client.post('/api/auth/register/', {
            'name': 'Jane',
            'email': 'john@example.com',
            'password': 'password456',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class LoginTests(APITestCase):
    def setUp(self):
        User.objects.create_user(
            email='john@example.com', password='password123', name='John',
        )

    def test_login_returns_jwt(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'john@example.com',
            'password': 'password123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login_returns_401(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'john@example.com',
            'password': 'wrongpassword',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PatientAccessTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com', password='password123', name='Owner',
        )
        self.other = User.objects.create_user(
            email='other@example.com', password='password123', name='Other',
        )

    def test_unauthenticated_request_rejected(self):
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_patient_creation(self):
        response = self.client.post('/api/patients/', {
            'name': 'Jane Patient',
            'age': 30,
            'gender': 'F',
            'address': '123 Main St',
            'phone': '555-0100',
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_by'], self.user.id)

    def test_patient_gender_accepts_full_name(self):
        response = self.client.post('/api/patients/', {
            'name': 'Rahul Sharma',
            'age': 25,
            'gender': 'Male',
            'address': 'Jaipur',
            'phone': '9876543210',
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['gender'], 'M')

    def test_user_cannot_access_other_users_patient(self):
        patient = Patient.objects.create(
            name='Secret',
            age=40,
            gender='M',
            address='Hidden',
            phone='111',
            created_by=self.other,
        )
        response = self.client.get(
            f'/api/patients/{patient.id}/',
            **auth_header(self.user),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DoctorTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='docuser@example.com', password='password123', name='Doc User',
        )

    def test_doctor_creation_requires_auth(self):
        response = self.client.post('/api/doctors/', {
            'name': 'Dr Smith',
            'specialization': 'Cardiology',
            'phone': '555-0200',
            'email': 'smith@clinic.com',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_doctor_creation(self):
        response = self.client.post('/api/doctors/', {
            'name': 'Dr Smith',
            'specialization': 'Cardiology',
            'phone': '555-0200',
            'email': 'smith@clinic.com',
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class MappingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='mapuser@example.com', password='password123', name='Map User',
        )
        self.patient = Patient.objects.create(
            name='Jane',
            age=25,
            gender='F',
            address='Main',
            phone='555',
            created_by=self.user,
        )
        self.doctor = Doctor.objects.create(
            name='Dr Lee',
            specialization='General',
            phone='556',
            email='lee@clinic.com',
        )

    def test_mapping_creation(self):
        response = self.client.post('/api/mappings/', {
            'patient': self.patient.id,
            'doctor': self.doctor.id,
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

    def test_duplicate_mapping_rejected(self):
        PatientDoctorMapping.objects.create(patient=self.patient, doctor=self.doctor)
        response = self.client.post('/api/mappings/', {
            'patient': self.patient.id,
            'doctor': self.doctor.id,
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_doctor_id_rejected(self):
        response = self.client.post('/api/mappings/', {
            'patient': self.patient.id,
            'doctor': 99999,
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('doctor', response.data)

    def test_cannot_map_other_users_patient(self):
        other = User.objects.create_user(
            email='other2@example.com', password='password123', name='Other',
        )
        other_patient = Patient.objects.create(
            name='Not Mine',
            age=50,
            gender='M',
            address='Elsewhere',
            phone='999',
            created_by=other,
        )
        response = self.client.post('/api/mappings/', {
            'patient': other_patient.id,
            'doctor': self.doctor.id,
        }, format='json', **auth_header(self.user))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('patient', response.data)
