import openai
from openai import OpenAI
from django.conf import settings
from django.http import HttpResponse
from .models import UserProfile, ScreeningRequest
from datetime import datetime
import requests
import time
import json

openai.api_key = settings.OPENAI_API_KEY
ASSEMBLY_API_KEY = "6df4aa17213c48b8aff3dfc1a57e78fc"

def saveConversationToDB(screening_id, conversation, summary):
    try:
        screening_request = ScreeningRequest.objects.get(id=screening_id)
        screening_request.conversation = json.dumps(conversation)
        screening_request.summary = summary
        screening_request.save()
        return True
    except ScreeningRequest.DoesNotExist:
        return False

def transcribe_with_speakers(file_path):
    headers = {"authorization": ASSEMBLY_API_KEY}
    
    with open(file_path, "rb") as f:
        upload_res = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, files={"file": f})
        audio_url = upload_res.json()["upload_url"]

    json_data = {
        "audio_url": audio_url,
        "speaker_labels": True
    }
    transcribe_res = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=json_data)
    transcript_id = transcribe_res.json()["id"]

    while True:
        status_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        result = status_res.json()
        if result["status"] == "completed":
            break
        elif result["status"] == "error":
            raise Exception("Transcription failed:", result["error"])
        time.sleep(3)
    return result["utterances"]

def completeScreeningRequest(screening_id):
    try:
        screening_request = ScreeningRequest.objects.get(id=screening_id)
        screening_request.completion_date = datetime.now()
        screening_request.save()
        return True
    except ScreeningRequest.DoesNotExist:
        return False

def errorResponse(message, status=200):
    response_json = '{"error": "' + message + '"}'
    return HttpResponse(response_json, content_type='application/json', status=status)

def addUserProfileToContext(context, user):
    user_profile = UserProfile.objects.get(user=user)
    context['user_profile'] = user_profile
    return context

def generate_openai_followup(conversation, template_questions):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    context_conversation = "\n".join(
        f"User: {user_msg['message']}\nBot: {bot_msg['message']}"
        for user_msg, bot_msg in zip(conversation["user_messages"], conversation["bot_messages"])
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical AI assistant helping in a patient screening process. I am giving you two contexts: the conversation that has taken place until now and also the template questions that are used to ask the patient. Based on these contexts, please provide the next best medical question to ask the patient. Also, please ensure to not repeat any of the questions that have already been asked and to end the conversation after you think all questions from the template have been answered. Don't prepend any text to the question like 'Next question is' or 'The next question is' or 'Bot: '"},
                {"role": "user", "content": "Template Questions:" + template_questions},
                {"role": "user", "content": "Conversation:" + context_conversation},
                {"role": "user", "content": "\n\nBased on the conversation and the template questions, what would be the next best medical question to ask? Please ensure the question is related to the patient's health and is not a repeat of any previous questions. Please also ensure that the question is not too short and is a complete sentence. Please also ensure that the question is not too vague and is specific to the patient's health. You also need to end the conversation after you think all questions from the template have been answered. The response should contain an acknowledgement of the last response from the patient and also include the question."}
            ],
            max_tokens=100
        )
        
        return completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "I'm sorry, I couldn't process your request at the moment."

def summarize_conversation(conversation):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    context_conversation = "\n".join(
        f"User: {user_msg['message']}\nBot: {bot_msg['message']}"
        for user_msg, bot_msg in zip(conversation["user_messages"], conversation["bot_messages"])
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical AI assistant helping in a patient screening process. I am giving you the conversation that has taken place until now. Based on this context, please summarize the conversation. This summary will be fed to a doctor to help them understand the patient's health. Please ensure that the summary is long enough to cover all the important points and also will have a structure which will give the complaints and the suggestive diagnosis."},
                {"role": "user", "content": "Conversation:" + context_conversation}
            ],
            max_tokens=100
        )
        
        return completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Unexpected error: {e}")
        return "I'm sorry, I couldn't process your request at the moment."
