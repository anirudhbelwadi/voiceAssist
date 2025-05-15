from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    isDoctor = models.BooleanField(default=False)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    user_profile = models.OneToOneField(UserProfile, on_delete=models.PROTECT, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    is_call_mode_of_screening = models.BooleanField(default=False)
    blood_pressure = models.CharField(max_length=10, blank=True, null=True)
    blood_sugar_level = models.CharField(max_length=10, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    def __str__(self):
        return self.user.username

class Medication(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name} ({self.frequency})"

class HealthCondition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    severity = models.CharField(max_length=50)
    diagnosis_date = models.DateField()
    def __str__(self):
        return f"{self.name} ({self.severity})"

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    user_profile = models.OneToOneField(UserProfile, on_delete=models.PROTECT, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    specialty = models.CharField(max_length=255, blank=True, null=True)
    patients = models.ManyToManyField(Patient)

class ScreeningRequest(models.Model):
    request_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    conversation = models.JSONField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)
    template = models.ForeignKey('ScreeningTemplate', on_delete=models.CASCADE, blank=True, null=True)
    summary = models.CharField(blank=True, null=True, max_length=10000)
    def __str__(self):
        return f"Screening Request ({self.patient.user.username} - {self.doctor.user.username})"

class ScreeningTemplate(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    question1 = models.CharField(max_length=1000, blank=True, null=True)
    question2 = models.CharField(max_length=1000, blank=True, null=True)
    question3 = models.CharField(max_length=1000, blank=True, null=True)
    question4 = models.CharField(max_length=1000, blank=True, null=True)
    question5 = models.CharField(max_length=1000, blank=True, null=True)
    def __str__(self):
        return self.name