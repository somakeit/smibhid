from typing import Annotated, TypeAlias

from pydantic import Field, BaseModel, RootModel

# Use a proper type alias (no annotation on the LHS)
ModuleName: TypeAlias = Annotated[str, Field(examples=["SGP30", "BME280", "SCD30"])]

class Sensor(BaseModel):
    name: str
    module: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "pressure",
                    "unit": "hPa"
                },
                {
                    "name": "temperature",
                    "unit": "C"
                },
                {
                    "name": "humidity",
                    "unit": "%"
                }
            ]
        }
    }

SensorReading: TypeAlias = Annotated[dict[str, int | float], Field(examples=[{"temperature": 25.0}, {"pressure": 1013.25}])]
SensorDataMap: TypeAlias = Annotated[dict[ModuleName, SensorReading], Field(examples=[{"BME280":{"pressure":1017.6,"humidity":0,"temperature":26.6}}])]