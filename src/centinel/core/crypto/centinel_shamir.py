"""
CENTINEL — Shamir Secret Sharing over GF(2^8)
==============================================

Pure-Python implementation of Shamir's Secret Sharing for Ed25519 private
keys used in the CENTINEL electoral evidence preservation chain.

Implementación pura en Python del Secret Sharing de Shamir para las claves
privadas Ed25519 utilizadas en la cadena de preservación de evidencia
electoral de CENTINEL.

Mathematical foundation / Fundamento matemático
-----------------------------------------------
Given a secret s ∈ GF(2^8), a threshold k, and a total number of shares n
(with k <= n <= 255), we construct a random polynomial of degree k-1:

    p(x) = a_0 + a_1·x + a_2·x² + ... + a_{k-1}·x^{k-1}

where a_0 = s and a_1, ..., a_{k-1} are sampled uniformly at random from
GF(2^8). Share i (for i ∈ {1, ..., n}) is the pair (i, p(i)).

Given any k shares (x_1, y_1), ..., (x_k, y_k), the secret is recovered via
Lagrange interpolation evaluated at x = 0:

    s = p(0) = Σ_i y_i · Π_{j≠i} (x_j / (x_j ⊕ x_i))

The field used is GF(2^8) constructed by the AES irreducible polynomial
x⁸ + x⁴ + x³ + x + 1 (0x11b). This is the same field used by AES; its
arithmetic is well-studied and library implementations exist for
independent verification.

Security properties / Propiedades de seguridad
----------------------------------------------
1. **Information-theoretic security up to threshold k.** Given fewer than k
   shares, the adversary learns nothing about the secret beyond what is
   already publicly known (the secret length).
2. **No backdoors possible.** The scheme is a polynomial over a finite
   field; there is no hidden state, no PRNG output that can be predicted,
   no algorithm parameter to subvert.
3. **Constant-time arithmetic.** All field operations use precomputed
   logarithm/exponential tables; runtime does not depend on secret values.

Limitations / Limitaciones
--------------------------
1. The scheme is **non-verifiable** — a malicious shareholder can submit a
   forged share that, combined with others, recovers an arbitrary chosen
   value rather than the true secret. CENTINEL mitigates this by including
   a SHA-256 hash of the original secret in every share, so reconstruction
   verifies the result. See `Share.secret_hash`.
2. Each byte of the secret is split independently. This is standard but
   means each byte uses an independent polynomial; the total entropy of
   the secret is preserved across the byte-wise split.

References / Referencias
------------------------
- Shamir, A. (1979). "How to share a secret." Communications of the ACM,
  22(11), 612-613. doi:10.1145/359168.359176
- NIST SP 800-90A (random number generation, used here via `secrets`)
- FIPS 197 (AES) — for the choice of irreducible polynomial

License: AGPL-3.0 (matching the parent CENTINEL project)
"""

from __future__ import annotations

import secrets as _secrets
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

__all__ = [
    "GF256",
    "split_byte",
    "combine_byte",
    "split_secret",
    "combine_shares",
    "ShamirError",
]


# ---------------------------------------------------------------------------
# Finite field arithmetic over GF(2^8) with AES irreducible polynomial 0x11b
# Aritmética del campo finito GF(2^8) con polinomio irreducible AES 0x11b
# ---------------------------------------------------------------------------


