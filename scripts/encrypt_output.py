#!/usr/bin/env python3
"""Encrypt output with a random AES key wrapped to the owner's RSA public key."""
import os, secrets, tarfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
MAGIC = b"VCOUT1\x00\x00"

def main():
    out = Path("output")
    wav, info = out/"voice-output.wav", out/"run-info.json"
    if not wav.is_file() or not info.is_file():
        raise SystemExit("Generated output files are missing.")
    pub = serialization.load_pem_public_key(Path("keys/output_public.pem").read_bytes())
    key, nonce = AESGCM.generate_key(bit_length=256), secrets.token_bytes(12)
    archive = Path("work-output.tar.gz")
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(wav, arcname="voice-output.wav", recursive=False)
        tf.add(info, arcname="run-info.json", recursive=False)
    ciphertext = AESGCM(key).encrypt(nonce, archive.read_bytes(), b"Voice-Clone output v1")
    wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=b"Voice-Clone output v1"))
    artifact = Path("artifact"); artifact.mkdir(exist_ok=True)
    (artifact/"voice-output.vcenc").write_bytes(MAGIC + len(wrapped).to_bytes(2,"big") + wrapped + nonce + ciphertext)
    archive.unlink(missing_ok=True); wav.unlink(missing_ok=True); info.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
