from __future__ import annotations

from typing import Any, List, Union

try:
    import tenseal as ts
    import numpy as np
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FullyHomomorphicEncryption:
    def __init__(self, use_real_fhe: bool = True) -> None:
        self.use_real_fhe: bool = use_real_fhe and TENSEAL_AVAILABLE

        if self.use_real_fhe:
            self.context = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=8192,
                coeff_mod_bit_sizes=[60, 40, 40, 60],
            )
            self.context.global_scale = 2 ** 40
            self.context.generate_galois_keys()
            logger.info("TenSEAL CKKS encryption initialized")
        else:
            from cryptography.fernet import Fernet
            self.key: bytes = Fernet.generate_key()
            self.cipher: Any = Fernet(self.key)
            logger.info("Using mock encryption (not true homomorphic)")

    def encrypt_value(self, value: float) -> Any:
        if self.use_real_fhe:
            return ts.ckks_vector(self.context, [float(value)])
        return self.cipher.encrypt(str(value).encode())

    def encrypt_vector(self, values: List[float]) -> Any:
        if self.use_real_fhe:
            return ts.ckks_vector(self.context, [float(v) for v in values])
        return [self.cipher.encrypt(str(v).encode()) for v in values]

    def decrypt_value(self, encrypted_value: Any) -> float:
        if self.use_real_fhe:
            return float(encrypted_value.decrypt()[0])
        return float(self.cipher.decrypt(encrypted_value).decode())

    def decrypt_vector(self, encrypted_vector: Any) -> List[float]:
        if self.use_real_fhe:
            return [float(x) for x in encrypted_vector.decrypt()]
        return [float(self.cipher.decrypt(v).decode()) for v in encrypted_vector]

    def compute_encrypted_mean(self, encrypted_vector: Any) -> Any:
        if self.use_real_fhe:
            n = len(encrypted_vector.decrypt())
            return encrypted_vector * (1.0 / n)
        decrypted = self.decrypt_vector(encrypted_vector)
        return self.encrypt_value(sum(decrypted) / len(decrypted))

    def compute_encrypted_comparison(self, encrypted_value: Any, threshold: float) -> Any:
        decrypted = self.decrypt_value(encrypted_value)
        result = 1.0 if decrypted > threshold else 0.0
        return self.encrypt_value(result)

    def serialize(self, encrypted_data: Any) -> bytes:
        if self.use_real_fhe:
            return encrypted_data.serialize()
        return encrypted_data

    def deserialize(self, serialized_data: bytes) -> Any:
        if self.use_real_fhe:
            return ts.ckks_vector_from(self.context, serialized_data)
        return serialized_data
