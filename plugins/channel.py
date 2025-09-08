# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db
from database.join_reqs import JoinReqs
from info import *
from utils import get_seconds, temp, get_size
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size

media_filter = filters.document | filters.video

# Auto Movie Update Channel Feature
async def send_movie_update(client, message, file_name):
    """Send movie update to update channel"""
    if not MOVIE_UPDATE_CHANNEL:
        return

    try:
        # Extract movie name from filename (remove quality, year, etc.)
        movie_name = file_name
        # Remove common video file extensions
        for ext in ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
            if movie_name.lower().endswith(ext):
                movie_name = movie_name[:-len(ext)]
                break

        # Remove quality indicators and other common suffixes
        remove_patterns = [
            r'\b(720p|1080p|480p|360p|2160p|4k|hd|sd|cam|dvdrip|brrip|webrip|hdtv|web-dl|bluray)\b',
            r'\b(x264|x265|hevc|h264|h265)\b',
            r'\b(aac|ac3|dts|mp3)\b',
            r'\[.*?\]',
            r'\(.*?\)',
            r'www\.\w+\.\w+',
            r'@\w+',
        ]

        for pattern in remove_patterns:
            movie_name = re.sub(pattern, '', movie_name, flags=re.IGNORECASE)

        # Clean up extra spaces and dots
        movie_name = re.sub(r'[._-]+', ' ', movie_name).strip()
        movie_name = re.sub(r'\s+', ' ', movie_name)

        # Create update message
        update_text = f"🎬 <b>New Movie Added!</b>\n\n🎭 <b>Title:</b> {movie_name}\n\n💾 <b>Size:</b> {get_size(message.document.file_size)}\n\n🔍 <b>Search to get this movie!</b>"

        # Send to update channel
        await client.send_message(
            chat_id=MOVIE_UPDATE_CHANNEL,
            text=update_text,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error sending movie update: {e}")

@Client.on_message(filters.channel & filters.incoming & filters.document, group=media)
async def media(bot, message):
    try:
        file_type = message.media
        media = getattr(message, file_type.value, None)
        if not media:
            logger.error("Media not found in message")
            return

        media.file_type = file_type.value
        media.caption = message.caption
        file_name, file_id, file_ref = unpack_new_file_id(media.file_id)

        # Send movie update if it's a video file
        if file_type.value == "document" and media.file_name:
            video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
            if any(media.file_name.lower().endswith(ext) for ext in video_extensions):
                await send_movie_update(bot, message, media.file_name)

        result = await save_file(media)
        if result:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    f"**Video Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
        else:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    "Video Already Exist.",
                    quote=True
                )
            else:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
    except Exception as e:
        logger.error(e)
        await message.reply_text(
            f"Something went wrong, Please check logs.",
            quote=True
        )

@Client.on_message(filters.channel & filters.incoming & filters.video, group=media)
async def video(bot, message):
    try:
        file_type = message.media
        media = getattr(message, file_type.value, None)
        if not media:
            logger.error("Media not found in message")
            return

        media.file_type = file_type.value
        media.caption = message.caption
        file_name, file_id, file_ref = unpack_new_file_id(media.file_id)

        # Send movie update if it's a video file
        if file_type.value == "video" and media.file_name:
            video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
            if any(media.file_name.lower().endswith(ext) for ext in video_extensions):
                await send_movie_update(bot, message, media.file_name)

        result = await save_file(media)
        if result:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    f"**Video Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
        else:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    "Video Already Exist.",
                    quote=True
                )
            else:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
    except Exception as e:
        logger.error(e)
        await message.reply_text(
            f"Something went wrong, Please check logs.",
            quote=True
        )

@Client.on_message(filters.private & filters.incoming & (filters.document | filters.video), group=media)
async def private_media(bot, message):
    try:
        file_type = message.media
        media = getattr(message, file_type.value, None)
        if not media:
            logger.error("Media not found in message")
            return

        media.file_type = file_type.value
        media.caption = message.caption
        file_name, file_id, file_ref = unpack_new_file_id(media.file_id)

        result = await save_file(media)
        if result:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    f"**Video Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"**File Saved Successfully**\n\n**File Name:** {file_name}\n",
                    quote=True
                )
        else:
            if file_type == enums.MessageMediaType.DOCUMENT:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
            elif file_type == enums.MessageMediaType.VIDEO:
                await message.reply_text(
                    "Video Already Exist.",
                    quote=True
                )
            else:
                await message.reply_text(
                    "File Already Exist.",
                    quote=True
                )
    except Exception as e:
        logger.error(e)
        await message.reply_text(
            f"Something went wrong, Please check logs.",
            quote=True
        )