# SPIA — Stripe Checkout Integration
# This is a placeholder backend endpoint for processing payments.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import secrets

router = APIRouter(prefix="/api/v1/checkout", tags=["checkout"])

STRIPE_SECRET_KEY = ""  # Set via env: STRIPE_SECRET_KEY
STRIPE_PRICE_IDS = {
    "pro": "price_XXXXXXXXXXXX",       # Replace with real Stripe Price ID
    "enterprise": "price_XXXXXXXXXXXX", # Replace with real Stripe Price ID
}


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "enterprise"
    email: str


@router.post("/create-session")
async def create_checkout_session(body: CheckoutRequest):
    """Create a Stripe Checkout session. Requires STRIPE_SECRET_KEY env var."""
    import os
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", STRIPE_SECRET_KEY)

    if not stripe_key or stripe_key == "":
        raise HTTPException(
            status_code=501,
            detail="Payment processing not configured. Set STRIPE_SECRET_KEY env var."
        )

    if body.plan not in STRIPE_PRICE_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {body.plan}")

    try:
        import stripe
        stripe.api_key = stripe_key

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_IDS[body.plan],
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://yourdomain.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://yourdomain.com/pricing",
            customer_email=body.email,
            metadata={"plan": body.plan},
        )
        return {"url": session.url}

    except ImportError:
        raise HTTPException(status_code=501, detail="Install stripe: pip install stripe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook():
    """Stripe webhook handler — generates license key on successful payment."""
    # When payment succeeds, call: python tools/generate_license.py {plan}
    # and email the key to the customer.
    return {"status": "ok", "message": "Webhook placeholder"}
