from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import sqlite3
from contextlib import closing
import uuid
from datetime import datetime
import os

app = Flask(__name__)

# ================= OPENAI ================= #
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ================= DATABASE ================= #
DB_NAME = "payments.db"


def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db()) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            service TEXT NOT NULL,
            mpesa_code TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()


init_db()

# ================= PAGES ================= #
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ================= MANUAL PAYMENT ================= #
@app.route("/pay", methods=["GET", "POST"])
def pay():

    if request.method == "POST":

        try:
            # SAFE FORM HANDLING
            phone = request.form.get("phone", "").strip()
            amount = request.form.get("amount", "").strip()
            service = request.form.get("service", "").strip()
            mpesa_code = request.form.get("mpesa_code", "").strip()

            # VALIDATION
            if not all([phone, amount, service, mpesa_code]):
                return jsonify({
                    "status": "error",
                    "message": "All fields are required"
                }), 400

            # Convert amount safely
            try:
                amount = int(amount)
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Amount must be a valid number"
                }), 400

            tx_id = str(uuid.uuid4())

            with closing(get_db()) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO transactions
                    (id, phone, amount, service, mpesa_code, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx_id,
                    phone,
                    amount,
                    service,
                    mpesa_code,
                    "PENDING VERIFICATION",
                    datetime.now().isoformat()
                ))

                conn.commit()

            return jsonify({
                "status": "success",
                "message": "Payment submitted successfully and pending verification",
                "transaction_id": tx_id
            })

        except Exception as e:
            print("PAYMENT ERROR:", e)

            return jsonify({
                "status": "error",
                "message": "Server error occurred"
            }), 500

    return render_template("pay.html")


# ================= AI ASSISTANT ================= #
@app.route("/assistant", methods=["POST"])
def assistant():

    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({
                "reply": "Please send a valid message."
            }), 400

        user_message = data["message"].strip()

        if not user_message:
            return jsonify({
                "reply": "Message cannot be empty."
            }), 400

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Chris Online Cyber Assistant. "
                        "Provide short, clear, professional responses for cyber services, KRA, eCitizen, CV writing, IT support."
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=200
        )

        return jsonify({
            "reply": response.choices[0].message.content
        })

    except Exception as e:
        print("OPENAI ERROR:", e)

        return jsonify({
            "reply": "Assistant temporarily unavailable. Please try again later."
        }), 500


# ================= RUN ================= #
if __name__ == "__main__":
    app.run(debug=True)