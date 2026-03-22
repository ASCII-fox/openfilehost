# Contains functions for getting SSL certificates 

from pathlib import Path


# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SSL_DIR = PROJECT_ROOT / "ssl"
CERT_DIR = SSL_DIR / "certs"


def get_ssl_context(ip_address=None):
    """Get SSL certificate paths"""
    if not ip_address:
        print("No IP address provided for certificate lookup")
        return None, None
    
    cert_name = ip_address.replace(':', '_')
    cert_path = CERT_DIR / cert_name
    cert_file = cert_path / "fullchain.pem"
    key_file = cert_path / "privkey.pem"
    
    if cert_file.exists() and key_file.exists():
        print(f"Using certificate from {cert_file}")
        return cert_file, key_file
    
    print("No certificate found.")
    return None, None
