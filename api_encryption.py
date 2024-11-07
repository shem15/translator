
# encrypt_api_key.py
from cryptography.fernet import Fernet
import json

# Generate an encryption key
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Save the key in a local file within the project directory
with open('secret.key', 'wb') as key_file:
    key_file.write(key)

# Load the API key from an external JSON file
with open('gg_t_temp.json') as f:
    api_data = json.load(f)
    api_key = api_data['key']

# Encrypt and save the API key
encrypted_data = cipher_suite.encrypt(api_key.encode())
with open('encrypted_api_key.json', 'wb') as f:
    f.write(encrypted_data)
