import json
from pprint import pprint

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from api import api_router

app = FastAPI(
    title="S.M.I.B.H.I.D. OpenAPI",
    description="S.M.I.B.H.I.D. OpenAPI",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    servers=None,
    openapi_tags=[
        {
            "name": "System",
            "description": "System information"
        },
        {
            "name": "Firmware Files",
            "description": "Firmware Files Update"
        },
        {
            "name": "Sensors",
            "description": "Sensor information"
        }
    ]
)

app.include_router(api_router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = app.openapi()

    # Remove 422 responses only if their schema $ref is HTTPValidationError
    for _, path_item in schema.get("paths", {}).items():
        for _, operation in path_item.items():
            responses = operation.get("responses", {})
            resp_422 = responses.get("422")
            if not resp_422:
                continue
            content = resp_422.get("content", {})
            should_delete = False
            for media, media_obj in content.items():
                schema_obj = media_obj.get("schema", {})
                ref = schema_obj.get("$ref")
                if ref == "#/components/schemas/HTTPValidationError":
                    should_delete = True
                    break
            if should_delete:
                del responses["422"]

    # Optionally remove HTTPValidationError/ValidationError schemas
    # only if no remaining references exist in the document
    def has_ref_to(ref_target: str) -> bool:
        # Walk paths
        for _, p in schema.get("paths", {}).items():
            for _, op in p.items():
                for resp in op.get("responses", {}).values():
                    for media_obj in resp.get("content", {}).values():
                        sch = media_obj.get("schema", {})
                        if sch.get("$ref") == ref_target:
                            return True
        # Also check requestBodies
        for _, p in schema.get("paths", {}).items():
            for _, op in p.items():
                rb = op.get("requestBody", {})
                for media_obj in rb.get("content", {}).values():
                    sch = media_obj.get("schema", {})
                    if sch.get("$ref") == ref_target:
                        return True
        return False

    schemas = schema.get("components", {}).get("schemas", {})
    for name in ("HTTPValidationError", "ValidationError"):
        ref_target = f"#/components/schemas/{name}"
        if name in schemas and not has_ref_to(ref_target):
            del schemas[name]

    app.openapi_schema = schema
    print(app.openapi())
    return schema

print(json.dumps(custom_openapi()))
print(get_swagger_ui_html(openapi_url="/openapi.json", title="docs").body.decode())