from fastapi import FastAPI, Header, HTTPException, Response
import time
import hashlib
import json
from typing import Dict, Any

app = FastAPI(title="Idempotency Gateway API")


idempotency_store: Dict[str, Dict[str, Any]] = {}




def hash_request_body(body: dict) -> str:
    """
    Create a consistent hash of the request body.
    Ensures same request always produces same hash.
    """
    body_str = json.dumps(body, sort_keys=True)
    return hashlib.sha256(body_str.encode()).hexdigest()


def simulate_payment_processing(payload: dict) -> dict:
    """
    Simulates a real payment processor with delay.
    """
    time.sleep(2)
    return {
        "message": f"Charged {payload.get('amount')} {payload.get('currency')}"
    }




@app.post("/process-payment")
def process_payment(
    payload: dict,
    response: Response,
    idempotency_key: str = Header(None)
):
  
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required"
        )

   
    request_hash = hash_request_body(payload)

  
    if idempotency_key not in idempotency_store:
       
        idempotency_store[idempotency_key] = {
            "request_hash": request_hash,
            "status": "processing",
            "response": None
        }

    
        result = simulate_payment_processing(payload)

  
        idempotency_store[idempotency_key]["status"] = "completed"
        idempotency_store[idempotency_key]["response"] = {
            "status_code": 201,
            "body": result
        }

        response.status_code = 201
        return result


    record = idempotency_store[idempotency_key]

    if record["request_hash"] != request_hash:
        raise HTTPException(
            status_code=409,
            detail="Idempotency key already used for a different request body."
        )


    while record["status"] == "processing":
        time.sleep(0.1)

    # Return cached response
    response.headers["X-Cache-Hit"] = "true"
    response.status_code = record["response"]["status_code"]
    return record["response"]["body"]
