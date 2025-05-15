import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from .decorators import login_not_required_without_next, login_required_without_next
from .forms import LoginForm, RegisterForm, DoctorProfileForm, ScreeningRequestForm, PatientProfileForm, PatientVitalsForm, TemplateForm
from .models import Patient, Doctor, UserProfile, Medication, HealthCondition, ScreeningRequest, ScreeningTemplate
from .helper import errorResponse, addUserProfileToContext, generate_openai_followup, summarize_conversation
from django.utils import timezone
from .calling import start_screening_call
import asyncio
import threading


def oauthRedirectView(request):
    if UserProfile.objects.filter(user=request.user).exists():
        return redirect('dashboard')
    return render(request, 'dashboard/selectUserType.html')

def registerPatientView(request):
    user_profile = UserProfile.objects.create(
        user = request.user,
        first_name=request.user.first_name,
        last_name=request.user.last_name,
        email=request.user.social_auth.get(provider='google-oauth2').extra_data['email'],
        isDoctor=False
    )
    user_profile.save()
    patient = Patient.objects.create(user=request.user, user_profile=user_profile)
    patient.save()
    return redirect('dashboard')

def registerDoctorView(request):
    user_profile = UserProfile.objects.create(
        user = request.user,
        first_name=request.user.first_name,
        last_name=request.user.last_name,
        email=request.user.social_auth.get(provider='google-oauth2').extra_data['email'],
        isDoctor=True
    )
    user_profile.save()
    doctor = Doctor.objects.create(user=request.user, user_profile=user_profile)
    doctor.save()
    return redirect('dashboard')

@login_not_required_without_next
def loginView(request):
    context = {}
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            context['form'] = form
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                context['error'] = 'Invalid username or password'
                return render(request, 'dashboard/login.html', context)
    else:
        form = LoginForm()
    context['form'] = form
    return render(request, 'dashboard/login.html', context)

@login_required_without_next
def dashboardView(request):
    context = {}
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.isDoctor:
        return redirect('viewPatients')
    else:
        return redirect('patientDashboard')

@login_required_without_next
def patientDashboardView(request):
    context = addUserProfileToContext({}, request.user)
    non_completed_screenings = ScreeningRequest.objects.filter(patient=Patient.objects.get(user=request.user), completion_date__isnull=True)
    non_completed_screening_list = []
    for screening in non_completed_screenings:
        screening_list = {
            'id': screening.id,
            'request_date': screening.request_date,
            'due_date': screening.due_date,
            'doctor': screening.doctor.user_profile.first_name + " " + screening.doctor.user_profile.last_name
        }
        non_completed_screening_list.append(screening_list)
    context['non_completed_screenings'] = non_completed_screening_list
    completed_screenings = ScreeningRequest.objects.filter(patient=Patient.objects.get(user=request.user), completion_date__isnull=False)
    completed_screening_list = []
    for screening in completed_screenings:
        screening_list = {
            'id': screening.id,
            'request_date': screening.request_date,
            'due_date': screening.due_date,
            'doctor': screening.doctor.user_profile.first_name + " " + screening.doctor.user_profile.last_name,
            'completion_date': screening.completion_date
        }
        completed_screening_list.append(screening_list)
    context['completed_screenings'] = completed_screening_list 
    if request.session.get('custom_success_message'):
        context['message'] = {
            'success': request.session.get('custom_success_message')
        }
        del request.session['custom_success_message']
    return render(request, 'dashboard/patientDashboard.html', context)

@login_required_without_next
def allPatientsView(request):
    context = addUserProfileToContext({}, request.user)
    if not context['user_profile'].isDoctor:
        return redirect('patientDashboard')
    doctor = Doctor.objects.get(user=request.user)
    patients_related_to_doctor = doctor.patients.all()
    patients_profile = []
    for patient in patients_related_to_doctor:
        patient_profile = UserProfile.objects.get(user=patient.user)
        patients_profile.append(patient_profile)
    context['patients'] = patients_profile
    return render(request, 'dashboard/doctorViewPatients.html', context)

