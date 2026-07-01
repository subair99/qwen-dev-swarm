# Prompt
"""

Create an encrypted Key-Value Local Cache class named EncryptedKVCache.
Requirements:
1. Accept an isolated local file_path, master_password string, and pbkdf2_iterations.
2. Derivation Security: Derive base master encryption and MAC keys using PBKDF2-HMAC-SHA256 with a unique salt.
3. CRITICAL - CRYPTOGRAPHIC KEY ISOLATION (No Keystream Reuse): 
   To eliminate the risk of XOR stream cipher vulnerabilities (C1 ^ C2 = P1 ^ P2), implement a Per-Item Key Derivation Strategy. For every item written to disk via set(), derive unique encryption and authentication sub-keys by passing a combination of the global salt and the specific item's 'key' string into a secondary fast hashing pass or derivation block.
4. Cipher Construction: Build an authenticated stream cipher using an incremental block counter (CTR format via struct.pack) and hashlib.sha256.
5. Authenticate via Encrypt-then-MAC using hmac.new and constant-time validation (hmac.compare_digest).
6. File Operations: Write modifications atomically using temporary file staging (os.replace) to eliminate disk-corruption risks inside the sandbox execution thread.

"""


import os
import json
import hmac
import hashlib
import struct
import base64
import tempfile

class EncryptedKVCache:
    def __init__(self, file_path: str, master_password: str, pbkdf2_iterations: int):
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("file_path must be a non-empty string.")
        if not isinstance(master_password, str):
            raise TypeError("master_password must be a string.")
        if not isinstance(pbkdf2_iterations, int) or pbkdf2_iterations <= 0:
            raise ValueError("pbkdf2_iterations must be a strictly positive integer.")

        self._file_path = file_path
        self._cache = {}

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                self._salt = f.read(32)
                if len(self._salt) != 32:
                    raise ValueError("Invalid file format: global salt is missing or corrupt.")
                json_data = f.read()
                if json_data:
                    self._cache = json.loads(json_data.decode('utf-8'))
        else:
            self._salt = os.urandom(32)

        self._master_material = hashlib.pbkdf2_hmac(
            'sha256',
            master_password.encode('utf-8'),
            self._salt,
            pbkdf2_iterations,
            dklen=64
        )

    def _derive_sub_keys(self, key: str) -> tuple:
        key_bytes = key.encode('utf-8')
        item_seed = hashlib.sha256(self._master_material + self._salt + key_bytes).digest()
        sub_enc_key = hashlib.sha256(item_seed + b'enc').digest()
        sub_mac_key = hashlib.sha256(item_seed + b'mac').digest()
        return sub_enc_key, sub_mac_key

    def _generate_keystream(self, length: int, nonce: bytes, sub_enc_key: bytes) -> bytes:
        keystream = bytearray()
        required_blocks = (length + 31) // 32
        for counter in range(required_blocks):
            block_input = nonce + struct.pack('>I', counter)
            keystream.extend(hashlib.sha256(sub_enc_key + block_input).digest())
        return bytes(keystream[:length])

    def _encrypt(self, plaintext: bytes, sub_enc_key: bytes, sub_mac_key: bytes) -> dict:
        nonce = os.urandom(12)
        keystream = self._generate_keystream(len(plaintext), nonce, sub_enc_key)
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream))
        mac = hmac.new(sub_mac_key, nonce + ciphertext, hashlib.sha256).digest()
        
        return {
            'nonce': base64.b64encode(nonce).decode('ascii'),
            'ct': base64.b64encode(ciphertext).decode('ascii'),
            'mac': base64.b64encode(mac).decode('ascii')
        }

    def _decrypt(self, item: dict, sub_enc_key: bytes, sub_mac_key: bytes) -> bytes:
        nonce = base64.b64decode(item['nonce'])
        ciphertext = base64.b64decode(item['ct'])
        mac = base64.b64decode(item['mac'])

        expected_mac = hmac.new(sub_mac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("MAC verification failed. Data corrupted or tampered.")

        keystream = self._generate_keystream(len(ciphertext), nonce, sub_enc_key)
        return bytes(c ^ k for c, k in zip(ciphertext, keystream))

    def _save_to_disk(self):
        json_data = json.dumps(self._cache).encode('utf-8')
        dir_name = os.path.dirname(self._file_path) or '.'
        
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(dir=dir_name)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(self._salt)
                f.write(json_data)
            os.replace(tmp_path, self._file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def set(self, key: str, value) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string.")
        
        sub_enc_key, sub_mac_key = self._derive_sub_keys(key)
        plaintext = json.dumps(value).encode('utf-8')
        self._cache[key] = self._encrypt(plaintext, sub_enc_key, sub_mac_key)
        self._save_to_disk()

    def get(self, key: str):
        if not isinstance(key, str):
            raise TypeError("key must be a string.")
            
        if key not in self._cache:
            return None
            
        sub_enc_key, sub_mac_key = self._derive_sub_keys(key)
        plaintext = self._decrypt(self._cache[key], sub_enc_key, sub_mac_key)
        return json.loads(plaintext.decode('utf-8'))

    def delete(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string.")
            
        if key in self._cache:
            del self._cache[key]
            self._save_to_disk()