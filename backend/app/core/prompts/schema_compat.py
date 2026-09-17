"""Hạ cấp JSON Schema của pydantic xuống hai phương ngữ provider.

Một pydantic model là nguồn sự thật duy nhất. Từ đó sinh ra:

- ``to_openai_response_format()`` — ``json_schema`` strict mode.
- ``to_gemini_schema()`` — ``response_schema``, vốn chỉ nhận một tập con của
  OpenAPI.

Điểm quan trọng: khi gặp ``anyOf`` / ``allOf`` / ``oneOf``, hàm này **raise ngay
lúc build** chứ không im lặng bỏ qua. Lỗi lúc chạy test còn hơn lỗi Gemini 400
giữa buổi demo. Test ``test_gemini_schema_has_no_unsupported_keys`` chạy hàm này
trên cả bốn model đầu ra.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

__all__ = [
    "UnsupportedSchemaError",
    "to_openai_response_format",
    "to_gemini_schema",
]


class UnsupportedSchemaError(TypeError):
    """Model đầu ra dùng cấu trúc mà Gemini response_schema không nhận."""


# Gemini chỉ giữ lại các khoá này; mọi khoá khác bị loại bỏ.
_GEMINI_ALLOWED_KEYS = frozenset(
    {
        "type",
        "format",
        "description",
        "nullable",
        "enum",
        "items",
        "properties",
        "required",
    }
)

_REJECTED_KEYS = ("anyOf", "allOf", "oneOf", "not")


def _resolve_ref(ref: str, defs: dict[str, Any]) -> dict[str, Any]:
    name = ref.rsplit("/", 1)[-1]
    if name not in defs:
        raise UnsupportedSchemaError(f"Khong giai duoc $ref: {ref}")
    return defs[name]


def _strip_for_gemini(node: Any, defs: dict[str, Any], path: str = "$") -> Any:
    """Duyệt đệ quy, inline $ref và loại bỏ khoá Gemini không hiểu."""
    if isinstance(node, list):
        return [_strip_for_gemini(item, defs, f"{path}[]") for item in node]
    if not isinstance(node, dict):
        return node

    for key in _REJECTED_KEYS:
        if key in node:
            raise UnsupportedSchemaError(
                f"{path}: Gemini response_schema khong ho tro '{key}'. "
                "Model dau ra khong duoc dung Optional/Union - "
                'dung sentinel "" hoac [] thay cho null.'
            )

    if "$ref" in node:
        node = {
            **_resolve_ref(node["$ref"], defs),
            **{k: v for k, v in node.items() if k != "$ref"},
        }

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key not in _GEMINI_ALLOWED_KEYS:
            continue
        if key == "properties" and isinstance(value, dict):
            out[key] = {
                prop: _strip_for_gemini(sub, defs, f"{path}.{prop}")
                for prop, sub in value.items()
            }
        elif key == "items":
            out[key] = _strip_for_gemini(value, defs, f"{path}[]")
        else:
            out[key] = value

    # Moi field deu bat buoc - xem docstring schemas.py.
    if out.get("type") == "object" and "properties" in out:
        out["required"] = sorted(out["properties"].keys())
    return out


def to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    raw = model.model_json_schema(by_alias=True)
    defs = raw.get("$defs", {})
    return _strip_for_gemini(raw, defs)


def _force_strict(node: Any, defs: dict[str, Any]) -> Any:
    """OpenAI strict mode: additionalProperties=false và required đầy đủ."""
    if isinstance(node, list):
        return [_force_strict(item, defs) for item in node]
    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        node = {
            **_resolve_ref(node["$ref"], defs),
            **{k: v for k, v in node.items() if k != "$ref"},
        }

    out = {k: _force_strict(v, defs) for k, v in node.items() if k != "$defs"}
    if out.get("type") == "object" and isinstance(out.get("properties"), dict):
        out["additionalProperties"] = False
        out["required"] = sorted(out["properties"].keys())
    return out


def to_openai_response_format(model: type[BaseModel]) -> dict[str, Any]:
    raw = model.model_json_schema(by_alias=True)
    defs = raw.get("$defs", {})
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model.__name__,
            "strict": True,
            "schema": _force_strict(raw, defs),
        },
    }