@login_required_without_next
def individualPatientView(request, patient_id):
    context = addUserProfileToContext({}, request.user)
    if request.method == 'POST':
        if context['user_profile'].isDoctor:
            form = PatientVitalsForm(request.POST)
            if form.is_valid():
                patient_profile = UserProfile.objects.get(id=patient_id)
                patient = Patient.objects.get(user=patient_profile.user)
                patient.blood_pressure = form.cleaned_data['blood_pressure']
                patient.blood_sugar_level = form.cleaned_data['blood_sugar_level']
                patient.weight = form.cleaned_data['weight']
                patient.height = form.cleaned_data['height']
                patient.save()
                context['message'] = {
                    'success': 'Vitals updated successfully'
                }
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            patient_profile = UserProfile.objects.get(id=patient_id)
            patient_profile.phone_number = form.cleaned_data['phone_number']
            patient_profile.save()
            patient = Patient.objects.get(user=patient_profile.user)
            patient.address = form.cleaned_data['address']
            patient.date_of_birth = form.cleaned_data['date_of_birth']
            patient.gender = form.cleaned_data['gender']
            patient.is_call_mode_of_screening = form.cleaned_data['is_call_preferred']
            patient.save()
            context['message'] = {
                'success': 'Profile updated successfully'
            }
    if context['user_profile'].isDoctor:
        doctor = Doctor.objects.get(user=context['user_profile'].user)
        patient = Patient.objects.get(user__id=patient_id)
        if not doctor.patients.filter(id=patient.id).exists():
            return redirect('viewPatients')
    else:
        patient = Patient.objects.get(user=request.user)
        if int(patient.user.id) != int(patient_id):
            return redirect('patientDashboard')
    patient_profile = UserProfile.objects.get(id=patient_id)
    patient = Patient.objects.get(user=patient_profile.user)
    context['patient'] = patient
    if context['user_profile'].isDoctor:
        context['vitals_form'] = PatientVitalsForm(initial={
            'blood_pressure': patient.blood_pressure,
            'blood_sugar_level': patient.blood_sugar_level,
            'weight': patient.weight,
            'height': patient.height
        })
    else:
        context['basic_details_form'] = PatientProfileForm(initial={
            'phone_number': patient.user_profile.phone_number,
            'address': patient.address,
            'date_of_birth': patient.date_of_birth,
            'gender': patient.gender,
            'is_call_preferred': patient.is_call_mode_of_screening
        })
    context['related_doctors'] = Doctor.objects.filter(patients=patient)
    vitals = {
        'blood_pressure': patient.blood_pressure,
        'blood_sugar_level': patient.blood_sugar_level,
        'weight': patient.weight,
        'height' : patient.height
    }
    context['vitals'] = vitals
    health_conditions = HealthCondition.objects.filter(patient=patient)
    health_condition_list = []
    for health_condition in health_conditions:
        health_condition_list.append({
            'name': health_condition.name,
            'severity': health_condition.severity,
            'diagnosis_date': health_condition.diagnosis_date
        })
    context['health_conditions'] = health_condition_list
    medications = Medication.objects.filter(patient=patient)
    medication_list = []
    for medication in medications:
        medication_list.append({
            'name': medication.name,
            'frequency': medication.frequency
        })
    context['medications'] = medication_list
    return render(request, 'dashboard/patientProfile.html', context)