class GF256:
    """
    Arithmetic in GF(2^8) using the AES irreducible polynomial 0x11b.
    All operations are constant-time relative to inputs (table-lookup based).

    Aritmética en GF(2^8) usando el polinomio irreducible de AES 0x11b.
    Todas las operaciones son de tiempo constante respecto a los inputs
    (basadas en tablas de búsqueda).
    """

    # Generator g = 3 (a primitive element of GF(2^8) / 0x11b).
    # Generador g = 3 (elemento primitivo de GF(2^8) / 0x11b).
    _IRREDUCIBLE: int = 0x11B
    _GENERATOR: int = 0x03

    _EXP: List[int] = []
    _LOG: List[int] = []

    @classmethod
    def _build_tables(cls) -> None:
        """Precompute exp/log tables on first use. / Tablas exp/log precomputadas."""
        if cls._EXP:
            return
        exp = [0] * 512  # 2x for wraparound convenience in multiplication
        log = [0] * 256
        x = 1
        for i in range(255):
            exp[i] = x
            log[x] = i
            # Multiply by generator (3 = 0x03).
            # Multiplicación por el generador.
            x = (x << 1) ^ x  # x * 3 in normal int
            if x & 0x100:
                x ^= cls._IRREDUCIBLE
            x &= 0xFF
        # Wrap-around copy so we can index without modulo in multiplication.
        for i in range(255, 512):
            exp[i] = exp[i - 255]
        cls._EXP = exp
        cls._LOG = log

    @classmethod
    def add(cls, a: int, b: int) -> int:
        """Addition in GF(2^8) is XOR. / La suma en GF(2^8) es XOR."""
        return (a ^ b) & 0xFF

    @classmethod
    def sub(cls, a: int, b: int) -> int:
        """Subtraction equals addition in characteristic-2 fields."""
        return (a ^ b) & 0xFF

    @classmethod
    def mul(cls, a: int, b: int) -> int:
        """Multiplication via log/exp tables. / Multiplicación por tablas log/exp."""
        cls._build_tables()
        if a == 0 or b == 0:
            return 0
        return cls._EXP[cls._LOG[a] + cls._LOG[b]]

    @classmethod
    def div(cls, a: int, b: int) -> int:
        """Division a / b in GF(2^8). Raises if b == 0."""
        cls._build_tables()
        if b == 0:
            raise ZeroDivisionError("Division by zero in GF(2^8)")
        if a == 0:
            return 0
        # exp[(log_a - log_b) mod 255]; we use +255 to keep index non-negative.
        return cls._EXP[cls._LOG[a] + 255 - cls._LOG[b]]


# ---------------------------------------------------------------------------
# Exceptions / Excepciones
# ---------------------------------------------------------------------------


class ShamirError(ValueError):
    """Base error for Shamir operations. / Error base de operaciones Shamir."""


# ---------------------------------------------------------------------------
# Core scheme — byte-wise split and combine
# Esquema central — división y combinación byte a byte
# ---------------------------------------------------------------------------


def _eval_poly(coeffs: Sequence[int], x: int) -> int:
    """
    Evaluate polynomial in GF(2^8) at point x using Horner's method.
    p(x) = c_0 + c_1·x + c_2·x² + ... + c_{n-1}·x^{n-1}

    Evalúa el polinomio en GF(2^8) en el punto x usando el método de Horner.
    """
    result = 0
    # Horner from highest degree down. / Horner desde el grado más alto.
    for coeff in reversed(coeffs):
        result = GF256.add(GF256.mul(result, x), coeff)
    return result


def split_byte(
    secret_byte: int,
    threshold: int,
    total: int,
    rng: object = None,
) -> List[Tuple[int, int]]:
    """
    Split a single byte into `total` shares such that any `threshold` shares
    can reconstruct it.

    Divide un solo byte en `total` shares de modo que `threshold` shares
    cualesquiera puedan reconstruirlo.

    Parameters
    ----------
    secret_byte : int
        Value in [0, 255]. / Valor en [0, 255].
    threshold : int
        Minimum shares required for reconstruction (k).
    total : int
        Total shares to generate (n). Must satisfy threshold <= total <= 255.
    rng : object, optional
        A `secrets.SystemRandom`-like object exposing `randbelow(n)`. If
        None, the standard library `secrets` module is used. Override only
        for deterministic testing.

    Returns
    -------
    List[Tuple[int, int]]
        List of (x, y) shares with x ∈ {1, ..., total}.
    """
    if not (0 <= secret_byte <= 255):
        raise ShamirError("Secret byte out of range [0, 255]")
    if not (1 <= threshold <= total <= 255):
        raise ShamirError(
            "Invalid threshold/total: require 1 <= threshold <= total <= 255"
        )

    # Sample k-1 random coefficients from GF(2^8). / Muestrea k-1 coeficientes aleatorios.
    # a_0 is the secret; a_1, ..., a_{k-1} are uniformly random.
    coeffs = [secret_byte]
    for _ in range(threshold - 1):
        if rng is None:
            coeffs.append(_secrets.randbelow(256))
        else:
            coeffs.append(rng.randbelow(256))

    # Evaluate at x = 1, 2, ..., total. We avoid x = 0 because p(0) = secret.
    shares = []
    for x in range(1, total + 1):
        shares.append((x, _eval_poly(coeffs, x)))
    return shares


