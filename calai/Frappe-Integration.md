# Cal.com (Calai) to Frappe Integration Strategy

This document outlines how the newly deployed Cal.diy Kubernetes application integrates with the Frappe microservice cluster.

## Architecture

![Architecture diagram visualizing Calai to Frappe Webhook integration](https://cal.com/images/branding/brandbook/brandmark-dark.png)

1. **Calai** resides in the `calai` namespace.
2. **Frappe** resides in the `frappe` namespace.
3. Due to strict **NetworkPolicies**, the `calai` pods are only allowed outbound access to the DNS server, external internet (for sending emails/processing calendars), and the specific `frappe` service on port `8000`.
4. The integration relies on **intra-cluster webhooks**. Cal.diy directly issues HTTP POST requests to `http://frappe-service.frappe.svc.cluster.local:8000/api/method/calai.webhooks.receive`.

## Security Protocols

Because these are incoming HTTP requests, they theoretically bypass standard Frappe authentication. Therefore, we use **HMAC-SHA256 Signatures**:

- Cal.diy signs every webhook request using a secret key.
- This secret is stored in Kubernetes secrets as `frappeWebhookHmacSecret` and injected into Cal.diy.
- The same secret must be stored securely in Frappe.
- Frappe intercepts the webhook, recalculates the HMAC of the raw payload using the secret, and compares it to the `X-Cal-Signature-256` header.

## Frappe Implementation Snippet

In your Frappe app (`calai` integration app), you need a whitelisted method:

```python
import frappe
import hmac
import hashlib
import json

@frappe.whitelist(allow_guest=True)
def receive():
    # 1. Fetch the raw payload
    raw_data = frappe.request.get_data()
    
    # 2. Extract signature from headers
    signature = frappe.get_request_header('X-Cal-Signature-256')
    if not signature:
        frappe.throw("Missing signature", frappe.PermissionError)

    # 3. Calculate expected signature
    secret = frappe.conf.get("cal_webhook_secret")
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        raw_data,
        hashlib.sha256
    ).hexdigest()

    # 4. Compare
    if not hmac.compare_digest(expected_signature, signature):
        frappe.throw("Invalid signature", frappe.PermissionError)

    # 5. Process Payload
    payload = json.loads(raw_data)
    event_type = payload.get('triggerEvent')
    
    if event_type == 'BOOKING_CREATED':
        process_booking_created(payload.get('payload'))
        
    return "OK"
```

## Configuring Cal.diy Webhooks

1. Login to Cal.diy at `https://cal.atxinvox.com.au` as admin.
2. Navigate to **Settings** > **Webhooks**.
3. Create a new Webhook:
   - **Subscriber URL**: `http://frappe-service.frappe.svc.cluster.local:8000/api/method/calai.webhooks.receive`
   - **Secret**: Match the value specified in your Kubernetes secret (default is `change-me-in-production`).
   - select requested events: `Booking Created`, `Booking Cancelled`, `Booking Rescheduled`.
