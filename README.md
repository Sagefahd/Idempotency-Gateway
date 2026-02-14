# Idempotency Gateway – Pay-Once Protocol

## Overview

This project implements an **Idempotency Gateway** for a payment processing system.
It guarantees that a payment request is processed **exactly once**, even if the client retries the same request multiple times due to network timeouts or failures.

The system prevents **double charging**, a critical issue in fintech systems, by using an `Idempotency-Key` supplied by the client.

This project is implemented as an **API-only service** (no frontend).

## Problem Statement

In payment systems, network issues may cause clients to retry requests.  
Without idempotency, this can lead to the **same payment being processed multiple times**, resulting in customer dissatisfaction and regulatory issues.

## Solution

The API enforces idempotency by:

- Requiring an `Idempotency-Key` for every payment request
- Storing the first successful response for each key
- Replaying the stored response for duplicate requests
- Rejecting requests that reuse a key with different payment data
- Handling concurrent (in-flight) duplicate requests safely

## Architecture Diagram

The system follows a request-validation and caching flow:

- Clients send a payment request with an `Idempotency-Key`
- The server checks if the key already exists
- If the request was processed before, the cached response is returned
- If the same key is reused with a different payload, the request is rejected
- TTL (Time-To-Live) prevents stale records from living forever (Developer's choice)

## API Documentation

Interactive documentation is available when the server is running:
run **uvicorn main:app --reload** to run server

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

A Postman collection is included in this repository for testing.

## A full flowchart is included in this repository as a **draw.io diagram**.

flowchart TD
A[Client sends POST /process-payment] --> B{Idempotency-Key present?}

    B -- No --> C[Return 400 Bad Request]
    B -- Yes --> D[Hash Request Body]

    D --> E{Key exists in store?}

    E -- No --> F[Store key as PROCESSING]
    F --> G[Simulate payment (2s)]
    G --> H[Store response as COMPLETED]
    H --> I[Return 201 Success]

    E -- Yes --> J{TTL expired?}
    J -- Yes --> K[Delete old record]
    K --> F

    J -- No --> L{Request hash matches?}
    L -- No --> M[Return 409 Conflict]

    L -- Yes --> N{Status = PROCESSING?}
    N -- Yes --> O[Return 409 Still Processing]

    N -- No --> P[Return cached response]
    P --> Q[X-Cache-Hit: true]

## Technology Stack

- **FastAPI** – Lightweight, fast REST API framework
- **Python 3.9+**
- **In-memory dictionary** (simulates Redis)
- **Uvicorn** – ASGI server

## Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone <my-forked-repo-url>
cd Idempotency-Gateway
```
