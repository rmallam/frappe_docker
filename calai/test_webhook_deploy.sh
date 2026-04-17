#!/bin/bash
# test_webhook_deploy.sh
# Tests the Calai to Frappe webhook integration by generating a valid HMAC signature and calling the endpoint.

# Configuration
SECRET="change-me-in-production"
WEBHOOK_URL="http://localhost:8000/api/method/calai.webhooks.receive"
# WEBHOOK_URL="http://frappe-service.frappe.svc.cluster.local:8000/api/method/calai.webhooks.receive" # If running inside pod

# JSON Payload
PAYLOAD=$(cat <<EOF
{
  "triggerEvent": "BOOKING_CREATED",
  "createdAt": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "payload": {
    "type": "Booking",
    "title": "Strategy Session",
    "description": "Discussing ATXINVOX",
    "startTime": "2026-05-01T09:00:00Z",
    "endTime": "2026-05-01T10:00:00Z",
    "attendees": [
      {
        "email": "user@example.com",
        "name": "John Doe"
      }
    ]
  }
}
EOF
)

# Calculate HMAC SHA256 Signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $NF}')

echo "Generated Signature: $SIGNATURE"
echo "Sending Webhook to $WEBHOOK_URL..."

# Send the request
curl -X POST "$WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -H "X-Cal-Signature-256: $SIGNATURE" \
     -d "$PAYLOAD"

echo -e "\n\nWebhook test complete."
