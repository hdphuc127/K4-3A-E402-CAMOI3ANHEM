"""Lam sach van ban khong dang tin truoc khi no cham vao prompt.

VI SAO PHAI CO TANG NAY, BEN CANH CHI DAN TRONG PROMPT
------------------------------------------------------
Phong thu o tang prompt mang tinh xac suat: no *de nghi* model khang cu. Buoc
escape ``<`` -> ``&lt;`` va ``>`` -> ``&gt;`` thi khac - no la mot chung minh.
Sau buoc do, van ban khong dang tin KHONG THE VE MAT SO HOC phat ra chuoi
``</retrieved_documents>`` hay mo mot khoi ``<system>`` gia, bat ke model nghi
gi. Ton khoang 50 micro-giay, 0 token, test duoc ma khong can API key, va song
sot qua viec doi provider.

Hai tang bo sung cho nhau: sanitizer chan phan CAU TRUC mot cach tuyet doi,
chi dan trong prompt xu ly phan NGU NGHIA (van ban doc len giong mot menh lenh
ma khong can den the XML nao).

THU TU LA BAT BUOC
------------------
Sanitizer phai chay TRUOC buoc dien template, khong phai sau. Sau khi dien roi
thi khong con phan biet duoc byte cua ke tan cong voi delimiter cua chinh minh.

NGUYEN TAC: KHONG BAO GIO XOA CAU VI PHAM
-----------------------------------------
Xoa la co may sinh false-negative (ke tan cong chi can dien dat lai) va no pha
noi dung bai giang hop le - mot transcript day *ve* prompt injection se dinh het
moi pattern trong file nay. Ta gan co (flag) de quan sat duoc, con quyet dinh
chan hay khong thi de tang policy trong guardrails.py.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import IntEnum, StrEnum

__all__ = [
    "InjectionFlag",
    "Severity",
    "SanitizedText",
    "sanitize_untrusted",
]


class InjectionFlag(StrEnum):
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    ROLE_HIJACK = "ROLE_HIJACK"
    PROMPT_EXFILTRATION = "PROMPT_EXFILTRATION"
    JAILBREAK_PERSONA = "JAILBREAK_PERSONA"
    TAG_INJECTION = "TAG_INJECTION"
    HIDDEN_CHARACTERS = "HIDDEN_CHARACTERS"
    URL_EXFILTRATION = "URL_EXFILTRATION"
    SECRET_PATTERN = "SECRET_PATTERN"
    EXCESSIVE_PADDING = "EXCESSIVE_PADDING"


class Severity(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class SanitizedText:
    text: str
    flags: frozenset[InjectionFlag]
    severity: Severity
    truncated: bool
    original_length: int

    def has(self, flag: InjectionFlag) -> bool:
        return flag in self.flags


# Ky tu vo hinh: zero-width, bidi-override, BOM, soft hyphen.
# Dung de giau payload - trong editor cua nguoi review thi khong thay gi.
#
# Dung raw string: neu viet escape trong chuoi thuong, mot so cong cu ghi file
# se vat chat hoa chung thanh byte dieu khien that trong ma nguon, va Python
# tu choi nap file ("source code string cannot contain null bytes").
_INVISIBLE_RE = re.compile(r"[​-‏‪-‮⁠-⁤﻿­]")

# Control chars C0/C1, giu lai \n va \t.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")

_REPEAT_RUN_RE = re.compile(r"(.)\1{40,}")
_BLANK_RUN_RE = re.compile(r"\n{4,}")

# Song ngu Viet - Anh, vi ca kho tai lieu lan ke tan cong deu co the dung
# mot trong hai thu tieng.
_PATTERNS: tuple[tuple[re.Pattern[str], InjectionFlag, Severity], ...] = (
    (
        re.compile(
            r"(?i)\b(ignore|disregard|forget|override)\b[^.\n]{0,40}"
            r"\b(previous|above|prior|all)\b[^.\n]{0,20}"
            r"\b(instruction|prompt|rule|direction)s?\b"
        ),
        InjectionFlag.INSTRUCTION_OVERRIDE,
        Severity.CRITICAL,
    ),
    (
        re.compile(
            r"(?i)(bỏ qua|phớt lờ|quên đi|không cần tuân theo|đừng làm theo)"
            r"[^.\n]{0,40}"
            r"(hướng dẫn|chỉ dẫn|quy tắc|yêu cầu|phía trên|ở trên|trước đó)"
        ),
        InjectionFlag.INSTRUCTION_OVERRIDE,
        Severity.CRITICAL,
    ),
    (
        re.compile(r"(?im)^\s*(system|assistant|user|developer)\s*[:>]"),
        InjectionFlag.ROLE_HIJACK,
        Severity.HIGH,
    ),
    (
        re.compile(
            r"(?i)\b(you are now|from now on|act as|pretend to be)\b"
            r"|(kể từ bây giờ|từ giờ bạn là|bây giờ bạn là|hãy đóng vai)"
        ),
        InjectionFlag.ROLE_HIJACK,
        Severity.HIGH,
    ),
    (
        re.compile(
            r"(?i)(\b(reveal|repeat|print|output|show)\b|in ra|lặp lại|cho xem)"
            r"[^.\n]{0,30}"
            r"(\bsystem\s*prompt\b|\binstruction\b|hướng dẫn hệ thống|"
            r"\bapi[_\s-]?key\b|\bsecret\b)"
        ),
        InjectionFlag.PROMPT_EXFILTRATION,
        Severity.CRITICAL,
    ),
    (
        re.compile(
            r"(?i)\b(jailbreak|DAN mode|developer mode|do anything now)\b"
            r"|(chế độ nhà phát triển|chế độ không giới hạn)"
        ),
        InjectionFlag.JAILBREAK_PERSONA,
        Severity.HIGH,
    ),
    (
        re.compile(r"!\[[^\]]*\]\(\s*https?://"),
        InjectionFlag.URL_EXFILTRATION,
        Severity.MEDIUM,
    ),
    (
        re.compile(
            r"(sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{30,}"
            r"|Bearer\s+[A-Za-z0-9._-]{16,})"
        ),
        InjectionFlag.SECRET_PATTERN,
        Severity.HIGH,
    ),
)

_TRUNCATION_MARK = " [...da cat bot]"


def sanitize_untrusted(raw: str, *, max_chars: int = 4000) -> SanitizedText:
    """Chuan hoa, escape va gan co cho mot doan van ban khong dang tin.

    Bao dam duy nhat va tuyet doi: ``"<" not in result.text`` va
    ``">" not in result.text``.
    """
    if not raw:
        return SanitizedText("", frozenset(), Severity.NONE, False, 0)

    original_length = len(raw)
    flags: set[InjectionFlag] = set()
    severity = Severity.NONE

    # 1. NFKC truoc tien - gop fullwidth "＜ｓｙｓｔｅｍ＞" va homoglyph ve ASCII.
    #    Neu lam sau buoc match thi moi regex ben duoi deu bi qua mat.
    text = unicodedata.normalize("NFKC", raw)

    # 2. Ky tu vo hinh.
    cleaned = _INVISIBLE_RE.sub("", text)
    if cleaned != text:
        flags.add(InjectionFlag.HIDDEN_CHARACTERS)
        severity = max(severity, Severity.MEDIUM)
    text = cleaned

    # 3. Control chars.
    text = _CONTROL_RE.sub("", text)

    # 4. Nhan dien pattern - lam TRUOC khi escape, vi sau khi escape thi
    #    van ban van doc duoc nhung ta muon bat ca y do lan cau truc.
    for pattern, flag, sev in _PATTERNS:
        if pattern.search(text):
            flags.add(flag)
            severity = max(severity, sev)

    # 5. Escape entity. Thu tu bat buoc: "&" truoc, neu khong thi "&lt;" vua
    #    tao ra se bi escape lan hai thanh "&amp;lt;".
    if "<" in text or ">" in text:
        flags.add(InjectionFlag.TAG_INJECTION)
        # Chi LOW: transcript bai giang ve code hoac ve chinh prompt injection
        # co chua dau ngoac nhon mot cach hoan toan hop le.
        severity = max(severity, Severity.LOW)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 6. Gop padding - chan thu day chi dan that ra khoi cua so chu y.
    collapsed = _BLANK_RUN_RE.sub("\n\n\n", text)
    collapsed = _REPEAT_RUN_RE.sub(lambda m: m.group(1) * 40, collapsed)
    if collapsed != text:
        flags.add(InjectionFlag.EXCESSIVE_PADDING)
        severity = max(severity, Severity.LOW)
    text = collapsed

    # 7. Cat theo bien tu.
    truncated = False
    if len(text) > max_chars:
        cut = text[:max_chars]
        space = cut.rfind(" ")
        if space > max_chars * 0.8:
            cut = cut[:space]
        text = cut.rstrip() + _TRUNCATION_MARK
        truncated = True

    return SanitizedText(
        text=text,
        flags=frozenset(flags),
        severity=severity,
        truncated=truncated,
        original_length=original_length,
    )