@login_required_without_next
def individualDoctorView(request, request_id):
    context = addUserProfileToContext({}, request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        if form.is_valid():
            doctor_profile = UserProfile.objects.get(id=request_id)
            doctor_profile.phone_number = form.cleaned_data['phone_number']
            doctor_profile.save()
            doctor = Doctor.objects.get(user=doctor_profile.user)
            doctor.institution = form.cleaned_data['institution']
            doctor.specialty = form.cleaned_data['specialty']
            doctor.save()
            context['message'] = {
                'success': 'Profile updated successfully'
            }
    doctor_profile = UserProfile.objects.get(id=request_id)
    doctor = Doctor.objects.get(user=doctor_profile.user)
    context['doctor'] = doctor
    context['is_same_doctor'] = doctor.user == request.user
    context['form'] = DoctorProfileForm(initial={
        'phone_number': doctor.user_profile.phone_number,
        'institution': doctor.institution,
        'specialty': doctor.specialty
    })
    return render(request, 'dashboard/doctorProfile.html', context)

@login_required_without_next
def viewScreeningRequestsView(request):
    context = addUserProfileToContext({}, request.user)
    doctor = Doctor.objects.get(user=request.user)
    screening_requests = ScreeningRequest.objects.filter(doctor=doctor)
    context['screenings'] = screening_requests
    return render(request, 'dashboard/doctorViewScreenings.html', context)

@login_required_without_next
def viewIndividualScreeningRequestView(request, request_id):
    context = addUserProfileToContext({}, request.user)
    screening_request = ScreeningRequest.objects.get(id=request_id)
    if screening_request.completion_date:
        if not context['user_profile'].isDoctor:
            conversation = json.loads(screening_request.conversation)
            conversation_list = []
            for i in range(len(conversation['user_messages'])):
                conversation_list.append({
                    'user_message': conversation['user_messages'][i]['message'],
                    'bot_message': conversation['bot_messages'][i]['message']
                })
            context['conversation'] = conversation_list
        else:
            doctor = Doctor.objects.get(user=request.user)
            if screening_request.doctor != doctor:
                return redirect('viewPatients')
            else:
                conversation = json.loads(screening_request.conversation)
                conversation_list = []
                for i in range(len(conversation['user_messages'])):
                    conversation_list.append({
                        'user_message': conversation['user_messages'][i]['message'],
                        'bot_message': conversation['bot_messages'][i]['message']
                    })
                context['conversation'] = conversation_list
    else:
        if not context['user_profile'].isDoctor:
            if screening_request.patient.is_call_mode_of_screening and screening_request.patient.user_profile.phone_number:
                fire_and_forget_async(
                    start_screening_call,
                    screening_request.id,
                    screening_request.patient.user_profile.phone_number,
                    f"I am calling on behalf of your healthcare provider, {screening_request.doctor.user_profile.first_name} {screening_request.doctor.user_profile.last_name}. Please tell me about your symptoms why you want to visit."
                )
                request.session['custom_success_message'] = "Screening request sent successfully"
                return redirect('patientDashboard')
    context['screening_request'] = screening_request
    return render(request, 'dashboard/viewScreening.html', context)

@login_required_without_next
def sendScreeningRequestView(request):
    context = addUserProfileToContext({}, request.user)
    logged_in_doctor = Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        form = ScreeningRequestForm(logged_in_doctor, request.POST)
        if form.is_valid():
            patient = form.cleaned_data['patient_choices']
            template = form.cleaned_data['template']
            due_date = form.cleaned_data['due_date']
            doctor = Doctor.objects.get(user=request.user)
            screening_request = ScreeningRequest.objects.create(
                patient=patient,
                doctor=doctor,
                template=template,
                due_date=due_date
            )
            screening_request.save()
            if patient.is_call_mode_of_screening and patient.user_profile.phone_number:
                fire_and_forget_async(
                    start_screening_call,
                    screening_request.id,
                    patient.user_profile.phone_number,
                    f"I am calling on behalf of your healthcare provider, {doctor.user_profile.first_name} {doctor.user_profile.last_name}. Please tell me about your symptoms why you want to visit."
                )
            context['message'] = {
                'success': 'Screening request sent successfully'
            }
    
    context['form'] = ScreeningRequestForm(doctor=logged_in_doctor)
    return render(request, 'dashboard/requestScreening.html', context)

def fire_and_forget_async(func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_until_complete, args=(func(*args, **kwargs),)).start()

@login_required_without_next
def logoutView(request):
    logout(request)
    return redirect('landing')

def getDoctorsForPatient(request, username):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)

    if request.method != 'GET':
        return errorResponse("You must use a GET request for this operation", status=405)

    if not username:
        return errorResponse("You must send all parameters.", status=400)
    
    non_related_doctors = Doctor.objects.exclude(patients__user__username=username)

    non_related_doctors_json = []

    for doctor in non_related_doctors:
        doctor_profile = UserProfile.objects.get(user=doctor.user)
        non_related_doctors_json.append({
            'first_name': doctor_profile.first_name,
            'last_name': doctor_profile.last_name,
            'id': doctor_profile.id
        })

    response = {'non_related_doctors': non_related_doctors_json}
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)
        
def addDoctorToPatient(request):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)

    if request.method != 'POST':
        return errorResponse("You must use a POST request for this operation", status=405)

    if not 'patient_username' in request.POST or not request.POST['patient_username'] or not 'doctor_id' in request.POST or not request.POST['doctor_id']:
        return errorResponse("You must send all parameters.", status=400)

    patient = Patient.objects.get(user__username=request.POST['patient_username'])
    doctor = Doctor.objects.get(user_profile__id=request.POST['doctor_id'])
    doctor.patients.add(patient)
    doctor.save()
    response = {"success": "Doctor added to patient successfully"}
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)

def addHealthCondition(request):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)

    if request.method != 'POST':
        return errorResponse("You must use a POST request for this operation", status=405)

    if not 'condition_name' in request.POST or not request.POST['condition_name'] or not 'condition_severity' in request.POST or not request.POST['condition_severity'] or not 'condition_date' in request.POST or not request.POST['condition_date'] or not 'patient_id' in request.POST or not request.POST['patient_id']:
        return errorResponse("You must send all parameters.", status=400)
    
    patient = Patient.objects.get(user_profile__id=request.POST['patient_id'])
    health_condition = HealthCondition.objects.create(
        patient=patient,
        name=request.POST['condition_name'],
        severity=request.POST['condition_severity'],
        diagnosis_date=request.POST['condition_date']
    )
    health_condition.save()

    return HttpResponse(json.dumps({"success": "Health condition added successfully"}), content_type='application/json', status=200)

