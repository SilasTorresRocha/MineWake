import os
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import pkcs12

CA_CERT_FILE = "ca/ca.crt"
CA_KEY_FILE = "ca/ca.key"

def _generate_rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

def init_ca(ca_name: str):
    os.makedirs("ca", exist_ok=True)
    if os.path.exists(CA_CERT_FILE) and os.path.exists(CA_KEY_FILE):
        return

    # Generate Private Key
    private_key = _generate_rsa_key()
    
    # Generate CA Certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"{ca_name} Root CA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, ca_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256())

    # Save Private Key
    with open(CA_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Save Certificate
    with open(CA_CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def generate_client_cert(client_name: str, password: str) -> bytes:
    # Load CA
    with open(CA_KEY_FILE, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(CA_CERT_FILE, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
        
    # Generate Client Key
    client_key = _generate_rsa_key()
    
    # Generate Client Certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, client_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        client_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650) # 10 years
    ).add_extension(
        x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
        critical=True
    ).sign(ca_key, hashes.SHA256())

    # Package as PKCS12
    p12_data = pkcs12.serialize_key_and_certificates(
        name=client_name.encode('utf-8'),
        key=client_key,
        cert=cert,
        cas=[ca_cert],
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )
    
    return p12_data
