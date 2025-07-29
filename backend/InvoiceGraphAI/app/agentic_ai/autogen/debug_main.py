from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class QueryRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

@app.post("/query")
async def handle_query(request: Request):
    raw_body = await request.body()
    print(f"Raw request body bytes: {raw_body}")

    try:
        json_body = await request.json()
        print(f"Parsed JSON body: {json_body}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Use model_validate_json instead of deprecated parse_raw
    try:
        user_query = QueryRequest.model_validate_json(raw_body)
        print(f"Parsed Pydantic model: {user_query}")
    except Exception as e:
        print(f"Pydantic parsing error: {e}")
        raise HTTPException(status_code=422, detail=f"Pydantic validation error: {e}")

    return {
        "prompt": user_query.prompt,
        "session_id": user_query.session_id
    }
