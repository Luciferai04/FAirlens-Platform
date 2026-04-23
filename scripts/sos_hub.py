import time
import sys
import os
import requests
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "C0AULSEGZT7")

def send_slack_notification(model_id):
    if not SLACK_TOKEN:
        return
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL,
        "text": f"🚨 *FAIRLENS SOS ALERT* 🚨",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"🚨 *FAIRLENS SOS ALERT: PIPELINE BLOCKED* 🚨\n*Model*: `{model_id}`\n*Status*: CRITICAL BIAS DETECTED"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Reason*:\nDemographic Parity > 0.10"},
                    {"type": "mrkdwn", "text": "*Impact*:\n1.2M Users Affected"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Investigate in Console"},
                        "url": "http://localhost:5173/incidents",
                        "style": "danger"
                    }
                ]
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        if not res.json().get("ok"):
            print(f"[ERROR] Slack API Error: {res.json().get('error')}")
    except Exception as e:
        print(f"[ERROR] Failed to send Slack alert: {e}")

def run_sos_hub():
    print("\033[91m" + "="*60)
    print("   🚨 FAIRLENS SOS: REAL-TIME PIPELINE MONITOR 🚨")
    print("="*60 + "\033[0m")
    print("[SYSTEM] Listening for Fairness Gate SOS signals...")
    print("[SYSTEM] Webhook status: ACTIVE (Simulated)")
    
    try:
        while True:
            # In a real app, this would be a socket listener or webhook endpoint
            # For the demo, we will check for a 'SOS_SIGNAL' file
            import os
            if os.path.exists(".sos_signal"):
                with open(".sos_signal", "r") as f:
                    model_id = f.read().strip()
                
                print("\n" + "!"*60)
                print(f"\033[41m\033[37m 🔥 SOS ALERT: PIPELINE BLOCKED! \033[0m")
                print(f"\033[91m MODEL ID: {model_id}\033[0m")
                print(f"\033[91m REASON: Critical Bias Threshold Exceeded (DPD > 0.10)\033[0m")
                print(f"\033[91m IMPACT: Deployment halted for 1.2M users.\033[0m")
                print(f"\033[91m STATUS: Remediation Playbook Sent to On-Call Engineer.\033[0m")
                print("!"*60)
                
                # Send Real Slack Notification
                send_slack_notification(model_id)
                
                # Clear the signal
                os.remove(".sos_signal")
                
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SYSTEM] SOS Hub shutting down.")

if __name__ == "__main__":
    run_sos_hub()
