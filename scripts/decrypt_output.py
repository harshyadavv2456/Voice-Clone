#!/usr/bin/env python3
"""Decrypt voice-output.vcenc locally using the private output key."""
from __future__ import annotations
import argparse, io, tarfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"VCOUT1\x00\x00"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("encrypted_file", type=Path)
    ap.add_argument("--private-key", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, default=Path.home() / "voice-clone-output")
    args = ap.parse_args()
    data = args.encrypted_file.read_bytes()
    if len(data) < 10 or data[:8] != MAGIC:
        raise SystemExit("This is not a Voice-Clone encrypted output file.")
    n = int.from_bytes(data[8:10], "big")
    if n < 1 or len(data) < 10 + n + 12 + 16:
        raise SystemExit("Encrypted output appears truncated.")
    priv = serialization.load_pem_private_key(args.private_key.read_bytes(), password=None)
    key = priv.decrypt(data[10:10+n], padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=b"Voice-Clone output v1"))
    plain = AESGCM(key).decrypt(data[10+n:10+n+12], data[10+n+12:], b"Voice-Clone output v1")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(plain), mode="r:gz") as tf:
        wanted = {"voice-output.wav", "run-info.json"}
        members = tf.getmembers()
        if any(m.name not in wanted or not m.isfile() for m in members) or {m.name for m in members} != wanted:
            raise SystemExit("Archive contents are unexpected; refusing extraction.")
        for name in sorted(wanted):
            stream = tf.extractfile(name)
            if stream is None:
                raise SystemExit("Expected output file is missing.")
            (args.output_dir / name).write_bytes(stream.read())
    print(f"Decrypted files saved in: {args.output_dir}")

if __name__ == "__main__":
    main()