def addMedication(request):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)

    if request.method != 'POST':
        return errorResponse("You must use a POST request for this operation", status=405)

    if not 'medication_name' in request.POST or not request.POST['medication_name'] or not 'medication_frequency' in request.POST or not request.POST['medication_frequency'] or not 'patient_id' in request.POST or not request.POST['patient_id']:
        return errorResponse("You must send all parameters.", status=400)
    
    patient = Patient.objects.get(user_profile__id=request.POST['patient_id'])
    medication = Medication.objects.create(
        patient=patient,
        name=request.POST['medication_name'],
        frequency=request.POST['medication_frequency']
    )
    medication.save()

    return HttpResponse(json.dumps({"success": "Medication added successfully"}), content_type='application/json', status=200)

def removeDoctor(request):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)
    
    if request.method != 'POST':
        return errorResponse("You must use a POST request for this operation", status=405)
    
    if not 'patient_id' in request.POST or not request.POST['patient_id'] or not 'doctor_id' in request.POST or not request.POST['doctor_id']:
        return errorResponse("You must send all parameters.", status=400)
    
    patient = Patient.objects.get(user_profile__id=request.POST['patient_id'])
    doctor = Doctor.objects.get(id=request.POST['doctor_id'])
    doctor.patients.remove(patient)
    doctor.save()
    response = {"success": "Doctor removed from patient successfully"}
    return HttpResponse(json.dumps(response), content_type='application/json', status=200)

@login_required_without_next
def createTemplate(request):
    context = {}
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            user = request.user
            doctor = Doctor.objects.get(user=user)
            template = ScreeningTemplate.objects.create(
                doctor=doctor,
                name=form.cleaned_data['name'],
                question1=form.cleaned_data['question1'],
                question2=form.cleaned_data['question2'],
                question3=form.cleaned_data['question3'],
                question4=form.cleaned_data['question4'],
                question5=form.cleaned_data['question5']
            )
            template.save()
            context['message'] = {'success' : 'Template created successfully'}
    context['form'] = TemplateForm()
    return render(request, "dashboard/createTemplate.html", context)

def landingView(request):
    context = {}
    return render(request, 'dashboard/landing.html', context)

def sendChatConversation(request):
    if not request.user.is_authenticated:
        return errorResponse("You must be logged in to do this operation", status=401)
    
    if request.method != 'POST':
        return errorResponse("You must use a POST request for this operation", status=405)

    if not 'message' in request.POST or not request.POST['message'] or not 'patient_id' in request.POST or not request.POST['patient_id'] or not 'screening_id' in request.POST or not request.POST['screening_id']:
        return errorResponse("You must send all parameters.", status=400)

    patient = Patient.objects.get(id=request.POST['patient_id'])
    screening_request = ScreeningRequest.objects.get(id=request.POST['screening_id'])

    if screening_request.patient != patient:
        return errorResponse("You are not allowed to send messages for this patient", status=403)

    if screening_request.completion_date:
        return errorResponse("You cannot send messages to this patient anymore", status=403)

    hasConversationEnded = False
    template = screening_request.template

    template_questions = '''
    \n1. {question1}
    \n2. {question2}
    \n3. {question3}
    \n4. {question4}
    \n5. {question5}
    '''.format(
        question1=template.question1,
        question2=template.question2,
        question3=template.question3,
        question4=template.question4,
        question5=template.question5
    )
    if not screening_request.conversation:
        conversation = {"user_messages": [], "bot_messages": [{'message': "Welcome! Let's start your screening. What's your full name?", 'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")},]}
    else:
        conversation = json.loads(screening_request.conversation)
    conversation['user_messages'].append({
        'message': request.POST['message'],
        'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    if request.POST['message'].strip().lower() == "stop":
        bot_message = "This is a bot message indicating the conversation has ended."
        summary = summarize_conversation(conversation)
        screening_request.completion_date = timezone.now()
        screening_request.summary = summary
        hasConversationEnded = True
    else:
        bot_message = generate_openai_followup(conversation, template_questions)

    conversation['bot_messages'].append({
        'message': bot_message,
        'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    screening_request.conversation = json.dumps(conversation)
    screening_request.save()
    return HttpResponse(json.dumps({"success": "Message sent successfully", "response_text": bot_message, "has_conversation_ended": hasConversationEnded}), content_type='application/json', status=200)
