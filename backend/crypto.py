import os
from cryptography.fernet import Fernet

class DoubleKeyCrypto:
    @staticmethod
    def encrypt_identity(identity_text: str) -> tuple[str, str, str]:
        """
        Encrypts an identity string and splits the decryption key into two shares:
        one for the Auditor and one for the Admin.
        
        Returns:
            ciphertext (str), share_auditor (hex string), share_admin (hex string)
        """
        # Generate raw Fernet key (32 bytes urlsafe base64)
        raw_key = Fernet.generate_key()
        
        # Split the key using 2-of-2 secret sharing (XOR split)
        # Convert base64 key bytes to raw bytes
        key_bytes = raw_key
        share_a = os.urandom(len(key_bytes))
        
        # XOR to create share_b
        share_b = bytes(b1 ^ b2 for b1, b2 in zip(key_bytes, share_a))
        
        # Encrypt the text using the original key
        cipher = Fernet(raw_key)
        ciphertext = cipher.encrypt(identity_text.encode('utf-8')).decode('utf-8')
        
        # Return hex-encoded shares and ciphertext
        return ciphertext, share_a.hex(), share_b.hex()

    @staticmethod
    def decrypt_identity(ciphertext: str, share_auditor_hex: str, share_admin_hex: str) -> str:
        """
        Reconstructs the Fernet key from the Auditor and Admin shares and decrypts the ciphertext.
        """
        try:
            share_a = bytes.fromhex(share_auditor_hex)
            share_b = bytes.fromhex(share_admin_hex)
            
            if len(share_a) != len(share_b):
                raise ValueError("Key shares size mismatch")
                
            # Reconstruct the original Fernet key bytes
            reconstructed_key = bytes(b1 ^ b2 for b1, b2 in zip(share_a, share_b))
            
            # Decrypt the text
            cipher = Fernet(reconstructed_key)
            decrypted = cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
            return decrypted
        except Exception as e:
            return f"[DECRYPTION FAILED - INVALID OR TAMPERED KEY SHARES: {e}]"
