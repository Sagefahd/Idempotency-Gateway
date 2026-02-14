import hashlib
import json
import time
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="Idempotency Gateway")


idempotency_store: Dict[str, Dict[str, Any]] = {}

# TTL in seconds (20 seconds for testing)
TTL_SECONDS = 20


# Models 

class PaymentRequest(BaseModel):
    amount: float
    currency: str




def hash_request_body(body: dict) -> str:
    body_str = json.dumps(body, sort_keys=True)
    return hashlib.sha256(body_str.encode()).hexdigest()


def is_expired(record: Dict[str, Any]) -> bool:
    return time.time() - record["created_at"] > TTL_SECONDS


def remove_if_expired(key: str):
    record = idempotency_store.get(key)
    if record and is_expired(record):
        del idempotency_store[key]



@app.post("/process-payment")
def process_payment(
    payment: PaymentRequest,
    response: Response,
    idempotency_key: Optional[str] = Header(None)
):

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required"
        )

    # Step 1: Clean expired record if needed
    remove_if_expired(idempotency_key)

    body_dict = payment.dict()
    request_hash = hash_request_body(body_dict)

    # Step 2: Check existing key
    if idempotency_key in idempotency_store:
        record = idempotency_store[idempotency_key]

        # Conflict if body differs
        if record["hash"] != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key already used for a different request body."
            )

        # If still processing
        if record["status"] == "processing":
            raise HTTPException(
                status_code=409,
                detail="Request is still processing. Please retry shortly."
            )

        # Return cached response
        response.headers["X-Cache-Hit"] = "true"
        return record["response"]

    # Step 3: Store as processing
    idempotency_store[idempotency_key] = {
        "status": "processing",
        "hash": request_hash,
        "response": None,
        "created_at": time.time()
    }

    # Simulate payment processing
    time.sleep(2)

    payment_response = {
        "message": f"Charged {payment.amount} {payment.currency}"
    }

    # Step 4: Mark completed
    idempotency_store[idempotency_key]["status"] = "completed"
    idempotency_store[idempotency_key]["response"] = payment_response

    return payment_response
