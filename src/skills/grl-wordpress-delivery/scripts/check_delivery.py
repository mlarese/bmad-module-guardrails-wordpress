#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pre-pass sullo stato di una delivery WordPress: schema, enum, coerenza, media.

Lo stato della delivery e' un contratto: quattro artefatti con tre valori
ciascuno, tre gate, una tabella dei media e un insieme di combinazioni che non
possono esistere — `release-approved` con un media pendente, un gate passato con
un artefatto ancora aperto. Verificarlo e' un confronto con una tabella, non un
giudizio: stesso file, stesso esito.

Cosa significhi un'evidenza e se basti restano di Milo e del modello.

Uscita: JSON su stdout. Exit 0 = coerente, 1 = violazioni, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from identity import digest_matches, immutable  # noqa: E402

SCHEMA = "grl-wordpress-delivery/v1"

DELIVERY_FILES = (
    "delivery.md",
    "content-model.md",
    "component-plan.md",
    "media-map.md",
    "release-evidence.md",
)

INTENTS = {"create", "migrate", "verify"}
ARTIFACT_KEYS = ("content_model", "component_plan", "media_map", "release_evidence")
# `not-applicable` esiste per `verify`, che non approva un modello e non pianifica
# componenti: senza, quei due artefatti resterebbero `pending` per sempre e
# nessun gate potrebbe partire.
ARTIFACT_VALUES = {"pending", "ready", "blocked", "not-applicable"}
# `verify` non approva un modello e non pianifica componenti: quei due file non
# esistono, quindi non possono nemmeno essere revisionati.
VERIFY_REQUIRED_FILES = ("delivery.md", "media-map.md", "release-evidence.md")
VERIFY_OPTIONAL_ARTIFACTS = ("content_model", "component_plan")
REVIEW_VALUES = {"pending", "passed", "blocked"}
VERDICTS = {"GO", "GO_CON_CONDIZIONI", "NO_GO", "EVIDENZA_INSUFFICIENTE"}
RELEASE_VALUES = {"pending", "blocked"} | VERDICTS
MEDIA_VALUES = {"pending", "verified", "blocked"}

STATUSES = (
    "planning",
    "awaiting-authorization",
    "implementing",
    "verification-pending",
    "blocked",
    "gate-pending",
    "release-approved",
    "released",
)

# Una transizione assente non e' un errore di battitura: e' un salto che nasconde
# un controllo non fatto. `planning → released` ne salta cinque.
TRANSITIONS = {
    "planning": {"awaiting-authorization", "implementing", "verification-pending", "gate-pending", "blocked"},
    "awaiting-authorization": {"planning", "implementing", "blocked"},
    "implementing": {"planning", "verification-pending", "blocked"},
    "verification-pending": {"planning", "implementing", "gate-pending", "blocked"},
    "gate-pending": {"planning", "implementing", "release-approved", "blocked"},
    "release-approved": {"implementing", "released", "blocked"},
    "released": {"blocked"},
    "blocked": {
        "planning",
        "awaiting-authorization",
        "implementing",
        "verification-pending",
        "gate-pending",
    },
}

TERMINAL_OK = {"release-approved", "released"}

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
INLINE_MAP = re.compile(r"^\{(.*)\}$")
INLINE_LIST = re.compile(r"^\[(.*)\]$")
ATTACHMENT_ID = re.compile(r"^\d+$")
# Lo slug e' un segmento di percorso: minuscole, cifre, punti e trattini.
SLUG = re.compile(r"^[a-z0-9]+([.-][a-z0-9]+)*$")

MEDIA_COLUMNS = ("asset", "target e binding", "attachment", "stato", "alt text", "evidenza")
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}


def fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_only).strip()


