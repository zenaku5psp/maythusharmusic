import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from maythusharmusic import YouTube, app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_maintenance,
)
from maythusharmusic.utils.inline import botplaylist_markup
from config import PLAYLIST_IMG_URL, SUPPORT_CHAT, adminlist
from strings import get_string

links = {}
clinks = {}

def ensure_video_flag(message):
    if message.command[0].startswith("v") or "-v" in message.text:
        return True
    return None

def ensure_fplay_flag(message, chat_id, _, is_cplay):
    if message.command[0][-1] == "e":
        if not asyncio.run(is_active_chat(chat_id)):
            key = "play_16" if is_cplay else "play_18"
            return False, _[key]
        return True, None
    return None, None

async def ensure_assistant_joined(client, message, chat_id, userbot, _, i_mention, is_cplay):
    try:
        get = await client.get_chat_member(chat_id, userbot.id if not is_cplay else userbot.username)
    except ChatAdminRequired:
        return False, await message.reply_text(_["call_1"])
    except UserNotParticipant:
        invitelink = clinks.get(chat_id) if is_cplay else links.get(chat_id)
        if not invitelink:
            if message.chat.username:
                invitelink = message.chat.username
                try:
                    await userbot.resolve_peer(invitelink)
                except:
                    pass
            else:
                try:
                    invitelink = await client.export_chat_invite_link(chat_id)
                except ChatAdminRequired:
                    return False, await message.reply_text(_["call_1"])
                except Exception as e:
                    return False, await message.reply_text(
                        _["call_3"].format(i_mention, type(e).__name__)
                    )
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
        myu = await message.reply_text(_["call_4"].format(i_mention))
        try:
            await asyncio.sleep(1)
            await userbot.join_chat(invitelink)
        except InviteRequestSent:
            try:
                await client.approve_chat_join_request(chat_id, userbot.id)
            except Exception as e:
                return False, await message.reply_text(
                    _["call_3"].format(i_mention, type(e).__name__)
                )
            await asyncio.sleep(3)
            await myu.edit(_["call_5"].format(i_mention))
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return False, await message.reply_text(
                _["call_3"].format(i_mention, type(e).__name__)
            )

        (clinks if is_cplay else links)[chat_id] = invitelink

    return True, None

def PlayWrapper(command, is_cplay=False):
    async def wrapper(client, message):
        i = await client.get_me()
        language = await get_lang(message.chat.id)
        _ = get_string(language)

        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ʜᴏᴡ ᴛᴏ ғɪx ?", callback_data="AnonymousAdmin")]]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        if await is_maintenance():
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=f"{i.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ <a href={SUPPORT_CHAT}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a>.",
                    disable_web_page_preview=True,
                )

        try:
            await message.delete()
        except:
            pass

        audio = message.reply_to_message.audio if message.reply_to_message else None
        voice = message.reply_to_message.voice if message.reply_to_message else None
        video = message.reply_to_message.video if message.reply_to_message else None
        document = message.reply_to_message.document if message.reply_to_message else None
        url = await YouTube.url(message)

        if not any([audio, voice, video, document, url]):
            if len(message.command) < 2:
                if "stream" in message.command:
                    return await message.reply_text(_["str_1"])
                buttons = botplaylist_markup(_)
                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["playlist_1"] if not is_cplay else _["play_18"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        chat_id = message.chat.id
        channel = None
        if message.command[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)
            if not chat_id:
                return await message.reply_text(_["setting_12"] if not is_cplay else _["setting_7"])
            try:
                chat = await client.get_chat(chat_id)
                channel = chat.title
            except:
                return await message.reply_text(_["cplay_4"])

        playmode = await get_playmode(message.chat.id)
        playtype = await get_playtype(message.chat.id)
        if playtype != "Everyone" and message.from_user.id not in SUDOERS:
            admins = adminlist.get(message.chat.id)
            if not admins or message.from_user.id not in admins:
                return await message.reply_text(_["admin_18"] if not is_cplay else _["admin_13"])

        video_flag = ensure_video_flag(message)
        fplay, error_msg = ensure_fplay_flag(message, chat_id, _, is_cplay)
        if error_msg:
            return await message.reply_text(error_msg)

        if not await is_active_chat(chat_id):
            userbot = await get_assistant(chat_id)
            success, error = await ensure_assistant_joined(client, message, chat_id, userbot, _, i.mention, is_cplay)
            if not success:
                return error

        return await command(
            client,
            message,
            _,
            chat_id,
            video_flag,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper
