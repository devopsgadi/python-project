import jwt
import time

# Define your Apple Developer credentials
key_id = 'your_key_id'  # From the Apple Developer Portal
issuer_id = 'your_issuer_id'  # From the Apple Developer Portal
private_key_path = 'path_to_your_p8_file.p8'  # Path to your .p8 file

# Load your private key (.p8 file)
with open(private_key_path, 'r') as f:
    private_key = f.read()

# Define JWT payload and header
header = {
    'kid': key_id,  # Key ID from your Apple Developer account
    'typ': 'JWT'
}

payload = {
    'iss': issuer_id,  # Issuer ID from your Apple Developer account
    'iat': int(time.time()),  # Issued at time (current time)
    'exp': int(time.time()) + 1200,  # Expiry time (optional, 20 minutes here)
    'aud': 'appstoreconnect-v1'  # Audience is always appstoreconnect-v1 for App Store Connect API
}

# Generate JWT token
jwt_token = jwt.encode(payload, private_key, algorithm='ES256', headers=header)

# Print the JWT token
print(jwt_token)
