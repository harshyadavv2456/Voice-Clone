# Security

Never publish voice recordings, source keys, output private keys, or generated audio in public issues.

- VOICE_SOURCE_KEY is a GitHub Actions secret that decrypts the encrypted source recording.
- VOICE_OUTPUT_PRIVATE.pem decrypts generated speech; keep it private and off the repository.
- Review changes to trusted workflow code before running it with secrets.
- Report security concerns privately to the repository owner.