def slugify(name: str) -> str:
    """Nome libero → slug della cartella, sempre accettato da `SLUG`.

    Lo stesso nome deve dare lo stesso slug — due normalizzazioni diverse
    creerebbero due delivery per lo stesso sito — e lo slug prodotto deve
    superare il validatore di questo stesso script, altrimenti la cartella
    nascerebbe con un nome che ogni controllo successivo rifiuta.
    """
    stripped = unicodedata.normalize("NFKD", name)
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii").lower()
    # I punti restano solo fra due alfanumerici: `1.0` e' una versione,
    # `dott. rossi` e' una punteggiatura.
    slug = re.sub(r"[^a-z0-9.]+", "-", ascii_only)
    slug = re.sub(r"\.(?![a-z0-9])", "-", slug)
    slug = re.sub(r"(?<![a-z0-9])\.", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-.")
    return slug if SLUG.fullmatch(slug) else ""


def split_top_level(text: str) -> list[str]:
    """Divide su virgole non annidate e non citate.

    Un blocker o un ambito di autorizzazione contengono virgole per natura:
    spezzarli produrrebbe due voci dove ce n'è una.
    """
    parts, depth, quote, current = [], 0, "", []
    for char in text:
        if quote:
            if char == quote:
                quote = ""
            current.append(char)
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def parse_scalar(raw: str) -> object:
    value = raw.strip()
    if value in ("", "null", "~"):
        return None
    if value.startswith(('"', "'")) and value[-1:] == value[:1] and len(value) >= 2:
        return value[1:-1]
    if value in ("true", "false"):
        return value == "true"
    inline_map = INLINE_MAP.match(value)
    if inline_map:
        mapping: dict[str, object] = {}
        for chunk in split_top_level(inline_map.group(1)):
            if ":" not in chunk:
                continue
            key, item = chunk.split(":", 1)
            mapping[key.strip()] = parse_scalar(item)
        return mapping
    inline_list = INLINE_LIST.match(value)
    if inline_list:
        return [parse_scalar(chunk) for chunk in split_top_level(inline_list.group(1))]
    return value


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Frontmatter YAML nelle due forme che un autore scrive davvero: mappe
    inline su una riga e mappe indentate sotto la chiave."""
    match = FRONTMATTER.match(text)
    if not match:
        return None
    data: dict[str, object] = {}
    pending_key: str | None = None
    for line in match.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if not pending_key:
                continue
            stripped = line.strip()
            if stripped.startswith("- "):
                # `blockers:` seguito da voci di lista: il contenitore è una
                # lista, non una mappa.
                existing = data.get(pending_key)
                items = existing if isinstance(existing, list) else []
                items.append(parse_scalar(stripped[2:]))
                data[pending_key] = items
            elif ":" in stripped:
                nested = data.get(pending_key)
                nested = nested if isinstance(nested, dict) else {}
                key, raw = stripped.split(":", 1)
                nested[key.strip()] = parse_scalar(raw)
                data[pending_key] = nested
            continue
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if not raw.strip():
            # `artifacts:` seguito da righe indentate: la mappa arriva sotto.
            data[key] = {}
            pending_key = key
            continue
        pending_key = None
        data[key] = parse_scalar(raw)
    return data


def parse_media_table(text: str) -> tuple[list[dict], list[str]]:
    """Righe della tabella dei media. La forma della tabella e' il contratto."""
    problems: list[str] = []
    rows: list[dict] = []
    lines = [line.strip() for line in text.split("\n")]
    header_index = None
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = [fold(cell) for cell in line.strip("|").split("|")]
        if all(column in cells for column in MEDIA_COLUMNS):
            header_index = index
            header = cells
            break
    if header_index is None:
        return [], ["la tabella dei media non ha le colonne attese: " + ", ".join(MEDIA_COLUMNS)]

    position = {column: header.index(column) for column in MEDIA_COLUMNS}
    for line in lines[header_index + 1:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if len(cells) < len(header):
            problems.append(f"riga con meno colonne del previsto: {line}")
            continue
        # Anche le colonne oltre le obbligatorie: `Identità` porta MIME e
        # dimensioni, ed è lì che il confronto con l'atteso va a guardare.
        row = {name: cells[index] for index, name in enumerate(header) if name}
        row.update({column: cells[position[column]] for column in MEDIA_COLUMNS})
        rows.append(row)
    return rows, problems


def delivery_target_of(frontmatter: dict) -> str:
    return str(frontmatter.get("target") or "")


def tokens(text: str) -> set[str]:
    """Token della cella, separati da spazi e punteggiatura di elenco.

    Il confronto va su token interi: `42` non deve valere per `4207`, e
    `640×320` non deve valere per `1640×3200`.
    """
    return {t.strip().lower() for t in re.split(r"[\s·,;|]+", text) if t.strip()}


# Dove vive ciascun campo atteso: la cella esatta, oppure i token delle colonne
# che descrivono l'identità osservata.
EXACT_FIELDS = {"attachment": "attachment", "filename": "asset"}
# Le intestazioni arrivano già normalizzate da `fold`: «Identità» → «identita».
TOKEN_COLUMNS = ("identita", "evidenza")


def check_expected_media(rows: list[dict], expected: dict) -> list[str]:
    """Identità attesa contro identità registrata, campo per campo.

    `attachment` e `filename` si confrontano con la loro cella per uguaglianza;
    MIME, dimensioni e checksum si cercano come token interi nelle colonne che
    portano l'identità osservata. Se quelle colonne non ci sono, il campo non è
    verificabile e va detto: dichiararlo corrispondente sarebbe peggio.
    """
    violations: list[str] = []
    by_asset = {row["asset"]: row for row in rows}
    for asset, fields in expected.items():
        row = by_asset.get(asset)
        if row is None:
            violations.append(f"`{asset}`: atteso ma assente dalla mappa dei media")
            continue
        observed = set()
        for column in TOKEN_COLUMNS:
            if row.get(column):
                observed |= tokens(str(row[column]))
        for key, value in (fields or {}).items():
            if not value:
                continue
            wanted = str(value).strip().lower()
            column = EXACT_FIELDS.get(key)
            if column:
                actual = str(row.get(column, "")).strip().lower()
                if actual != wanted:
                    violations.append(
                        f"`{asset}`: {key} atteso {value}, registrato {row.get(column) or 'niente'}"
                    )
                continue
            if not observed:
                violations.append(
                    f"`{asset}`: {key} atteso ({value}) non verificabile, "
                    "la riga non registra nessuna identità osservata"
                )
            elif wanted not in observed:
                violations.append(
                    f"`{asset}`: {key} atteso ({value}) non compare fra i valori registrati"
                )
    return violations


def check_media(rows: list[dict]) -> tuple[dict, list[str]]:
    violations: list[str] = []
    seen: dict[str, str] = {}
    counts = {value: 0 for value in MEDIA_VALUES}
    unknown: list[str] = []

    def is_image(row: dict) -> bool:
        identity = str(row.get("identita") or "").strip().lower()
        asset = str(row.get("asset") or "").strip().lower()
        return identity.startswith("image/") or Path(asset).suffix in IMAGE_SUFFIXES

    for row in rows:
        asset = row["asset"] or "(senza nome)"
        state = row["stato"].strip().lower()
        attachment = row["attachment"].strip()
        alt_text = row["alt text"].strip()
        evidence = row["evidenza"].strip()

        if state in counts:
            counts[state] += 1
        else:
            unknown.append(asset)
            violations.append(f"`{asset}`: stato `{row['stato']}` fuori da {sorted(MEDIA_VALUES)}")
            continue

        if state == "verified":
            if not ATTACHMENT_ID.match(attachment):
                violations.append(
                    f"`{asset}`: verified senza attachment ID numerico (trovato: {attachment or 'vuoto'})"
                )
            if not evidence:
                violations.append(f"`{asset}`: verified senza evidenza")
            if not row["target e binding"].strip():
                violations.append(f"`{asset}`: verified senza target e binding")
            if is_image(row):
                alt_folded = fold(alt_text)
                decorative_declaration = "decorativ" in alt_folded and "alt" in alt_folded
                decorative_empty = decorative_declaration and (
                    "vuot" in alt_folded or "empty" in alt_folded
                )
                if not alt_folded or alt_folded in {"non noto", "n a", "da definire", "pending"}:
                    violations.append(
                        f"`{asset}`: immagine verified senza alt text informativo o dichiarazione decorativa"
                    )
                elif decorative_declaration and not decorative_empty:
                    violations.append(
                        f"`{asset}`: dichiarazione decorativa senza dichiarare alt vuoto"
                    )
                elif decorative_empty:
                    # Un'immagine decorativa può avere alt vuoto, ma la scelta
                    # deve essere esplicita e rileggibile da chi verifica.
                    pass

        if ATTACHMENT_ID.match(attachment):
            if attachment in seen and seen[attachment] != asset:
                violations.append(
                    f"attachment {attachment} usato da `{seen[attachment]}` e da `{asset}`"
                )
            seen.setdefault(attachment, asset)

    summary = {
        "total": len(rows),
        "by_state": counts,
        "unknown_state": unknown,
        "all_verified": bool(rows) and counts["verified"] == len(rows),
    }
    return summary, violations


# `media-map.md` non entra: e' una tabella di fatti, non prosa, e il gate 1 la
# copre gia' con la lente structure.
PROSE_REVIEWED = (
    "content-model.md",
    "component-plan.md",
    "release-evidence.md",
    "delivery.md",
)
VERIFY_PROSE_REVIEWED = ("release-evidence.md", "delivery.md")

# I path revisionati si dichiarano in un blocco, non sparsi nel testo: una frase
# che dice «NON eseguita su content-model.md» non deve valere per una citazione.
REVIEWED_HEADING = re.compile(r"^\s*#*\s*file revisionati\b", re.I | re.M)
LIST_ITEM = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.M)
MARKDOWN_PATH = re.compile(r"[\w./-]+\.md")


def reviewed_paths(text: str) -> list[str]:
    """Le voci elencate sotto l'intestazione «File revisionati»."""
    heading = REVIEWED_HEADING.search(text)
    if not heading:
        return []
    block: list[str] = []
    for line in text[heading.end():].split("\n"):
        item = LIST_ITEM.match(line)
        if item:
            block.append(item.group(1).strip())
            continue
        if line.strip() and block:
            break
    return block


def check_evidence(folder: Path, gates: dict, identity: dict, intent: str | None) -> list[str]:
    """Un gate passato deve poter essere riletto in `release-evidence.md`.

    Che cosa dicano quelle evidenze è giudizio; che i path siano dichiarati in un
    blocco, che il report esista come file e che l'identità sia nominata no.
    """
    evidence_file = folder / "release-evidence.md"
    if not evidence_file.is_file():
        return []
    started = [
        key for key in ("prose_review", "release") if gates.get(key) not in (None, "pending")
    ]
    if not started:
        return []
    text = evidence_file.read_text(encoding="utf-8")
    violations: list[str] = []

    if gates.get("prose_review") == "passed":
        expected = VERIFY_PROSE_REVIEWED if intent == "verify" else PROSE_REVIEWED
        declared = reviewed_paths(text)
        if not declared:
            violations.append(
                "`prose_review: passed` ma release-evidence.md non ha un blocco "
                "«File revisionati» con i path elencati"
            )
        else:
            absent = [
                name for name in expected if not any(name in path for path in declared)
            ]
            if absent:
                violations.append(
                    "`prose_review: passed` ma questi file non sono fra quelli dichiarati "
                    "revisionati: " + ", ".join(absent)
                )

    if gates.get("release") in VERDICTS:
        reports = [
            candidate
            for candidate in MARKDOWN_PATH.findall(text)
            if (folder / candidate).is_file() or Path(candidate).is_file()
        ]
        if not reports:
            violations.append(
                f"`gates.release: {gates['release']}` senza il path di un report del gate "
                "che esista davvero"
            )
        marker = next(
            (
                str(identity.get(key))
                for key in ("commit", "digest", "content_snapshot")
                if identity.get(key)
            ),
            None,
        )
        if marker and marker not in text:
            violations.append(
                f"il verdetto è registrato ma release-evidence.md non nomina l'identità "
                f"a cui si riferisce ({marker[:16]})"
            )
    return violations


def list_deliveries(root: Path) -> list[dict]:
    """Le delivery sotto la radice, dalla più recente: slug, stato, target, data.

    Chi torna dopo una settimana ricorda il sito, non lo slug: senza questo
    elenco il modello aprirebbe un frontmatter per cartella a ogni `resume`.
    """
    found: list[dict] = []
    if not root.is_dir():
        return found
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        delivery = folder / "delivery.md"
        entry = {
            "folder": str(folder),
            "slug": folder.name,
            "readable": delivery.is_file(),
            "status": None,
            "intent": None,
            "target": None,
            "updated_at": None,
        }
        if delivery.is_file():
            frontmatter = parse_frontmatter(delivery.read_text(encoding="utf-8")) or {}
            for field in ("slug", "status", "intent", "target", "updated_at"):
                if frontmatter.get(field):
                    entry[field] = frontmatter[field]
        found.append(entry)
    return sorted(found, key=lambda e: str(e["updated_at"] or ""), reverse=True)


def terminal_requirements(
    state: str,
    artifacts_open: list[str],
    gates: dict,
    verified: list[str],
    media_summary: dict | None,
    media_readable: bool,
) -> list[str]:
    """Cosa deve essere vero per stare in `release-approved` o `released`."""
    violations: list[str] = []
    if artifacts_open:
        violations.append(f"`{state}` con artefatti aperti: {', '.join(artifacts_open)}")
    if gates.get("substantive_review") != "passed":
        violations.append(f"`{state}` senza review sostanziale passata")
    if gates.get("prose_review") != "passed":
        violations.append(f"`{state}` senza review di prosa passata")
    if gates.get("release") not in ("GO", "GO_CON_CONDIZIONI"):
        violations.append(
            f"`{state}` senza verdetto favorevole del release gate; "
            f"trovato: {gates.get('release')!r}"
        )
    if not verified:
        violations.append(
            f"`{state}` senza identificatore immutabile verificato: servono un commit "
            "hash, un artefatto il cui SHA-256 corrisponde al digest, o uno snapshot "
            "dei contenuti"
        )
    # Una tabella illeggibile non e' una delivery senza media: e' una delivery
    # di cui non si sa niente, e non puo' passare per completa.
    if not media_readable:
        violations.append(f"`{state}` con la tabella dei media non leggibile")
    elif media_summary:
        pending = media_summary["by_state"]["pending"]
        blocked = media_summary["by_state"]["blocked"]
        if pending:
            violations.append(f"`{state}` con {pending} media ancora pendenti")
        if blocked:
            violations.append(f"`{state}` con {blocked} media bloccati")
    return violations


def check(
    folder: Path,
    transition_to: str | None,
    expected_media: dict | None = None,
    initializing: bool = False,
) -> dict:
    violations: list[str] = []
    delivery = folder / "delivery.md"
    # Quali file servano dipende dall'intento, che sta dentro il file che si sta
    # per leggere: si guarda prima, e in mancanza si assume la delivery completa.
    intent_hint = None
    if delivery.is_file():
        peek = parse_frontmatter(delivery.read_text(encoding="utf-8")) or {}
        intent_hint = peek.get("intent")
    required = VERIFY_REQUIRED_FILES if intent_hint == "verify" else DELIVERY_FILES
    missing = [name for name in required if not (folder / name).is_file()]
    # Durante l'inizializzazione i file nascono uno alla volta: segnalarli come
    # violazioni renderebbe impossibile seguire l'istruzione che li crea.
    if not initializing:
        for name in missing:
            violations.append(f"file della delivery mancante: {name}")

    if not delivery.is_file():
        return {
            "folder": str(folder),
            "frontmatter": None,
            "media": None,
            "missing_files": missing,
            "violations": violations,
            "ok": not violations if initializing else False,
        }

    frontmatter = parse_frontmatter(delivery.read_text(encoding="utf-8"))
    if frontmatter is None:
        violations.append("delivery.md non ha frontmatter: lo stato non e' leggibile")
        return {
            "folder": str(folder),
            "frontmatter": None,
            "media": None,
            "missing_files": missing,
            "violations": violations,
            "ok": False,
        }

    if frontmatter.get("schema") != SCHEMA:
        violations.append(f"campo `schema` assente o diverso da `{SCHEMA}`")

    slug = frontmatter.get("slug")
    if not slug:
        violations.append("campo `slug` vuoto")
    else:
        if slug != folder.name:
            violations.append(f"`slug` ({slug}) non coincide con la cartella ({folder.name})")
        if not SLUG.match(str(slug)):
            violations.append(
                f"`slug` ({slug}) non e' normalizzato: minuscole, cifre, punti e trattini"
            )

    if not frontmatter.get("target"):
        violations.append("campo `target` vuoto: la delivery non dice dove consegna")

    intent = frontmatter.get("intent")
    if intent not in INTENTS:
        violations.append(f"`intent` deve essere uno fra {sorted(INTENTS)}; trovato: {intent!r}")

    status = frontmatter.get("status")
    if status not in STATUSES:
        violations.append(f"`status` fuori enum; trovato: {status!r}")

    artifacts = frontmatter.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        violations.append("`artifacts` mancante o non e' una mappa")
    for key in ARTIFACT_KEYS:
        value = artifacts.get(key)
        if value not in ARTIFACT_VALUES:
            violations.append(f"`artifacts.{key}` fuori enum; trovato: {value!r}")
        elif value == "not-applicable" and not (
            intent == "verify" and key in VERIFY_OPTIONAL_ARTIFACTS
        ):
            violations.append(
                f"`artifacts.{key}: not-applicable` vale solo per `intent: verify` "
                f"su {', '.join(VERIFY_OPTIONAL_ARTIFACTS)}"
            )

    gates = frontmatter.get("gates")
    if not isinstance(gates, dict):
        gates = {}
        violations.append("`gates` mancante o non e' una mappa")
    for key, allowed in (
        ("substantive_review", REVIEW_VALUES),
        ("prose_review", REVIEW_VALUES),
        ("release", RELEASE_VALUES),
    ):
        value = gates.get(key)
        if value not in allowed:
            violations.append(f"`gates.{key}` fuori enum; trovato: {value!r}")

    authorized = frontmatter.get("implementation_authorized") is True
    scope = str(frontmatter.get("authorization_scope") or "")
    if authorized and not scope:
        violations.append("`implementation_authorized` senza `authorization_scope`")

    # Entrare in `implementing` significa toccare il sito: l'autorizzazione va
    # registrata prima, e deve nominare *questo* target.
    entering = transition_to if transition_to else status
    if entering == "implementing":
        if not authorized:
            violations.append(
                "`implementing` senza `implementation_authorized: true`: "
                "il silenzio non è consenso"
            )
        elif delivery_target_of(frontmatter) and not tokens(scope) & tokens(
            delivery_target_of(frontmatter)
        ):
            violations.append(
                f"`authorization_scope` ({scope}) non nomina il target "
                f"({delivery_target_of(frontmatter)}): un'autorizzazione per un altro "
                "ambiente non vale per questo"
            )

    blockers = frontmatter.get("blockers") or []
    if status == "blocked" and not blockers:
        violations.append("`status: blocked` senza nessun blocker elencato")
    # Una delivery bloccata *è* incoerente: le violazioni che i suoi blocker già
    # dichiarano sono la registrazione del blocco, non un difetto da correggere.
    blocking_state = status == "blocked" and bool(blockers)

    media_summary: dict | None = None
    media_readable = False
    media_file = folder / "media-map.md"
    if media_file.is_file():
        rows, problems = parse_media_table(media_file.read_text(encoding="utf-8"))
        violations.extend(problems)
        media_readable = not problems
        media_summary, media_violations = check_media(rows)
        media_summary["readable"] = media_readable
        violations.extend(media_violations)
        if expected_media:
            violations.extend(check_expected_media(rows, expected_media))
            media_summary["expected_checked"] = len(expected_media)

    artifacts_open = [
        key for key in ARTIFACT_KEYS if artifacts.get(key) in ("pending", "blocked")
    ]
    media_open = bool(media_summary) and bool(
        media_summary["by_state"]["pending"] or media_summary["by_state"]["blocked"]
    )
    gates_started = [
        key
        for key in ("substantive_review", "prose_review", "release")
        if gates.get(key) not in (None, "pending")
    ]
    if artifacts_open and gates_started:
        violations.append(
            "gate avviati con artefatti aperti: "
            f"{', '.join(gates_started)} contro {', '.join(artifacts_open)}"
        )
    if media_open and gates_started:
        violations.append(
            "gate avviati con media aperti: "
            f"{', '.join(gates_started)} contro pending/blocked nella media-map"
        )

    identity = frontmatter.get("release_identity") if isinstance(
        frontmatter.get("release_identity"), dict
    ) else {}
    declared_digest = str(identity.get("digest") or "")
    verified = immutable(
        str(identity.get("commit") or ""),
        declared_digest,
        str(identity.get("content_snapshot") or ""),
        digest_matches(identity.get("artifact"), declared_digest, folder),
    )
    identity_target = str(identity.get("target") or "")
    delivery_target = str(frontmatter.get("target") or "")
    if identity_target and delivery_target and identity_target != delivery_target:
        violations.append(
            f"`release_identity.target` ({identity_target}) non coincide con "
            f"`target` ({delivery_target}): il candidato è congelato per un altro ambiente"
        )

    # I requisiti terminali si valutano sullo stato in cui si sta *entrando*.
    # Valutarli su quello corrente li farebbe scattare solo dopo che la
    # promozione e' stata scritta, cioe' quando non servono piu'.
    target_state = transition_to if transition_to in TERMINAL_OK else status
    if target_state in TERMINAL_OK:
        violations.extend(
            terminal_requirements(
                target_state, artifacts_open, gates, verified, media_summary, media_readable
            )
        )

    violations.extend(check_evidence(folder, gates, identity, intent))

    transition = None
    if transition_to:
        allowed = TRANSITIONS.get(status, set()) if status in STATUSES else set()
        ok = transition_to in allowed
        transition = {"from": status, "to": transition_to, "allowed": ok}
        if transition_to not in STATUSES:
            violations.append(f"transizione verso uno stato inesistente: {transition_to}")
        elif not ok:
            violations.append(
                f"transizione `{status}` → `{transition_to}` non ammessa; "
                f"da qui si va a: {', '.join(sorted(allowed)) or 'nessuno stato'}"
            )

    return {
        "folder": str(folder),
        "frontmatter": {
            "slug": slug,
            "intent": intent,
            "status": status,
            "target": frontmatter.get("target"),
            "updated_at": frontmatter.get("updated_at"),
            "artifacts": artifacts,
            "gates": gates,
            "blockers": blockers,
            "immutable_identity": verified,
        },
        "media": media_summary,
        "missing_files": missing,
        "blocking_state": blocking_state,
        "transition": transition,
        "violations": violations,
        "ok": not violations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica lo stato persistito di una delivery WordPress: presenza dei cinque "
            "file, schema e enum del frontmatter, coerenza fra artefatti, gate, media e "
            "stato, e ammissibilita' di una transizione."
        )
    )
    parser.add_argument(
        "folder",
        nargs="?",
        help="cartella della delivery ({output_folder}/wordpress/{slug})",
    )
    parser.add_argument(
        "--transition-to",
        help="stato verso cui si vuole passare: verifica che la transizione sia ammessa",
    )
    parser.add_argument(
        "--slugify",
        metavar="NOME",
        help="normalizza un nome libero in slug e termina, senza leggere nessuna cartella",
    )
    parser.add_argument(
        "--list",
        dest="list_root",
        metavar="RADICE",
        help="elenca le delivery sotto {output_folder}/wordpress e termina",
    )
    parser.add_argument(
        "--initializing",
        action="store_true",
        help="la delivery sta nascendo: i file non ancora scritti non sono violazioni",
    )
    parser.add_argument(
        "--expected-media",
        metavar="FILE.json",
        help='identità attesa per asset: {"logo.png": {"mime": "image/png", "dimensions": "640×320"}}',
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_root:
        print(json.dumps(list_deliveries(Path(args.list_root)), ensure_ascii=False, indent=2))
        return 0

    if args.slugify is not None:
        slug = slugify(args.slugify)
        print(json.dumps({"input": args.slugify, "slug": slug}, ensure_ascii=False))
        if not slug:
            print("errore: il nome non produce nessuno slug", file=sys.stderr)
            return 1
        return 0

    if not args.folder:
        print("errore: serve la cartella della delivery, oppure --slugify", file=sys.stderr)
        return 2

    folder = Path(args.folder)
    if folder.is_file() and folder.name == "delivery.md":
        folder = folder.parent
    if not folder.is_dir():
        print(f"errore: cartella non leggibile: {folder}", file=sys.stderr)
        return 2

    expected_media = None
    if args.expected_media:
        try:
            expected_media = json.loads(Path(args.expected_media).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"errore: identità attese non leggibili: {error}", file=sys.stderr)
            return 2

    try:
        result = check(folder, args.transition_to, expected_media, args.initializing)
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose:
        for line in result["violations"]:
            print(f"violazione: {line}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
