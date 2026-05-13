import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "database" in body
    assert "enabled" in body["database"]
    if body["database"]["enabled"]:
        assert body["database"]["reachable"] in (True, False)
    else:
        assert body["database"]["reachable"] is None
