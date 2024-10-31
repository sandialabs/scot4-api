import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TlpEnum, TargetTypeEnum, EntryClassEnum
from app.core.config import settings

from tests.utils.product import create_random_product
from tests.utils.user import create_random_user
from tests.utils.entry import create_random_entry
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.intel import create_random_intel
from tests.utils.promotion import promote_intel_to_product


def test_get_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, False)

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/product/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data is not None
    assert product_data["id"] == product.id


def test_create_product(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    data = {
        "owner": user.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "subject": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/product",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data is not None
    assert product_data["id"] > 0
    assert product_data["subject"] == data["subject"]


def test_update_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/product/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data is not None
    assert product_data["id"] == product.id
    assert product_data["subject"] == data["subject"]
    assert product_data["subject"] != product.subject


def test_delete_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/product/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data is not None
    assert product_data["id"] == product.id

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/product/undelete?target_id={product.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/undelete?target_id={product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data is not None
    assert product_data["id"] == product.id


def test_entries_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, False)
    entry = create_random_entry(db, faker, user.username, target_type=TargetTypeEnum.product, target_id=product.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/product/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_product(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = create_random_product(db, faker, owner.username, False)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/tag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_product = r.json()
    assert any([i for i in tag_product["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/untag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_product = r.json()
    assert tag_product["tags"] == []


def test_source_add_remove_product(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = create_random_product(db, faker, owner.username, False)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/add-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_product = r.json()
    assert any([i for i in source_product["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/remove-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/{-1}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/product/{product.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_product = r.json()
    assert source_product["sources"] == []


def test_entities_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = create_random_product(db, faker, owner.username, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.product, product.id)

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/product/{-1}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = create_random_product(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/product/{product.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/product/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_data = r.json()
    assert product_data == []

    r = client.get(
        f"{settings.API_V1_STR}/product/{product.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in product_data)
    assert product_data[0]["audit_data"]["subject"] == data["subject"]


def test_search_product(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    products = []
    for _ in range(5):
        products.append(create_random_product(db, faker, owner.username, False))

    random_product = random.choice(products)

    r = client.get(
        f"{settings.API_V1_STR}/product/?id={random_product.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    product_search = r.json()
    assert product_search is not None
    assert product_search["result"] == []

    random_product = random.choice(products)

    r = client.get(
        f"{settings.API_V1_STR}/product/?id={random_product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_search = r.json()
    assert product_search is not None
    assert product_search["totalCount"] == 1
    assert any(i["id"] == random_product.id for i in product_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    product_search = r.json()
    assert product_search is not None
    assert product_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/product/?id=!{random_product.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_product.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/product/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/product/?id=({products[0].id},{products[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == products[0].id
    assert r.json()["result"][3]["id"] == products[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/product/?id=!({products[0].id},{products[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != products[0].id for a in r.json()["result"])
    assert any(a["id"] != products[1].id for a in r.json()["result"])
    assert any(a["id"] != products[2].id for a in r.json()["result"])
    assert any(a["id"] != products[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/product/?id=[{products[0].id},{products[4].id},{products[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == products[0].id
    assert r.json()["result"][1]["id"] == products[2].id
    assert r.json()["result"][2]["id"] == products[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/product/?id=![{products[0].id},{products[4].id},{products[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != products[0].id for a in r.json()["result"])
    assert all(a["id"] != products[2].id for a in r.json()["result"])
    assert all(a["id"] != products[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.product, random_product.id)

    r = client.get(
        f"{settings.API_V1_STR}/product/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_product.id

    r = client.get(
        f"{settings.API_V1_STR}/product/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_product.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.product, random_product.id)

    r = client.get(
        f"{settings.API_V1_STR}/product/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_product.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_product.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?tlp={random_product.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_product.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/product/?subject={random_product.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_product.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?entry_count={random_product.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_product.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/product/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    intel = create_random_intel(db, faker)
    product = promote_intel_to_product(db, [intel.id])

    r = client.get(
        f"{settings.API_V1_STR}/product/?promoted_from=intel:{intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == product.id

    intel1 = create_random_intel(db, faker)
    product1 = promote_intel_to_product(db, [intel1.id])

    r = client.get(
        f"{settings.API_V1_STR}/product/?promoted_from=!intel:{intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert any(i["id"] == product1.id for i in api_dispatch["result"])
    assert all(i["id"] != product.id for i in api_dispatch["result"])
