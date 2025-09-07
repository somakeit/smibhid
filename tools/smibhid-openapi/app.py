from fastapi import FastAPI
from api import api_router

app = FastAPI(
    title="S.M.I.B.H.I.D. OpenAPI",
    description="S.M.I.B.H.I.D. OpenAPI",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_tags=[
        {
            "name": "System",
            "description": "System information"
        }
    ]
)

app.include_router(api_router)
print(app.openapi())