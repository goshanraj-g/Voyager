from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import openai
from dotenv import load_dotenv
import os

load_dotenv(PATH)


app = Flask(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
openai.api_key = os.getenv("OPENAI_API_KEY")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

conversation_context = {}

@app.route("/sms", methods=["POST"])
def sms_webhook():
    incoming_msg = request.form.get('Body')
    from_number = request.form.get('From')

    if from_number not in conversation_context:
        conversation_context[from_number] = []
    conversation_context[from_number].append({"role": "user", "content": incoming_msg})

    try:
        system_prompt = (
            "You are an online medical doctor. Based on the client's message, provide advice or information."
            "If the situation seems critical, extract the correct area code from the phone number (consider formats like +1 and digits accurately). For area codes 647, 416, or 437, recognize it as Toronto. Suggest nearby popular hospitals, including their names, phone numbers, and addresses, if possible. "
            "Only provide hospital details for severe cases. Respond concisely with all necessary details, formatted clearly and spaced appropriately."
            "Lastly, remember that you're going to give messages to a person, so make it catered towards that."
        )
        query_message = f"The user's phone number is {from_number}. Their message is: '{incoming_msg}'."

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query_message}
            ]
        )
        ai_response = response['choices'][0]['message']['content']
        conversation_context[from_number].append({"role": "assistant", "content": ai_response})
    except Exception as e:
        print(f"OpenAI error: {e}")
        ai_response = "Sorry, I couldn't process your message. Please try again later."

    print(f"Generated response: {ai_response}")

    twilio_response = MessagingResponse()
    twilio_response.message(ai_response)
    return Response(str(twilio_response), mimetype="text/xml")

if __name__ == "__main__":
    app.run(debug=True)
