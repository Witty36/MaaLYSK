import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify_apk  # noqa: E402

DIGEST = "a" * 64


class CertificateParseTests(unittest.TestCase):
    def test_standard_apksigner_line(self):
        output = (
            "Verifies\n"
            "Verified using v2 scheme (APK Signature Scheme v2): true\n"
            "Number of signers: 1\n"
            "Signer #1 certificate DN: CN=Android Debug,O=Android,C=US\n"
            f"Signer #1 certificate SHA-256 digest: {DIGEST}\n"
            "Signer #1 certificate SHA-1 digest: 0123456789abcdef\n"
        )
        self.assertEqual(verify_apk._parse_certificate(output), DIGEST)

    def test_case_and_digest_spacing(self):
        output = "Signer #1 Certificate Sha256 Digest:  \n" + DIGEST.upper() + "\n"
        self.assertEqual(verify_apk._parse_certificate(output), DIGEST)

    def test_missing_line(self):
        self.assertEqual(
            verify_apk._parse_certificate("Verifies\nNumber of signers: 1\n"), ""
        )


if __name__ == "__main__":
    unittest.main()
