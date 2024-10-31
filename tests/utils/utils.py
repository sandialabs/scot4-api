import base64
import copy
import os
import random
from faker import Faker
from faker.providers import internet
from fastapi.testclient import TestClient
from tabulate import tabulate

from app.core.config import settings

try:
    from tests.utils.entity import create_entity
except ImportError:
    # needed to make initial_data.py function properly
    from entity import create_entity


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


def generate_html_entry(faker: Faker):
    ioc_choices = {
        "mac": [faker.mac_address() for x in range(100)],
        "id": [faker.md5() for x in range(100)],
        "mail": [faker.email() for x in range(100)],
        "v4_ip": [faker.ipv4() for x in range(100)],
        "v6_ip": [faker.ipv6() for x in range(100)],
        "url": [faker.url() for x in range(100)],
        "domains": [faker.domain_name() for x in range(100)],
    }
    image_dir = os.path.dirname(__file__)
    faker.add_provider(internet)
    is_list = 1 if random.uniform(0, 1) > 0.1 else 0
    is_table = 1 if random.uniform(0, 1) > 0.5 else 0
    is_image = 1 if random.uniform(0, 1) > 0.75 else 0
    is_pre = 1 if random.uniform(0, 1) > 0.25 else 0
    num_elements = is_list + is_table + is_image + is_pre
    words_in_sentences = random.choices(range(80, 100), k=random.randint(1 + num_elements, 5 + num_elements))
    sentences = []
    flaired_sentences = []
    entities = []
    for x in words_in_sentences:
        fake_sentence = faker.sentence(nb_words=x)
        fake_sentence_flaired = copy.deepcopy(fake_sentence)

        num_uris = random.randint(1, 3)
        uris = [f"{random.choice(ioc_choices['url'])}" for _ in range(num_uris)]
        uris_flaired = []
        for uri in uris:
            entity = create_entity(uri, "uri")
            entities.append(entity)
            uris_flaired.append(
                f'<span class="entity uri" data-entity-type="uri" data-entity-value="{uri}">{uri}</span>'
            )

        num_ip4 = random.randint(1, 3)
        ipv4 = [f"{random.choice(ioc_choices['v4_ip'])}" for _ in range(num_ip4)]

        ipv4_flaired = []
        for ip in ipv4:
            entity = create_entity(ip, "ipv4")
            entities.append(entity)

            ipv4_flaired.append(
                f'<span class="entity ipv4" data-entity-type="ipv4" data-entity-value="{ip}">{ip}</span>'
            )

        num_ip6 = random.randint(1, 3)
        ipv6 = [f"{random.choice(ioc_choices['v6_ip'])}" for _ in range(num_ip6)]
        ipv6_flaired = []
        for ip in ipv6:
            entity = create_entity(ip, "ipv6")
            entities.append(entity)

            ipv6_flaired.append(
                f'<span class="entity ipv6" data-entity-type="ipv6" data-entity-value="{ip}">{ip}</span>'
            )

        num_domains = random.randint(1, 3)
        domains = [
            f"{random.choice(ioc_choices['domains'])}" for _ in range(num_domains)
        ]

        domains_flaired = []
        for domain in domains:
            entity = create_entity(domain, "domain")
            entities.append(entity)
            domains_flaired.append(
                f'<span class="entity domain" data-entity-type="domain" data-entity-value="{domain}">{domain}</span>'
            )

        emails = [f"{faker.word()}@{domain}" for domain in domains]
        emails_flaired = []
        for email, domain in zip(emails, domains):
            entity = create_entity(email, "email")
            entities.append(entity)
            emails_flaired.append(
                f'<span class="entity email" data-entity-type="email" data-entity-value="{email}">{email.split("@")[0]}<span class="entity domain" data-entity-type="domain" data-entity-value="{domain}">{domain}</span></span>'
            )

        num_emails = len(emails)
        num_sentence_elements = num_uris + num_ip4 + num_ip6 + num_domains + num_emails
        fake_sentence = fake_sentence.split(" ")
        fake_sentence_flaired = fake_sentence_flaired.split(" ")
        sentence_positions = random.choices(
            range(len(fake_sentence)), k=num_sentence_elements
        )
        word_index = 0
        hyper_link_positions = sentence_positions[word_index: word_index + num_uris]
        word_index = word_index + num_uris
        ip4_positions = sentence_positions[word_index: word_index + num_ip4]
        word_index = word_index + num_ip4
        ip6_positions = sentence_positions[word_index: word_index + num_ip6]
        word_index = word_index + num_ip6
        domain_positions = sentence_positions[word_index: word_index + num_domains]
        word_index = word_index + num_domains
        email_positions = sentence_positions[word_index: word_index + num_emails]
        word_index = word_index + num_emails

        fake_sentence = [
            uris.pop(0) if i in hyper_link_positions else y
            for i, y in enumerate(fake_sentence)
        ]
        fake_sentence = [
            ipv4.pop(0) if i in ip4_positions else y
            for i, y in enumerate(fake_sentence)
        ]
        fake_sentence = [
            ipv6.pop(0) if i in ip6_positions else y
            for i, y in enumerate(fake_sentence)
        ]
        fake_sentence = [
            domains.pop(0) if i in domain_positions else y
            for i, y in enumerate(fake_sentence)
        ]
        fake_sentence = [
            emails.pop(0) if i in email_positions else y
            for i, y in enumerate(fake_sentence)
        ]
        fake_sentence = " ".join(fake_sentence)

        fake_sentence_flaired = [
            uris_flaired.pop(0) if i in hyper_link_positions else y
            for i, y in enumerate(fake_sentence_flaired)
        ]
        fake_sentence_flaired = [
            ipv4_flaired.pop(0) if i in ip4_positions else y
            for i, y in enumerate(fake_sentence_flaired)
        ]
        fake_sentence_flaired = [
            ipv6_flaired.pop(0) if i in ip6_positions else y
            for i, y in enumerate(fake_sentence_flaired)
        ]
        fake_sentence_flaired = [
            domains_flaired.pop(0) if i in domain_positions else y
            for i, y in enumerate(fake_sentence_flaired)
        ]
        fake_sentence_flaired = [
            emails_flaired.pop(0) if i in email_positions else y
            for i, y in enumerate(fake_sentence_flaired)
        ]

        fake_sentence_flaired = " ".join(fake_sentence_flaired)

        sentences.append(f"<p>{fake_sentence}</p>")
        flaired_sentences.append(f"<p>{fake_sentence_flaired}</p>")

    element_positions = random.choices(range(len(sentences)), k=num_elements)
    index = 0
    if is_table == 1:
        table_pos = element_positions[index]
        table_rows = random.randint(2, 5)
        table_columns = random.randint(2, 5)
        headers = [faker.word() for x in range(table_columns)]
        table = [
            [
                " ".join(faker.words(nb=random.randint(2, 5)))
                for _ in range(table_columns)
            ]
            for _ in range(table_rows)
        ]
        html_table = tabulate(table, headers=headers, tablefmt="unsafehtml")
        sentences.insert(table_pos, html_table)
        flaired_sentences.insert(table_pos, html_table)
        index += 1

    if is_image == 1:
        image_pos = element_positions[index]
        image_dictionary = {
            0: f"{image_dir}/test_images/coffee.png",
            1: f"{image_dir}/test_images/covid.png",
        }
        image_data_index = faker.pybool()
        image_data_uri = base64.b64encode(
            open(image_dictionary[image_data_index], "rb").read()
        )
        image_data_uri = (
            f'<img src="data:image/png;base64,{image_data_uri.decode()}"</img>'
        )
        sentences.insert(image_pos, image_data_uri)
        flaired_sentences.insert(image_pos, image_data_uri)
        index += 1

    if is_pre == 1:
        pre_text = faker.paragraph(nb_sentences=4)
        pre_text = f"<p><pre>{pre_text}</pre></p>"
        pre_pos = element_positions[index]
        sentences.insert(pre_pos, pre_text)
        flaired_sentences.insert(pre_pos, pre_text)
        index += 1

    if is_list == 1:
        list_pos = element_positions[index]
        html_list = generate_html_list(faker.words(nb=random.randint(2, 5)))
        sentences.insert(list_pos, html_list)
        flaired_sentences.insert(list_pos, html_list)
        index += 1

    entry_data_raw = "".join(sentences)
    entry_data_flaired = "".join(flaired_sentences)

    return entry_data_raw, entry_data_flaired, entities


def generate_html_list(words):
    text = []
    text.append("<p>")
    text.append("<ul>")
    for word in words:
        text.append(f"<li>{word}</li>")
    text.append("</ul>")
    return "\n".join(text)
