from livekit.api import AccessToken, VideoGrants

# These are the default keys for a local LiveKit server
API_KEY = "devkey"
API_SECRET = "secret"

def generate_token():
    token = AccessToken(API_KEY, API_SECRET).with_identity("jarvis-user").with_name("JARVIS User").with_grants(
        VideoGrants(
            room_join=True,
            room="test-room",
            can_publish=True,
            can_publish_data=True,
        )
    ).to_jwt()
    print(token)

if __name__ == "__main__":
    generate_token()
