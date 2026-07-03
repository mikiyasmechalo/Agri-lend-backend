# Internal API contract with Eyosiyas (geospatial pipeline)
# This service consumes structured geospatial data (NDVI, climate layers).

from app.core.config import settings
import httpx


class GeospatialService:
    def __init__(self):
        self.base_url = settings.eyosiyas_service_url
        self.client = httpx.AsyncClient(timeout=30)

    async def get_ndvi_timeseries(self, parcel_id: str, days: int = 90) -> list[dict]:
        response = await self.client.get(
            f"{self.base_url}/api/v1/ndvi/{parcel_id}",
            params={"days": days},
        )
        response.raise_for_status()
        return response.json()

    async def get_climate_data(self, parcel_id: str) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/v1/climate/{parcel_id}",
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
