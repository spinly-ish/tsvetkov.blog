#!/usr/bin/env python3
"""Apply Directus schema for tsvetkov.blog.

Создаёт коллекции `posts` и `site_config`, поля и роли через REST API.
Идемпотентный: повторный запуск пропустит уже созданное.

Использование:
    DIRECTUS_URL=http://localhost:8055 \
    DIRECTUS_TOKEN=<static admin token> \
    python3 apply_schema.py

Токен берётся из Directus UI: User → Token (Static). Нужны admin права.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


URL = os.environ.get("DIRECTUS_URL", "").rstrip("/")
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")

if not URL or not TOKEN:
    sys.exit("Set DIRECTUS_URL and DIRECTUS_TOKEN env vars")


def api(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    req = urllib.request.Request(
        f"{URL}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body_text)
        except json.JSONDecodeError:
            return e.code, body_text


def exists_collection(name: str) -> bool:
    code, _ = api("GET", f"/collections/{name}")
    return code == 200


def exists_field(collection: str, field: str) -> bool:
    code, _ = api("GET", f"/fields/{collection}/{field}")
    return code == 200


def exists_role(name: str) -> str | None:
    code, data = api("GET", f"/roles?filter[name][_eq]={name}&limit=1")
    if code == 200 and data and data.get("data"):
        return data["data"][0]["id"]
    return None


def exists_policy(name: str) -> str | None:
    code, data = api("GET", f"/policies?filter[name][_eq]={name}&limit=1")
    if code == 200 and data and data.get("data"):
        return data["data"][0]["id"]
    return None


def exists_access(role_id: str, policy_id: str) -> bool:
    code, data = api(
        "GET",
        f"/access?filter[role][_eq]={role_id}&filter[policy][_eq]={policy_id}&limit=1",
    )
    return code == 200 and bool(data and data.get("data"))


def create_collection(name: str, *, singleton: bool = False, note: str = "") -> None:
    if exists_collection(name):
        print(f"  collection {name}: exists, skip")
        return
    body = {
        "collection": name,
        "meta": {
            "icon": "article" if name == "posts" else "settings",
            "note": note,
            "singleton": singleton,
        },
        "schema": {"name": name},
    }
    code, resp = api("POST", "/collections", body)
    if code >= 300:
        sys.exit(f"create collection {name} failed: {code} {resp}")
    print(f"  collection {name}: created")


def create_field(collection: str, field: str, spec: dict) -> None:
    if exists_field(collection, field):
        print(f"  field {collection}.{field}: exists, skip")
        return
    body = {"field": field, **spec}
    code, resp = api("POST", f"/fields/{collection}", body)
    if code >= 300:
        sys.exit(f"create field {collection}.{field} failed: {code} {resp}")
    print(f"  field {collection}.{field}: created")


# ---------- Field specs ----------

def s_string(required: bool = True, interface: str = "input") -> dict:
    return {
        "type": "string",
        "meta": {"interface": interface, "required": required},
        "schema": {"is_nullable": not required},
    }


def s_text(required: bool = True, interface: str = "input-multiline") -> dict:
    return {
        "type": "text",
        "meta": {"interface": interface, "required": required},
        "schema": {"is_nullable": not required},
    }


def s_md(required: bool = True) -> dict:
    return {
        "type": "text",
        "meta": {"interface": "input-rich-text-md", "required": required, "options": {"toolbar": ["heading", "bold", "italic", "strikethrough", "bullist", "numlist", "blockquote", "link", "code", "empty"]}},
        "schema": {"is_nullable": not required},
    }


def s_int(required: bool = True) -> dict:
    return {
        "type": "integer",
        "meta": {"interface": "input", "required": required},
        "schema": {"is_nullable": not required},
    }


def s_date() -> dict:
    return {
        "type": "date",
        "meta": {"interface": "datetime", "required": True},
        "schema": {"is_nullable": False},
    }


def s_dropdown(choices: list[tuple[str, str]], default: str) -> dict:
    return {
        "type": "string",
        "meta": {
            "interface": "select-dropdown",
            "options": {"choices": [{"text": t, "value": v} for v, t in choices]},
            "required": True,
        },
        "schema": {"is_nullable": False, "default_value": default},
    }


def s_slug() -> dict:
    return {
        "type": "string",
        "meta": {"interface": "input", "required": True, "options": {"slug": True}},
        "schema": {"is_nullable": False, "is_unique": True},
    }


# ---------- Schema definitions ----------

SITE_CONFIG_FIELDS: dict[str, dict] = {
    "base_url": s_string(),
    "author": s_string(),
    "job_title": s_string(),
    "title_en": s_string(),
    "title_ru": s_string(),
    "description_en": s_text(),
    "description_ru": s_text(),
    "og_description_en": s_text(),
    "og_description_ru": s_text(),
    "hero_label_en": s_string(),
    "hero_label_ru": s_string(),
    "about_title_en": s_string(),
    "about_title_ru": s_string(),
    "about_text_en": s_text(),
    "about_text_ru": s_text(),
    "back_link_en": s_string(),
    "back_link_ru": s_string(),
    "read_time_template_en": s_string(),
    "read_time_template_ru": s_string(),
    "feed_title_en": s_string(),
    "feed_title_ru": s_string(),
    "feed_description_en": s_text(),
    "feed_description_ru": s_text(),
}

POSTS_FIELDS: dict[str, dict] = {
    "slug": s_slug(),
    "date": s_date(),
    "read_time_min": s_int(),
    "image": s_string(),
    "status": s_dropdown(
        [("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
        default="draft",
    ),
    "sort": s_int(required=False),
    "title_en": s_string(),
    "title_ru": s_string(),
    "description_en": s_text(),
    "description_ru": s_text(),
    "excerpt_en": s_text(),
    "excerpt_ru": s_text(),
    "image_alt_card_en": s_string(),
    "image_alt_card_ru": s_string(),
    "image_alt_post_en": s_string(),
    "image_alt_post_ru": s_string(),
    "body_md_en": s_md(),
    "body_md_ru": s_md(),
}


# ---------- Roles ----------

def ensure_role(name: str, description: str) -> str:
    """v11: role хранит только name/description/icon. admin/app access ушли в policy."""
    role_id = exists_role(name)
    if role_id:
        print(f"  role {name}: exists, skip")
        return role_id
    code, resp = api("POST", "/roles", {"name": name, "description": description})
    if code >= 300:
        sys.exit(f"create role {name} failed: {code} {resp}")
    print(f"  role {name}: created")
    return resp["data"]["id"]


def ensure_policy(name: str, description: str, *, admin_access: bool = False, app_access: bool = False) -> str:
    """v11: policy держит admin_access/app_access и связанные permissions."""
    policy_id = exists_policy(name)
    if policy_id:
        print(f"  policy {name}: exists, skip")
        return policy_id
    code, resp = api("POST", "/policies", {
        "name": name,
        "description": description,
        "admin_access": admin_access,
        "app_access": app_access,
    })
    if code >= 300:
        sys.exit(f"create policy {name} failed: {code} {resp}")
    print(f"  policy {name}: created")
    return resp["data"]["id"]


def ensure_access(role_id: str, policy_id: str, label: str) -> None:
    """v11: связывает role ↔ policy через junction-коллекцию /access."""
    if exists_access(role_id, policy_id):
        print(f"    access {label}: exists, skip")
        return
    code, resp = api("POST", "/access", {"role": role_id, "policy": policy_id})
    if code >= 300:
        sys.exit(f"create access {label} failed: {code} {resp}")
    print(f"    access {label}: created")


def ensure_permission(policy_id: str, collection: str, action: str, fields: list[str] | None = None, permissions: dict | None = None) -> None:
    """v11: permission привязан к policy, а не к role напрямую."""
    code, data = api(
        "GET",
        f"/permissions?filter[policy][_eq]={policy_id}&filter[collection][_eq]={collection}&filter[action][_eq]={action}&limit=1",
    )
    if code == 200 and data and data.get("data"):
        print(f"    perm {collection}.{action}: exists, skip")
        return
    body = {
        "policy": policy_id,
        "collection": collection,
        "action": action,
        "fields": fields or ["*"],
        "permissions": permissions or {},
        "validation": {},
    }
    code, resp = api("POST", "/permissions", body)
    if code >= 300:
        sys.exit(f"create permission {collection}.{action} failed: {code} {resp}")
    print(f"    perm {collection}.{action}: created")


# ---------- Main ----------

def main() -> None:
    print(f"Connecting to {URL}")
    code, _ = api("GET", "/server/info")
    if code != 200:
        sys.exit(f"cannot reach Directus at {URL}: {code}")

    print("Creating collections")
    create_collection("site_config", singleton=True, note="Глобальные настройки сайта (singleton)")
    create_collection("posts", note="Посты блога: метаданные + локализованные тексты + Markdown тело")

    print("Creating fields: site_config")
    for fname, spec in SITE_CONFIG_FIELDS.items():
        create_field("site_config", fname, spec)

    print("Creating fields: posts")
    for fname, spec in POSTS_FIELDS.items():
        create_field("posts", fname, spec)

    print("Creating roles")
    agent_role = ensure_role("agent", "AI агент или внешний клиент. Create/Read/Update постов.")
    build_role = ensure_role("build", "CI builder. Read только опубликованных постов и site_config.")

    print("Creating policies")
    agent_policy = ensure_policy("agent-policy", "Permissions for agent role.")
    build_policy = ensure_policy("build-policy", "Permissions for build role.")

    print("Linking roles ↔ policies")
    ensure_access(agent_role, agent_policy, "agent ↔ agent-policy")
    ensure_access(build_role, build_policy, "build ↔ build-policy")

    print("Creating permissions: agent")
    ensure_permission(agent_policy, "posts", "create")
    ensure_permission(agent_policy, "posts", "read")
    ensure_permission(agent_policy, "posts", "update")
    ensure_permission(agent_policy, "posts", "delete")
    # site_config — singleton, агент должен уметь править глобальные настройки.
    ensure_permission(agent_policy, "site_config", "create")
    ensure_permission(agent_policy, "site_config", "read")
    ensure_permission(agent_policy, "site_config", "update")

    print("Creating permissions: build")
    ensure_permission(
        build_policy,
        "posts",
        "read",
        permissions={"status": {"_eq": "published"}},
    )
    ensure_permission(build_policy, "site_config", "read")

    print()
    print("Done. Next steps:")
    print(f"  1. Open {URL}/admin → Settings → Access Tokens")
    print("  2. Create static token for `agent` role → save as DIRECTUS_AGENT_TOKEN")
    print("  3. Create static token for `build` role → save as DIRECTUS_BUILD_TOKEN")
    print("  4. Run scripts/migrate_to_directus.py to import existing posts.")


if __name__ == "__main__":
    main()
