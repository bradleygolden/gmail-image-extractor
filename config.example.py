"""Basic server configuration options for the Gmail Image Extractor app"""

# Name of the site
site_name = "Gmail Image Extractor"

# Site Description
site_description = "This is the site description"

# Main port that Tornado should listen over for serving web pages
port = 8888

# Base url where site is being hosted
base_url = "http://localhost"

# Full url where site is hosted
full_url = base_url + ":" + str(port)

# A salt for creating secure cookies.  Should be unique per deployment
cookie_secret = "SOMETHING RANDOM"

# Google login url for OAuth2
oauth2_login_url = "/auth/login"

# Google redirect URI
oauth2_redirect_url = "/oauth2callback"

# Google provided OAuth2 credentials for completing oauth flow for IMAP access
# oauth2_client_id = "YOUR CLIENT ID HERE"
oauth2_client_id = "client_id"
# oauth2_client_secret = "YOUR CLIENT SECRET HERE"
oauth2_client_secret = "client_secret"

# Enable cross-site request forgery protection
xsrf_cookies = True

# Set debug mode while using the Torndo server
# Using debug mode allows for autoreload mode as well as other useful features
debug = True

# The threshold, in seconds, when oauth tokens should be refreshed with google.
# If an oauth token is within this many seconds of expiring it will be refreshed
oauth2_expiration_threshold = 1200

# Google Analytics account ID.  If included, Google analytics will be
# included on each page view
google_analytics_account_id = None

# HMAC Key. Used to autheticate images that are being sent to and from the server.
hmac_key = 'RandomKey'

# Optional hardcoded oauth credentials.  Useful when doing stress testing
# with hardcoded responses, etc.  Set to None to use standard, oauth flow
# settings. (ie)
devel_oauth_credentials = dict(
    access_token="some token",
    expires_in=3599,
    email="some email",
)

zip_removal_countdown = 30*60  # 30 minutes