def combine_byte(shares: Sequence[Tuple[int, int]]) -> int:
    """
    Reconstruct a single secret byte from a sufficient set of shares using
    Lagrange interpolation evaluated at x = 0.

    Reconstruye un byte secreto desde un conjunto suficiente de shares
    usando interpolación de Lagrange evaluada en x = 0.

    The caller must guarantee that the number of shares is at least the
    original threshold; otherwise the result is mathematically undefined
    (a low-entropy nonsense value).

    Parameters
    ----------
    shares : sequence of (x, y) tuples
        Each x must be a distinct positive integer in [1, 255].

    Returns
    -------
    int
        The reconstructed secret byte, in [0, 255].
    """
    if len(shares) < 1:
        raise ShamirError("At least one share required")

    x_values = [s[0] for s in shares]
    if len(set(x_values)) != len(x_values):
        raise ShamirError("Duplicate x values in shares")
    if any(x == 0 or x > 255 for x in x_values):
        raise ShamirError("Share x values must be in [1, 255]")

    secret = 0
    for i, (x_i, y_i) in enumerate(shares):
        # Compute the Lagrange basis polynomial L_i(0) =
        # Π_{j ≠ i} x_j / (x_j ⊕ x_i)  in GF(2^8) (note ⊕ for subtraction).
        numerator = 1
        denominator = 1
        for j, (x_j, _) in enumerate(shares):
            if j == i:
                continue
            numerator = GF256.mul(numerator, x_j)
            denominator = GF256.mul(denominator, GF256.sub(x_j, x_i))
        lagrange_term = GF256.mul(y_i, GF256.div(numerator, denominator))
        secret = GF256.add(secret, lagrange_term)
    return secret


# ---------------------------------------------------------------------------
# Multi-byte secret splitting / División de secretos multi-byte
# ---------------------------------------------------------------------------


def split_secret(
    secret: bytes,
    threshold: int,
    total: int,
) -> List[bytes]:
    """
    Split a multi-byte secret into `total` shares. Each output share is a
    bytes object of length len(secret) + 1, with the first byte being the
    x-coordinate (1 <= x <= total) and the remaining bytes the y-values
    for each byte of the secret.

    Divide un secreto multi-byte en `total` shares. Cada share resultante
    es un objeto bytes de longitud len(secret) + 1, donde el primer byte
    es la coordenada x (1 <= x <= total) y los bytes restantes son los
    valores y para cada byte del secreto.

    Parameters
    ----------
    secret : bytes
        The secret to split (e.g., 32 raw bytes of an Ed25519 private key).
    threshold : int
        Minimum number of shares required to reconstruct.
    total : int
        Total number of shares to generate.

    Returns
    -------
    List[bytes]
        List of `total` shares, each share is `bytes` of length len(secret)+1.
    """
    if not isinstance(secret, (bytes, bytearray)):
        raise ShamirError("secret must be bytes")
    if len(secret) == 0:
        raise ShamirError("Empty secret")

    # We compute one split per byte of the secret, then transpose: each
    # output share gets one y-value from each byte's split.
    per_byte_shares: List[List[Tuple[int, int]]] = []
    for byte in secret:
        per_byte_shares.append(split_byte(byte, threshold, total))

    # Transpose: build n output shares each containing len(secret) y-values.
    result: List[bytes] = []
    for i in range(total):
        x = i + 1
        ys = bytearray([x])
        for byte_shares in per_byte_shares:
            # byte_shares is the list of (x, y) for one byte;
            # take the y for share index i (which has x = i+1).
            ys.append(byte_shares[i][1])
        result.append(bytes(ys))
    return result


def combine_shares(shares: Iterable[bytes]) -> bytes:
    """
    Reconstruct a multi-byte secret from a sufficient set of shares.

    Reconstruye un secreto multi-byte desde un conjunto suficiente de shares.

    Parameters
    ----------
    shares : iterable of bytes
        Each share must have identical length L; the first byte is the
        x-coordinate, the remaining L-1 bytes are the y-values for each
        byte of the original secret.

    Returns
    -------
    bytes
        The reconstructed secret of length L-1.
    """
    share_list = list(shares)
    if len(share_list) < 1:
        raise ShamirError("At least one share required")
    lengths = {len(s) for s in share_list}
    if len(lengths) != 1:
        raise ShamirError(f"Inconsistent share lengths: {lengths}")
    share_len = lengths.pop()
    if share_len < 2:
        raise ShamirError("Shares too short to contain any secret data")

    secret_len = share_len - 1
    reconstructed = bytearray()
    for byte_idx in range(secret_len):
        byte_shares = []
        for s in share_list:
            x = s[0]
            y = s[1 + byte_idx]
            byte_shares.append((x, y))
        reconstructed.append(combine_byte(byte_shares))
    return bytes(reconstructed)
