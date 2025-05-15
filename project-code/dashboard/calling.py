from twilio.rest import Client
import time
import asyncio
from .helper import completeScreeningRequest, transcribe_with_speakers, summarize_conversation, saveConversationToDB
from asgiref.sync import sync_to_async
import requests
import os

TWILIO_SID = "ACd1f17060e796f1c9b9c014761a2b310e"
TWILIO_AUTH_TOKEN = "b244e89fb8d350d7d0dcb0f206fdafc0"
TWILIO_FROM = "+14127252215"
GPT_MODEL = "gpt-4"

def download_twilio_recording(recording_sid, screening_id):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    recording = client.recordings(recording_sid).fetch()

    recording_uri = recording.uri.replace('.json', '.mp3')
    audio_url = f"https://api.twilio.com{recording_uri}"

    response = requests.get(audio_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN))

    if response.status_code == 200:
        with open(f"{recording_sid}.mp3", "wb") as f:
            f.write(response.content)
        print(f"✅ Recording downloaded: {recording_sid}.mp3")
        utterances = transcribe_with_speakers(f"{recording_sid}.mp3")
        os.remove(f"{recording_sid}.mp3")
        conversation = {
            "bot_messages": [],
            "user_messages": []
        }
        for speech in utterances:
            if speech["speaker"] == "A":
                conversation["bot_messages"].append({
                    'message': speech["text"]
                })
            elif speech["speaker"] == "B":
                conversation["user_messages"].append({
                    'message': speech["text"]
                })
        if len(conversation["user_messages"]) == 0:
            return False
        summary = summarize_conversation(conversation)
        saveConversationToDB(screening_id, conversation, summary)
        return True
    else:
        print(f"❌ Failed to download: {response.status_code} - {response.text}")
        return False

async def start_screening_call(screening_id, to_number: str, initial_goal: str):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    print("\n[*] Placing call to patient... on number:", to_number + " with goal:", initial_goal)
    call = client.calls.create(
        to=to_number,
        from_=TWILIO_FROM,
        twiml=f"""
        <Response>
            <Say voice="alice">Hi! I'm your virtual assistant.</Say>
            <Gather input="speech" timeout="5" action="https://patientscreening.pythonanywhere.com/handle_speech">
                <Say>{initial_goal}</Say>
            </Gather>
            <Say>Thank you. Goodbye!</Say>
        </Response>
        """,
        record=True
    )

    call_sid = call.sid
    print(f"[+] Call initiated, SID: {call_sid}")

    print("[*] Waiting for call to complete...")
    while True:
        call = client.calls(call_sid).fetch()
        if call.status in ["completed", "canceled", "failed", "busy", "no-answer"]:
            break
        time.sleep(2)
    if call.status == "completed":
        time.sleep(10)
        was_call_answered = await sync_to_async(download_twilio_recording)(call.recordings.list()[0].sid, screening_id)
        if was_call_answered:
            print("[+] Call answered and recording processed.")
            await sync_to_async(completeScreeningRequest)(screening_id)
        else:
            print("[+] Call was not answered or recording was not processed.")
    print(f"[+] Call ended with status: {call.status}\n")