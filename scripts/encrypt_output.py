#!/usr/bin/env python3
"""Hybrid-encrypt generated output so only the private RSA-key holder can open it."""
from __future__ import annotations
import json, os, secrets, tarfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"VCOUT1\x00\x00"
OUT = Path("artifact/voice-output.vcenc")


def main() -> None:
    outdir = Path("output")
    wav = outdir / "voice-output.wav"
    info = outdir / "run-info.json"
    if not wav.is_file() or not info.is_file():
        raise SystemExit("Expected generated audio and run metadata are missing.")
    public_key = serialization.load_pem_public_key(Path("keys/output_public.pem").read_bytes())
    if public_key.key_size < 3072:
        raise SystemExit("Output public key is unexpectedly weak.")
    os.makedirs("artifact", exist_ok=True)
    archive = Path("work-output.tar.gz")
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(wav, arcname="voice-output.wav", recursive=False)
        tf.add(info, arcname="run-info.json", recursive=False)
    plaintext = archive.read_bytes()
    key = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, b"Voice-Clone output v1")
    wrapped = public_key.encrypt(
        key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=b"Voice-Clone output v1"),
    )
    OUT.write_bytes(MAGIC + len(wrapped).to_bytes(2, "big") + wrapped + nonce + ciphertext)
    archive.unlink(missing_ok=True)
    # Remove plaintext as soon as encrypted output is written.
    wav.unlink(missing_ok=True)
    info.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
