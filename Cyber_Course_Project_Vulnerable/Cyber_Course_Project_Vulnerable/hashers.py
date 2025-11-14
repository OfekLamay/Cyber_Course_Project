"""
Custom Password Hasher implementing HMAC + Salt as per project requirements
This hasher uses HMAC-SHA256 with salt, compatible with Django's password system
"""

import hashlib
import hmac
import os
import json
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare
from django.conf import settings


class HMACPasswordHasher(BasePasswordHasher):
    """
    HMAC + Salt password hasher as per project requirements
    Compatible with Django's authentication system
    """
    algorithm = 'hmac_salt'
    library = 'hmac'
    
    def encode(self, password, salt):
        """
        Encode password using HMAC + Salt
        """
        # Load HMAC key from config
        try:
            config_path = os.path.join(settings.BASE_DIR, 'config', 'password_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            hmac_key = config.get('security', {}).get('hmac_key', 'default_secret_key')
        except FileNotFoundError:
            hmac_key = 'default_secret_key'
        
        # Create HMAC hash
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        hmac_key_bytes = hmac_key.encode('utf-8')
        
        # HMAC with password + salt
        hmac_hash = hmac.new(
            hmac_key_bytes, 
            password_bytes + salt_bytes, 
            hashlib.sha256
        )
        
        hash_value = hmac_hash.hexdigest()
        
        # Return in Django's expected format: algorithm$salt$hash
        return f'{self.algorithm}${salt}${hash_value}'
    
    def verify(self, password, encoded):
        """
        Verify password against stored hash
        """
        algorithm, salt, hash_value = encoded.split('$', 2)
        assert algorithm == self.algorithm
        
        encoded_2 = self.encode(password, salt)
        return constant_time_compare(encoded, encoded_2)
    
    def safe_summary(self, encoded):
        """
        Return summary of the password hash for admin interface
        """
        algorithm, salt, hash_value = encoded.split('$', 2)
        assert algorithm == self.algorithm
        return {
            'algorithm': algorithm,
            'salt': salt[:6] + '...',
            'hash': hash_value[:6] + '...',
        }
    
    def harden_runtime(self, password, encoded):
        """
        No additional hardening needed for HMAC
        """
        pass
    
    def must_update(self, encoded):
        """
        Check if password needs to be updated
        """
        return False