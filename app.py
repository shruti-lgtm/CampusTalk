import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import base64
import os

st.set_page_config(page_title="CampusTalk", page_icon="💬", layout="centered")


def set_bg_image(image_file):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, image_file)

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        .block-container {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg_image("background.jpg")

# ---------------- MongoDB Connection ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["chat_app"]
users_col = db["users"]
messages_col = db["messages"]

# ---------------- Session State ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- Helper Functions ----------------
def register_user(username, password):
    if users_col.find_one({"username": username}):
        return False
    users_col.insert_one({"username": username, "password": password})
    return True

def login_user(username, password):
    return users_col.find_one({"username": username, "password": password})

def send_message(sender, receiver, message):
    messages_col.insert_one({
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def get_messages(user, other_user):
    return list(
        messages_col.find({
            "$or": [
                {"sender": user, "receiver": other_user},
                {"sender": other_user, "receiver": user}
            ]
        }).sort("timestamp", 1)
    )


st.markdown("""
<style>
.chat-container {
    display: flex;
    flex-direction: column;
}

.chat-bubble {
    max-width: 70%;
    padding: 10px 14px;
    border-radius: 12px;
    margin: 6px 0;
    font-size: 15px;
}

.chat-left {
    align-self: flex-start;
    background-color: #FFC0CB; /* light pink for your messages */
    text-align: left;
}

.chat-right {
    align-self: flex-end;
    background-color: #ADD8E6; /* light blue for incoming messages */
    text-align: right;
}

.chat-user {
    font-weight: bold;
    font-size: 13px;
}

.chat-time {
    font-size: 11px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UI ----------------
st.markdown('<h1 style="color:black;">🎓 CampusTalk</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="color:black;">Web Based Chat App using Python, Streamlit & MongoDB</h3>', unsafe_allow_html=True)

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- Register ----------------
if choice == "Register":
    st.markdown('<h3 style="color:black;">📝 Create New Account</h3>', unsafe_allow_html=True)
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        if not new_user or not new_pass:
            st.error("All fields are required")
        elif register_user(new_user, new_pass):
            st.success("Registration successful! Go to Login.")
        else:
            st.error("Username already exists")

# ---------------- Login ----------------
elif choice == "Login":
    st.markdown('<h3 style="color:black;">🔐 Login to CampusTalk</h3>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            st.session_state.user = username
            st.success(f"Welcome {username} 👋")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------------- Chat Area ----------------
if st.session_state.user:
    st.markdown("---")
    st.markdown(
        f'<h3 style="color:black;">💬 Chat Room (Logged in as {st.session_state.user})</h3>',
        unsafe_allow_html=True
    )

    # Recipient selection
    all_users = [
        u["username"] for u in users_col.find()
        if u["username"] != st.session_state.user
    ]

    if all_users:
        recipient = st.selectbox("Send message to", all_users)
        message = st.text_input("Type your message")

        if st.button("Send"):
            if message.strip():
                send_message(st.session_state.user, recipient, message)
                st.success("Message sent ✔️")
                st.rerun()

        # ---------------- Chat History ----------------
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        messages = get_messages(st.session_state.user, recipient)

        for msg in messages:
            sender = msg["sender"]
            text = msg["message"]
            time = msg["timestamp"]

            if sender == st.session_state.user:
                # Your messages → LEFT (light pink)
                st.markdown(
                    f"""
                    <div class="chat-bubble chat-left">
                        {text}<br>
                        <span class="chat-time">{time}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Incoming messages → RIGHT (light blue)
                st.markdown(
                    f"""
                    <div class="chat-bubble chat-right">
                        <div class="chat-user">{sender}</div>
                        {text}<br>
                        <span class="chat-time">{time}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------- Export ----------------
        if st.button("📥 Export Chat to CSV"):
            df = pd.DataFrame(messages)
            df.to_csv("campustalk_chat.csv", index=False)
            st.success("Chat exported as campustalk_chat.csv")

    else:
        st.info("No other users available to chat with.")

    # ---------------- Logout ----------------
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()
