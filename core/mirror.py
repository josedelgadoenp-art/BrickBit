"""Modo Espejo: proyección visual simbólica de tu 'yo' futuro.

Toma una foto del usuario y genera dos versiones estilizadas de su futuro:
la vida protegida (cálida, nítida, vibrante) y la desprotegida (apagada,
erosionada). Es una estilización simbólica hecha con procesamiento de imagen
local — en producción se conectaría a un modelo generativo de envejecimiento
facial con consentimiento explícito.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def preparar(img_bytes: bytes, lado: int = 460) -> Image.Image:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img.thumbnail((lado, lado))
    return img


def version_protegida(img: Image.Image) -> Image.Image:
    """Futuro blindado: cálido, luminoso, con vida."""
    out = ImageEnhance.Color(img).enhance(1.22)
    out = ImageEnhance.Brightness(out).enhance(1.07)
    out = ImageEnhance.Contrast(out).enhance(1.06)
    out = out.filter(ImageFilter.SMOOTH_MORE)
    a = np.asarray(out).astype(np.int16)
    a[..., 0] = np.clip(a[..., 0] + 14, 0, 255)   # calidez (rojo arriba)
    a[..., 2] = np.clip(a[..., 2] - 8, 0, 255)    # menos azul frío
    return Image.fromarray(a.astype(np.uint8))


def version_desprotegida(img: Image.Image) -> Image.Image:
    """Futuro expuesto: desaturado, erosionado, con viñeta y grano."""
    out = ImageEnhance.Color(img).enhance(0.30)
    out = ImageEnhance.Brightness(out).enhance(0.80)
    out = ImageEnhance.Contrast(out).enhance(0.90)
    out = out.filter(ImageFilter.GaussianBlur(0.7))
    a = np.asarray(out).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((yy - h / 2) / (h / 2)) ** 2 + ((xx - w / 2) / (w / 2)) ** 2)
    vineta = np.clip(1 - 0.5 * np.clip(d - 0.5, 0, None), 0.42, 1)[..., None]
    grano = np.random.default_rng(3).normal(0, 10, a.shape)
    a = np.clip(a * vineta + grano, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def espejo(img_bytes: bytes) -> tuple[Image.Image, Image.Image]:
    """(futuro_protegido, futuro_desprotegido)."""
    base = preparar(img_bytes)
    return version_protegida(base), version_desprotegida(base)
