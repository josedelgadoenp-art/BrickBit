"""Certificados de Destino: cadena de bloques ligera para metas cumplidas.

Cada meta 100% financiada acuña un certificado encadenado por hash SHA-256
al anterior (una mini-blockchain de sesión). En producción se anclaría a una
red pública o a un ledger permisionado de GNP para verificación externa,
convirtiendo cada logro en un activo social compartible.
"""

from __future__ import annotations

import datetime
import hashlib
import json

import streamlit as st

GENESIS = "GNP-LIFEOS-GENESIS"


def _hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def cadena() -> list[dict]:
    return st.session_state.setdefault("ledger", [])


def acunar(meta: dict, perfil: dict) -> dict:
    """Acuña un Certificado de Destino para una meta financiada."""
    chain = cadena()
    bloque = {
        "indice": len(chain) + 1,
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "titular": perfil["nombre"] or "Prospecto GNP",
        "meta": meta["nombre"],
        "icono": meta["icono"],
        "anio_objetivo": meta["anio_objetivo"],
        "monto_blindado": round(meta["costo_futuro"], 2),
        "vehiculo": meta["producto"]["nombre"],
        "hash_previo": chain[-1]["hash"] if chain else _hash({"genesis": GENESIS}),
    }
    bloque["hash"] = _hash(bloque)
    chain.append(bloque)
    return bloque


def verificar() -> tuple[bool, int]:
    """Verifica la integridad de la cadena. (ok, bloques_validos)."""
    chain = cadena()
    previo = _hash({"genesis": GENESIS})
    for i, b in enumerate(chain):
        cuerpo = {k: v for k, v in b.items() if k != "hash"}
        if b["hash_previo"] != previo or _hash(cuerpo) != b["hash"]:
            return False, i
        previo = b["hash"]
    return True, len(chain)


def certificado_md(b: dict) -> str:
    return "\n".join([
        "# 🔗 Certificado de Destino GNP",
        "",
        f"## {b['icono']} {b['meta']}",
        "",
        f"- **Titular:** {b['titular']}",
        f"- **Meta blindada para:** {b['anio_objetivo']}",
        f"- **Monto garantizado:** ${b['monto_blindado']:,.0f} MXN",
        f"- **Vehículo GNP:** {b['vehiculo']}",
        f"- **Bloque #{b['indice']}** · acuñado el {b['ts']}",
        "",
        f"**Huella criptográfica (SHA-256):**",
        f"`{b['hash']}`",
        "",
        f"*Encadenado a:* `{b['hash_previo'][:24]}…`",
        "",
        "> Este certificado es verificable e inmutable: cualquier alteración rompe la cadena.",
        "> Demo conceptual — en producción se ancla a un ledger público auditable.",
    ])
