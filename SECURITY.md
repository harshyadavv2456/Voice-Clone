# Security

Please do not report or publish voice recordings, voice-source keys, output private keys, or generated audio in public issues.

- `VOICE_SOURCE_KEY` is a repository Actions secret. Anyone who can change trusted workflow code and run it with secrets could access the source recording; review code changes carefully.
- `VOICE_OUTPUT_PRIVATE.pem` decrypts generated speech. Keep it offline/private; never commit it.
- The reference asset in `assets/voice-reference.mp3.enc` is encrypted with AES-256-GCM. The corresponding key is deliberately not stored in the repository.
- Report security problems privately to the repository owner rather than opening a public issue containing personal audio or keys.
