import requests
from config import COOKIE_URL
from maythusharmusic.utils.errors import capture_internal_err
from maythusharmusic.logging import LOGGER

COOKIE_PATH = "assets/cookies.txt"


def resolve_raw_cookie_url(url: str) -> str:
    """
    Return the raw content URL from Batbin or Pastebin.
    Supports:
    - https://batbin.me/abc123
    - https://pastebin.com/abc123
    """
    url = url.strip()
    low_url = url.lower()
    if "pastebin.com/" in low_url and "/raw/" not in low_url:
        paste_id = url.split("/")[-1]
        return f"https://pastebin.com/raw/{paste_id}"
    if "batbin.me/" in low_url and "/raw/" not in low_url:
        paste_id = url.split("/")[-1]
        return f"https://batbin.me/raw/{paste_id}"
    return url


@capture_internal_err
async def fetch_and_store_cookies():
    """
    Fetch cookies from Batbin or Pastebin, clean-write to cookies.txt.
    """
    if not COOKIE_URL:
        raise EnvironmentError("⚠️ ᴄᴏᴏᴋɪᴇ_ᴜʀʟ ɴᴏᴛ sᴇᴛ ɪɴ ᴇɴᴠ.")

    raw_url = resolve_raw_cookie_url(COOKIE_URL)

    try:
        response = requests.get(raw_url)
        response.raise_for_status()
    except Exception as e:
        raise ConnectionError(f"⚠️ ᴄᴀɴ'ᴛ ꜰᴇᴛᴄʜ ᴄᴏᴏᴋɪᴇs:\n{e}")

    cookies = response.text.strip()
    if not cookies.startswith("# Netscape"):
        raise ValueError("⚠️ ɪɴᴠᴀʟɪᴅ ᴄᴏᴏᴋɪᴇ ꜰᴏʀᴍᴀᴛ. ɴᴇᴇᴅs ɴᴇᴛsᴄᴀᴘᴇ ꜰᴏʀᴍᴀᴛ.")

    if len(cookies) < 100:
        raise ValueError("⚠️ ᴄᴏᴏᴋɪᴇ ᴄᴏɴᴛᴇɴᴛ ᴛᴏᴏ sʜᴏʀᴛ. ᴘᴏssɪʙʟʏ ɪɴᴠᴀʟɪᴅ.")

    try:
        with open(COOKIE_PATH, "w", encoding="utf-8") as f:
            f.write(cookies)
    except Exception as e:
        raise IOError(f"⚠️ ғᴀɪʟᴇᴅ ᴛᴏ sᴀᴠᴇ ᴄᴏᴏᴋɪᴇs: {e}")
