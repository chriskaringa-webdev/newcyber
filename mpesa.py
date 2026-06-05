import requests
import base64
import datetime
import os

from dotenv import load_dotenv

load_dotenv()

# ================= ENV VARIABLES ================= #

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")

SHORTCODE = os.getenv("SHORTCODE")
PASSKEY = os.getenv("PASSKEY")

CALLBACK_URL = os.getenv("CALLBACK_URL")

# ================= ACCESS TOKEN ================= #

def get_access_token():

    try:

        url = (
            "https://sandbox.safaricom.co.ke/"
            "oauth/v1/generate?grant_type=client_credentials"
        )

        response = requests.get(
            url,
            auth=(CONSUMER_KEY, CONSUMER_SECRET)
        )

        data = response.json()

        print("TOKEN RESPONSE:", data)

        return data.get("access_token")

    except Exception as e:

        print("ACCESS TOKEN ERROR:", e)

        return None


# ================= STK PUSH ================= #

def stk_push(phone, amount):

    try:

        phone = str(phone).strip()

        # FORMAT PHONE
        if phone.startswith("07"):
            phone = "254" + phone[1:]

        access_token = get_access_token()

        if not access_token:

            return {
                "error": "Failed to get access token"
            }

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        password = base64.b64encode(
            (
                SHORTCODE +
                PASSKEY +
                timestamp
            ).encode()
        ).decode()

        url = (
            "https://sandbox.safaricom.co.ke/"
            "mpesa/stkpush/v1/processrequest"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {

            "BusinessShortCode": SHORTCODE,

            "Password": password,

            "Timestamp": timestamp,

            "TransactionType": "CustomerPayBillOnline",

            "Amount": int(amount),

            "PartyA": phone,

            "PartyB": SHORTCODE,

            "PhoneNumber": phone,

            "CallBackURL": CALLBACK_URL,

            "AccountReference": "ChrisCyber",

            "TransactionDesc": "Payment"

        }

        print("========== STK PAYLOAD ==========")
        print(payload)

        response = requests.post(
            url,
            json=payload,
            headers=headers
        )

        result = response.json()

        print("========== STK RESPONSE ==========")
        print(result)

        return result

    except Exception as e:

        print("STK PUSH ERROR:", e)

        return {
            "error": str(e)
        }