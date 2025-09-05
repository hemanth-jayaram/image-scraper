"""
Configuration file for Article Image Scraper Pipeline

Modify these settings to customize the behavior of the image scraper.
"""

# Image filtering settings
MIN_IMAGE_SIZE = (100, 100)  # Minimum width x height in pixels
MAX_FILE_SIZE_MB = 10  # Maximum file size in MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg'}

# Scoring thresholds
MIN_ACCEPTABLE_SCORE = 40  # Minimum score to accept an image
TRAFILATURA_THRESHOLD = 80  # Score threshold for trafilatura method
NEWSPAPER_THRESHOLD = 70   # Score threshold for newspaper3k method

# Network settings
REQUEST_TIMEOUT = 30  # Timeout for HTTP requests in seconds
RETRY_ATTEMPTS = 3    # Number of retry attempts for failed requests
REQUEST_DELAY = 0.5   # Delay between requests in seconds

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Image processing settings
JPG_QUALITY = 90  # JPEG quality (1-100)
OPTIMIZE_JPG = True  # Enable JPEG optimization

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'scraper.log'

# Output settings
OUTPUT_FOLDER = 'articles+images'
MAX_IMAGES_PER_ARTICLE = 1  # Always 1 for this pipeline

# Tracking pixel patterns to exclude
TRACKING_DOMAINS = [
    'facebook.com', 'google-analytics.com', 'googletagmanager.com',
    'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
    'outbrain.com', 'taboola.com', 'amazon-adsystem.com'
]

TRACKING_PATTERNS = [
    'facebook.com/tr', 'google-analytics.com', '/pixel?', '/track?',
    '/beacon?', '/analytics?', 'googletagmanager.com'
]

# Logo and branding patterns to exclude
LOGO_PATTERNS = [
    r'logo', r'icon', r'favicon', r'avatar', r'profile',
    r'advertisement', r'ad[_-]', r'banner', r'widget',
    r'social', r'share', r'button', r'arrow', r'play',
    r'thumbnail.*small', r'thumb.*\d+x\d+', r'\d+x\d+.*thumb',
    r'brand', r'header', r'masthead', r'watermark',
    r'signature', r'emblem', r'badge', r'seal', r'mark'
]
