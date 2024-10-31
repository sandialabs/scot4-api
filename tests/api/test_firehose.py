import time
import pytest
import json

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from async_asgi_testclient import TestClient as AsyncClient

from app.main import app
from app.enums import TargetTypeEnum
from app.core.config import settings

from tests.utils.user import create_random_user


def do_work(db, faker, client, superuser_token_headers):
    time.sleep(5)
    user = create_random_user(db, faker)
    alert_data = faker.pydict(value_types=[str])
    data = {"alert": {"owner": user.email, "data": alert_data}}
    r = client.post(
        f"{settings.API_V1_STR}/alert/",
        headers=superuser_token_headers,
        json=data,
    )
    return r.json()


@pytest.mark.asyncio
async def test_async_stream_audits(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(do_work, db, faker, client, superuser_token_headers)

        events = []
        async with AsyncClient(app) as async_client:
            r = await async_client.get(f"{settings.API_V1_STR}/firehose/", headers=normal_user_token_headers, stream=True)
            assert r.status_code == 200
            i = 0
            async for line in r.iter_content(100000):
                try:
                    events.append(json.loads(line.replace(b"data: ", b"").strip()))
                except Exception:
                    pass
                if i > 3:
                    break
                i += 1

        alert = future.result()

        assert len(events) != 0
        assert any(i["what"] == "create" and i["element_type"] == TargetTypeEnum.alert.value and i["element_id"] == alert["id"] for i in events)
