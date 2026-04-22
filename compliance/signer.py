"""
Signs PDF files using Cloud KMS asymmetric signing key.
Provides sign() and verify() operations for tamper-evident compliance artifacts.
"""
from __future__ import annotations
import hashlib
import os


def sign_pdf(
    pdf_path: str,
    project: str = None,
    key_ring: str = None,
    key_id: str = None,
    location: str = "global",
) -> tuple:
    """
    Compute SHA-256 of PDF, sign with KMS asymmetric key.

    Args:
        pdf_path: Path to the PDF file to sign
        project: GCP project ID
        key_ring: KMS key ring name (default: fairlens-keys)
        key_id: KMS key name (default: compliance-signer)
        location: KMS location (default: global)

    Returns:
        (signed_pdf_bytes, signature_hex, sha256_hash)
    """
    project = project or os.environ.get("GCP_PROJECT_ID", "")
    key_ring = key_ring or os.environ.get("KMS_KEY_RING", "fairlens-keys")
    key_id = key_id or os.environ.get("KMS_KEY_ID", "compliance-signer")

    with open(pdf_path, "rb") as f:
        content = f.read()

    sha256_hash = hashlib.sha256(content).hexdigest()

    try:
        from google.cloud import kms

        client = kms.KeyManagementServiceClient()
        key_version_name = client.crypto_key_version_path(
            project, location, key_ring, key_id, "1"
        )

        digest_bytes = hashlib.sha256(content).digest()
        response = client.asymmetric_sign(
            request={
                "name": key_version_name,
                "digest": {"sha256": digest_bytes},
            }
        )

        signature_hex = response.signature.hex()
        print(f"[Compliance] PDF signed. SHA-256: {sha256_hash}")
        print(f"[Compliance] KMS signature length: {len(response.signature)} bytes")

        return (content, signature_hex, sha256_hash)

    except ImportError:
        print("[Compliance] google-cloud-kms not available. Returning unsigned hash.")
        return (content, "unsigned-" + sha256_hash[:32], sha256_hash)

    except Exception as e:
        print(f"[Compliance] KMS signing failed: {e}. Returning unsigned hash.")
        return (content, "unsigned-" + sha256_hash[:32], sha256_hash)


def verify(pdf_bytes: bytes, signature_hex: str, project: str = None,
           key_ring: str = None, key_id: str = None, location: str = "global") -> bool:
    """
    Verify a KMS signature against the PDF content.

    Args:
        pdf_bytes: Raw PDF file bytes
        signature_hex: Hex-encoded KMS signature
        project, key_ring, key_id, location: KMS coordinates

    Returns:
        True if signature is valid, False otherwise
    """
    if signature_hex.startswith("unsigned-"):
        # Fallback: verify by hash comparison
        expected_hash = signature_hex.replace("unsigned-", "")
        actual_hash = hashlib.sha256(pdf_bytes).hexdigest()[:32]
        return expected_hash == actual_hash

    project = project or os.environ.get("GCP_PROJECT_ID", "")
    key_ring = key_ring or os.environ.get("KMS_KEY_RING", "fairlens-keys")
    key_id = key_id or os.environ.get("KMS_KEY_ID", "compliance-signer")

    try:
        from google.cloud import kms

        client = kms.KeyManagementServiceClient()
        key_version_name = client.crypto_key_version_path(
            project, location, key_ring, key_id, "1"
        )

        # Get the public key
        public_key_response = client.get_public_key(request={"name": key_version_name})

        # Verify using cryptography library
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, utils

        public_key = serialization.load_pem_public_key(
            public_key_response.pem.encode("utf-8")
        )

        signature_bytes = bytes.fromhex(signature_hex)
        digest = hashlib.sha256(pdf_bytes).digest()

        public_key.verify(
            signature_bytes,
            digest,
            padding.PKCS1v15(),
            utils.Prehashed(hashes.SHA256()),
        )
        return True

    except Exception as e:
        print(f"[Compliance] Verification failed: {e}")
        return False
