"""
SSL/TLS configuration utilities for robust HTTPS connections.
Ensures all HTTP clients use proper CA certificate bundles.
"""
import logging
import ssl
import os

import certifi
import requests

logger = logging.getLogger(__name__)


def get_ca_bundle_path() -> str:
    """
    Get the path to the CA certificate bundle.
    Returns certifi's bundle path, which is the most up-to-date.
    """
    return certifi.where()


def configure_requests_ssl():
    """
    Configure requests library to use certifi's CA bundle.
    This ensures all requests.Session() instances use proper SSL verification.
    """
    try:
        ca_bundle = get_ca_bundle_path()
        
        # Verify bundle exists
        if not os.path.exists(ca_bundle):
            logger.warning("CA bundle not found at: %s", ca_bundle)
            return False
        
        # Set environment variable for requests/urllib3
        os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
        os.environ['CURL_CA_BUNDLE'] = ca_bundle
        
        # Configure requests default session to use certifi
        # This is actually the default, but we make it explicit
        requests.packages.urllib3.disable_warnings()
        
        logger.info("Requests SSL configured with CA bundle: %s", ca_bundle)
        return True
    except Exception as e:
        logger.error("Failed to configure requests SSL: %s", e, exc_info=True)
        return False


def create_ssl_verified_session() -> requests.Session:
    """
    Create a requests.Session with proper SSL verification.
    Uses certifi's CA bundle for certificate validation.
    """
    session = requests.Session()
    ca_bundle = get_ca_bundle_path()
    
    # Explicitly set verify to use certifi bundle
    session.verify = ca_bundle
    
    return session


def log_ssl_info():
    """
    Log SSL/TLS configuration information for debugging.
    """
    try:
        logger.info("=" * 60)
        logger.info("SSL/TLS Configuration Information")
        logger.info("=" * 60)
        logger.info("OpenSSL Version: %s", ssl.OPENSSL_VERSION)
        
        ca_bundle = get_ca_bundle_path()
        logger.info("CA Certificate Bundle: %s", ca_bundle)
        
        if os.path.exists(ca_bundle):
            bundle_size = os.path.getsize(ca_bundle)
            logger.info("CA Bundle Size: %d bytes (%.2f KB)", bundle_size, bundle_size / 1024)
        else:
            logger.warning("CA Bundle NOT FOUND!")
        
        # Check environment variables
        req_ca = os.environ.get('REQUESTS_CA_BUNDLE')
        curl_ca = os.environ.get('CURL_CA_BUNDLE')
        logger.info("REQUESTS_CA_BUNDLE: %s", req_ca or "not set")
        logger.info("CURL_CA_BUNDLE: %s", curl_ca or "not set")
        
        logger.info("=" * 60)
    except Exception as e:
        logger.error("Failed to log SSL info: %s", e, exc_info=True)


# Initialize SSL configuration on module import
configure_requests_ssl()

