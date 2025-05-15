
from django.urls import path
from . import views

urlpatterns = [
    path('registerPatient/', views.registerPatientView, name='registerPatient'),
    path('registerDoctor/', views.registerDoctorView, name='registerDoctor'),
    path('login/', views.loginView, name='login'),
    path('', views.landingView, name='home'),
    path('dashboard/', views.dashboardView, name='dashboard'),
    path('viewPatients/', views.allPatientsView, name='viewPatients'),
    path('viewPatient/<int:patient_id>/', views.individualPatientView, name='viewPatient'),
    path('doctorProfile/<int:request_id>/', views.individualDoctorView, name='doctorProfile'),
    path('viewScreeningRequests/', views.viewScreeningRequestsView, name='viewScreeningRequests'),
    path('viewScreeningRequest/<int:request_id>/', views.viewIndividualScreeningRequestView, name='viewScreeningRequest'),
    path('sendScreeningRequest/', views.sendScreeningRequestView, name='sendScreeningRequest'),
    path('patientDashboard/', views.patientDashboardView, name='patientDashboard'),
    path('oauthComplete/', views.oauthRedirectView, name="oauthComplete"),
    path('logout/', views.logoutView, name='logout'),
    path('api/get-doctors/<str:username>/', views.getDoctorsForPatient, name='getDoctorsForPatient'),
    path('api/addDoctorToPatient/', views.addDoctorToPatient, name='addDoctorToPatient'),
    path('api/addCondition/', views.addHealthCondition, name='addHealthCondition'),
    path('api/addMedication/', views.addMedication, name='addMedication'),
    path('api/removeDoctor/', views.removeDoctor, name='removeDoctor'),
    path('createTemplate/', views.createTemplate, name="createTemplate"),
    path('api/sendChatConversation/', views.sendChatConversation, name='sendChatConversation'),
    path('landing/', views.landingView, name='landing'),
]