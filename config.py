"""Basic server configuration options for the Gmail Image Extractor app"""

# Main port that Tornado should listen over for serving web pages
port = 8888

# A salt for creating secure cookies.  Should be unique per deployment
cookie_secret = "SOMETHING RANDOM"

# Google provided OAuth2 credentials for completing oauth flow for IMAP access
oauth2_client_id = "clientid"
oauth2_client_secret = "clientsecret"

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
