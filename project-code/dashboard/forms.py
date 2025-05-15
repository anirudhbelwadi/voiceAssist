from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Patient, Doctor, ScreeningTemplate

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=200, widget=forms.TextInput(attrs={'style': 'font-size: 24px;', 'class': 'form-control'}))
    password = forms.CharField(label="Password", max_length=200, widget=forms.PasswordInput(attrs={'style': 'font-size: 24px;', 'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'password']

class RegisterForm(forms.Form):
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    email = forms.EmailField(label="E-mail", max_length=50, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    phone_number = forms.CharField(label="Phone Number", max_length=15, widget=forms.TextInput(attrs={'style': 'font-size: 24px'}))

class ScreeningRequestForm(forms.Form):
    doctor = None
    
    patient_choices = forms.ModelChoiceField(
        queryset=Patient.objects.none(),
        label="Select Patient",
        empty_label="Select Patient"
    )
    # template = forms.ChoiceField(choices=[(x, x) for x in TEMPLATE_CHOICES])
    template = forms.ModelChoiceField(
        queryset=Doctor.objects.none(),
        label="Select Template",
        empty_label="Select Template"
    )
    due_date = forms.DateField(label="Due Date", widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, doctor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['patient_choices'].queryset = doctor.patients.all()
            self.fields['template'].queryset = ScreeningTemplate.objects.filter(doctor=doctor)

class TemplateForm(forms.Form):
    name = forms.CharField(label="Template Name", max_length=255, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    question1 = forms.CharField(label="Question 1", max_length=1000, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    question2 = forms.CharField(label="Question 2", max_length=1000, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    question3 = forms.CharField(label="Question 3", max_length=1000, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    question4 = forms.CharField(label="Question 4", max_length=1000, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    question5 = forms.CharField(label="Question 5", max_length=1000, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))

class DoctorProfileForm(forms.Form):
    phone_number = forms.CharField(label="Phone Number", max_length=15, widget=forms.TextInput(attrs={'style': 'font-size: 24px'}))
    institution = forms.CharField(label="Institution", max_length=255, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    specialty = forms.CharField(label="Specialty", max_length=255, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))

class PatientProfileForm(forms.Form):
    phone_number = forms.CharField(label="Phone Number", max_length=15, widget=forms.TextInput(attrs={'style': 'font-size: 24px'}))
    address = forms.CharField(label="Address", max_length=255, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}))
    date_of_birth = forms.DateField(label="Date of Birth", widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[(x, y) for x,y in [['','Select a gender'], ['Male', 'Male'], ['Female','Female'], ['Other','Other']]], label="Select Gender")
    is_call_preferred = forms.BooleanField(label="Call Preferred", required=False, widget=forms.CheckboxInput(attrs={'style': 'font-size: 24px;'}))

class PatientVitalsForm(forms.Form):
    blood_pressure = forms.CharField(label="Blood Pressure", max_length=10, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}), required=False)
    blood_sugar_level = forms.CharField(label="Blood Sugar Level", max_length=10, widget=forms.TextInput(attrs={'style': 'font-size: 24px;'}), required=False)
    weight = forms.FloatField(label="Weight (kg)", widget=forms.NumberInput(attrs={'style': 'font-size: 24px;'}), required=False)
    height = forms.FloatField(label="Height (cm)", widget=forms.NumberInput(attrs={'style': 'font-size: 24px;'}), required=False)