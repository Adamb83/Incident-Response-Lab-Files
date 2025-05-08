import os
import fnmatch
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

########################
# PASTE YOUR MATCHING RSA PRIVATE KEY HERE
########################
private_key_pem = b"""-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAwdNoJTbDX4UcCKV0OHd9cvdl+VVR3h0dE2ff19w2/Mieb1fh
pRg6S/YJ2JWzrasI8dLHjnkMc93fAISUIK9H8anWGU2V0EzUIXviNunCyXY908XR
TgTsgVy0etPEcrl5XUmZNkHmvUZ7anmP2n9tQyQKm/puFiXKU8UivsJqE+LeqSHj
NEwuBquuH9bhApoL0BcHjxvQwwi+rvIxKPaW/tavvK5E6DFrC8TOwxjK5f76sPHh
fCU21v0LGJ+TSBt8T0215YyUNI+9OX8NHftblY2tM+iPP0f1Yp6pUU6oFpQC3Usi
tn2q4HQiP0xg5HsyWVfin6NT4sCKyMSjHxnTfwIDAQABAoIBAB+2OYNhLtz5d8k4
XMgCUM2XCaGeIntfMwsiQx7bokmAf1+DNuFekecstZawg4nGAnwiOtEmH/HzGpHI
nz2rv+8blPJl3b2LXGewD6ZhX6O7i0kTQ/fqWVGe+85eyHTmwKMRMBaO+LP+DKIy
imU61QMXqf60Hf/UpgJHrjQcteNTwaGSQds0Q7/CsK6FV8u90HJnmIyhc4aJg6hQ
DVCVGT0pPbtJqlAetzwSnhoKOfPVzzDOYQYEO8m4WAi8HXza+qtwWlO9K/WhQ91v
5zraulBSkx99Pc4mit+n7oVQolMDW8RHCVCUMWJvTRgOruNqwjEXAA+W+UJgB0qM
loUeT6kCgYEA5hLHBPOaZCTc/GcqTckzhO/PkHY9qnvr07i75gcnNEw1QyUCLXXW
8pkdSEU9ENcSeiBY9pv7ocT8uyXrVWR+ISFj6mo8nY4MIVRpTRyIZUdx+9Qy5Yo/
GxVR/gAqVrozzjCKweu2frWNTk7Layv0pUKcq+UjYlUEjkmuDlsby9cCgYEA16rz
KCKJlYwiIHwK+zjJ/2dpKnoNEnlGAIl34AmUOjw/KDnDI/lp684ceRgPLXsMLwpx
HzND6MDe57IkdgUfws+VHZ8c7QWIBqWwuxTNALaivkbb5EmBTTtKWV85dLE/RoGX
EnSTuQPoyPLKBMulXwaKGWhnmDqVKVsTWzjLAJkCgYEArVBt3fwITPI8CmNIyeoM
RlNEoAWCdJ//SbG60hCHZu0VnmwNlONVNdFD7sJBuyLZB2jAu51LVFSJMg3hlqUq
Ipj9pIO8/88WsjDdVjptQSYt5k+2u5WF7kgESPwk6MpB5kxI6sY+5nqrZNcUg7pM
BAYG8bKeEiALW4iDdssJSGcCgYAt9lnR8OJfg7j2MVlpxuWNz+0ix1Yn3L6leKaa
kZAMhTB0kzLaZNpFDe0VhaIecD3dfJ01KAjN/uTCfj21BUyKiRDfejyA6w/dUsyC
YmF6SHIQmStd0KiE3CDxQREOpIO2tAGNRlkBMisXQF77fKcmxE8EMTL6x2looedT
Jpxk6QKBgEyBsMZwgAVRd5QteJlv/K1M9pwaU52orDuapDi1S/LG78+gL67XAx9k
oi0kgGecAgCT5dyL26WZfPKm649hdaZHj5lVlBZ5UK1KlymjaoKYcj+vM7dfiK4j
7Waciso1tjV4gG7inELMsD6jjVtdN1sFVRbs+IXHQtVmLabFR4XV
-----END RSA PRIVATE KEY-----
"""

########################
# AUTO-DETECT FOLDERS (WINDOWS)
########################

user_profile = Path(os.environ["USERPROFILE"])
documents_folder = user_profile / "Documents"
pictures_folder = user_profile / "Pictures"

FOLDERS_TO_DECRYPT = [
    str(documents_folder),
    str(pictures_folder),
]

########################
# OTHER CONFIG
########################
ENCRYPTED_FILE_EXTENSION = ".enc"
ENCRYPTED_KEY_FILENAME = "encrypted_key.bin"
OUTPUT_SUFFIX = "_decrypted"

def load_private_key_from_pem(pem_data: bytes):
    private_key = serialization.load_pem_private_key(
        pem_data,
        password=None
    )
    return private_key

def decrypt_aes_key_with_rsa(encrypted_aes_key: bytes, private_key):
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return aes_key

def decrypt_file_with_aes(encrypted_file: str, aes_key: bytes):
    with open(encrypted_file, 'rb') as ef:
        iv = ef.read(16)
        ciphertext = ef.read()

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

    pad_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-pad_length]

    base_name = encrypted_file.replace(ENCRYPTED_FILE_EXTENSION, "")
    output_file = base_name + OUTPUT_SUFFIX
    with open(output_file, 'wb') as out:
        out.write(decrypted_data)

    return output_file

def main():
    print("[+] Loading RSA private key...")
    private_key = load_private_key_from_pem(private_key_pem)

    print("[+] Reading RSA-encrypted AES key...")
    with open(ENCRYPTED_KEY_FILENAME, 'rb') as ek:
        encrypted_aes_key = ek.read()

    print("[+] Decrypting AES key...")
    aes_key = decrypt_aes_key_with_rsa(encrypted_aes_key, private_key)

    # Find and decrypt all .enc files
    for folder in FOLDERS_TO_DECRYPT:
        if not os.path.exists(folder):
            print(f"[-] Folder does not exist: {folder}")
            continue

        print(f"[+] Searching folder for .enc files: {folder}")
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if filename.endswith(ENCRYPTED_FILE_EXTENSION):
                    enc_file_path = os.path.join(root, filename)
                    print(f"    Decrypting: {enc_file_path}")
                    output_path = decrypt_file_with_aes(enc_file_path, aes_key)
                    print(f"    -> Output: {output_path}")

    print("[+] Decryption complete.")

if __name__ == "__main__":
    main()
