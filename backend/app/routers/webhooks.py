import json
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.gateways.razorpay import get_razorpay
from app.services import webhooks as wh

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay webhook receiver.

    Must return 2xx quickly. Signature is verified against the RAW body.
    """
    raw = await request.body()
    try:
        payload = json.loads(raw.decode() or "{}")
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")

    gateway = get_razorpay()
    valid = gateway.verify_webhook(dict(request.headers), raw)

    evt = wh.persist_event(db, gateway="razorpay",
                           signature_valid=valid, payload=payload)
    # Process inline for MVP (in prod: enqueue to worker)
    wh.process_event(db, evt)

    return {"ok": True, "event_id": str(evt.id),
            "signature_valid": valid, "status": evt.process_status}
