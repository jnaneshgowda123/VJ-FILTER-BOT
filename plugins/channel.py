# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging
import re
import asyncio
from datetime import datetime
from collections import defaultdict
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import save_file, unpack_new_file_id
from database.users_chats_db import db
from info import *
from utils import get_seconds, temp, get_size
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from Script import script
from pymongo.errors import PyMongoError, DuplicateKeyError
from pyrogram.errors import MessageIdInvalid, MessageNotModified, FloodWait
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

media_filter = filters.document | filters.video

# Try to import movie details functions, fallback if not available
try:
    from plugins.Dreamxfutures.Imdbposter import get_movie_detailsx, fetch_image, get_movie_details
    MOVIE_DETAILS_AVAILABLE = True
except ImportError:
    MOVIE_DETAILS_AVAILABLE = False
    logger.warning("Movie details functions not available, basic movie updates will be used")

# Constants for better organization
IGNORE_WORDS = {
    "rarbg", "dub", "sub", "sample", "mkv", "aac", "combined",
    "action", "adventure", "animation", "biography", "comedy", "crime",
    "documentary", "drama", "family", "fantasy", "film-noir", "history",
    "horror", "music", "musical", "mystery", "romance", "sci-fi", "sport",
    "thriller", "war", "western", "hdcam", "hdtc", "camrip", "ts", "tc",
    "telesync", "dvdscr", "dvdrip", "predvd", "webrip", "web-dl", "tvrip",
    "hdtv", "web dl", "webdl", "bluray", "brrip", "bdrip", "360p", "480p",
    "720p", "1080p", "2160p", "4k", "1440p", "540p", "240p", "140p", "hevc",
    "hdrip", "hin", "hindi", "tam", "tamil", "kan", "kannada", "tel", "telugu",
    "mal", "malayalam", "eng", "english", "pun", "punjabi", "ben", "bengali"
}

CAPTION_LANGUAGES = {
    "hin": "Hindi", "hindi": "Hindi",
    "tam": "Tamil", "tamil": "Tamil",
    "kan": "Kannada", "kannada": "Kannada",
    "tel": "Telugu", "telugu": "Telugu",
    "mal": "Malayalam", "malayalam": "Malayalam",
    "eng": "English", "english": "English",
    "pun": "Punjabi", "punjabi": "Punjabi",
    "ben": "Bengali", "bengali": "Bengali"
}

# Precompiled regex patterns
CLEAN_PATTERN = re.compile(r'@[^ \n\r\t\.,:;!?()\[\]{}<>\\/"\'=_%]+|\bwww\.[^\s\]\)]+|\([\@^]+\)|\[[\@^]+\]')
NORMALIZE_PATTERN = re.compile(r"[._]+|[()\[\]{}:;'–!,.?_]")
QUALITY_PATTERN = re.compile(
    r"\b(?:HDCam|HDTC|CamRip|TS|TC|TeleSync|DVDScr|DVDRip|PreDVD|"
    r"WEBRip|WEB-DL|TVRip|HDTV|WEB DL|WebDl|BluRay|BRRip|BDRip|"
    r"360p|480p|720p|1080p|2160p|4K|1440p|540p|240p|140p|HEVC|HDRip)\b",
    re.IGNORECASE
)

locks = defaultdict(asyncio.Lock)
pending_updates = {}

def clean_mentions_links(text: str) -> str:
    return CLEAN_PATTERN.sub("", text or "").strip()

def normalize(s: str) -> str:
    s = NORMALIZE_PATTERN.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()

def extract_movie_name(filename: str) -> str:
    """Extract clean movie name from filename"""
    # Remove file extensions
    name = filename
    for ext in ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
            break

    # Clean mentions and links
    name = clean_mentions_links(name)

    # Remove quality indicators and other patterns
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
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # Normalize and clean
    name = normalize(name)

    # Remove ignored words
    words = [word for word in name.split() if word.lower() not in IGNORE_WORDS]

    return " ".join(words).strip()

async def process_and_send_movie_update(bot, filename, caption, file_size):
    """Process and send enhanced movie update to update channel"""
    if not MOVIE_UPDATE_CHANNEL:
        return

    try:
        # Extract clean movie name
        movie_name = extract_movie_name(filename)
        if not movie_name:
            return

        # Check if movie update is enabled for this bot
        if hasattr(db, 'movie_update_status'):
            if not await db.movie_update_status(bot.me.id):
                return

        # Get or create movie collection
        if not hasattr(db, 'movie_updates'):
            db.movie_updates = db.db.movie_updates

        # Check if this movie already exists
        movie_doc = await db.movie_updates.find_one({"_id": movie_name})

        # Extract additional info
        caption_clean = caption.lower() if caption else ""
        quality = QUALITY_PATTERN.findall(f"{filename} {caption_clean}")
        quality_str = ", ".join(quality) if quality else "N/A"

        # Extract language
        lang_keys = {k for k in CAPTION_LANGUAGES if k in caption_clean or k in filename.lower()}
        language = ", ".join(sorted({CAPTION_LANGUAGES[k] for k in lang_keys})) if lang_keys else "N/A"

        file_data = {
            "filename": filename,
            "quality": quality_str,
            "language": language,
            "size": get_size(file_size),
            "timestamp": datetime.now()
        }

        if not movie_doc:
            # New movie - get details if available
            details = {}
            if MOVIE_DETAILS_AVAILABLE:
                try:
                    if hasattr(locals(), 'TMDB_POSTER') and TMDB_POSTER:
                        details = await get_movie_detailsx(movie_name) or {}
                        if details.get("error"):
                            details = await get_movie_details(movie_name) or {}
                    else:
                        details = await get_movie_details(movie_name) or {}
                except Exception as e:
                    logger.error(f"Error getting movie details: {e}")
                    details = {}

            # Create new movie document
            movie_doc = {
                "_id": movie_name,
                "files": [file_data],
                "poster_url": details.get("poster_url"),
                "backdrop_url": details.get("backdrop_url"),
                "genres": details.get("genres", "N/A"),
                "rating": details.get("rating", "N/A"),
                "year": details.get("year", "N/A"),
                "message_id": None,
                "is_photo": False
            }

            try:
                await db.movie_updates.insert_one(movie_doc)
                await send_movie_update(bot, movie_name)
            except DuplicateKeyError:
                # Handle race condition
                await db.movie_updates.update_one(
                    {"_id": movie_name},
                    {"$push": {"files": file_data}}
                )
        else:
            # Update existing movie
            if any(f["filename"] == filename for f in movie_doc["files"]):
                return  # File already exists

            await db.movie_updates.update_one(
                {"_id": movie_name},
                {"$push": {"files": file_data}}
            )
            # Schedule update after delay to batch multiple files
            schedule_update(bot, movie_name)

    except Exception as e:
        logger.error(f"Error processing movie update: {e}")

def schedule_update(bot, movie_name, delay=10):
    """Schedule delayed update to batch multiple files"""
    if handle := pending_updates.get(movie_name):
        if not handle.cancelled():
            handle.cancel()

    loop = asyncio.get_event_loop()
    pending_updates[movie_name] = loop.call_later(
        delay,
        lambda: asyncio.create_task(update_movie_message(bot, movie_name))
    )

async def send_movie_update(bot, movie_name):
    """Send new movie update message"""
    try:
        movie_doc = await db.movie_updates.find_one({"_id": movie_name})
        if not movie_doc:
            return

        text = generate_movie_message(movie_doc, movie_name)

        # Create button
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                '🔍 Get Files',
                url=f"https://t.me/{temp.U_NAME}?start=search-{movie_name.replace(' ', '+')}"
            )
        ]])

        # Determine sending method based on configuration
        poster_url = None
        if hasattr(locals(), 'LANDSCAPE_POSTER') and LANDSCAPE_POSTER and movie_doc.get("backdrop_url"):
            poster_url = movie_doc["backdrop_url"]
        elif movie_doc.get("poster_url"):
            poster_url = movie_doc["poster_url"]

        # Send message
        if poster_url and not (hasattr(locals(), 'LINK_PREVIEW') and LINK_PREVIEW):
            # Send as photo
            try:
                if MOVIE_DETAILS_AVAILABLE:
                    resized_poster = await fetch_image(poster_url)
                    msg = await bot.send_photo(
                        chat_id=MOVIE_UPDATE_CHANNEL,
                        photo=resized_poster,
                        caption=text,
                        reply_markup=buttons,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    msg = await bot.send_photo(
                        chat_id=MOVIE_UPDATE_CHANNEL,
                        photo=poster_url,
                        caption=text,
                        reply_markup=buttons,
                        parse_mode=enums.ParseMode.HTML
                    )
                is_photo = True
            except Exception as e:
                logger.error(f"Failed to send photo, falling back to text: {e}")
                # Fallback to text message
                msg = await bot.send_message(
                    chat_id=MOVIE_UPDATE_CHANNEL,
                    text=text,
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=not (hasattr(locals(), 'LINK_PREVIEW') and LINK_PREVIEW)
                )
                is_photo = False
        else:
            # Send as text message
            send_params = {
                "chat_id": MOVIE_UPDATE_CHANNEL,
                "text": text,
                "reply_markup": buttons,
                "parse_mode": enums.ParseMode.HTML
            }

            if hasattr(locals(), 'LINK_PREVIEW') and LINK_PREVIEW:
                if hasattr(locals(), 'ABOVE_PREVIEW') and ABOVE_PREVIEW:
                    send_params["invert_media"] = True
            else:
                send_params["disable_web_page_preview"] = True

            msg = await bot.send_message(**send_params)
            is_photo = False

        # Update document with message info
        await db.movie_updates.update_one(
            {"_id": movie_name},
            {"$set": {"message_id": msg.id, "is_photo": is_photo}}
        )

        return msg

    except Exception as e:
        logger.error(f"Failed to send movie update: {e}")
        return None

async def update_movie_message(bot, movie_name):
    """Update existing movie message with new files"""
    try:
        movie_doc = await db.movie_updates.find_one({"_id": movie_name})
        if not movie_doc:
            return

        text = generate_movie_message(movie_doc, movie_name)

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                '🔍 Get Files',
                url=f"https://t.me/{temp.U_NAME}?start=search-{movie_name.replace(' ', '+')}"
            )
        ]])

        message_id = movie_doc.get("message_id")
        is_photo = movie_doc.get("is_photo", False)

        if not message_id:
            await send_movie_update(bot, movie_name)
            return

        try:
            if is_photo:
                await bot.edit_message_caption(
                    chat_id=MOVIE_UPDATE_CHANNEL,
                    message_id=message_id,
                    caption=text,
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                edit_params = {
                    "chat_id": MOVIE_UPDATE_CHANNEL,
                    "message_id": message_id,
                    "text": text,
                    "reply_markup": buttons,
                    "parse_mode": enums.ParseMode.HTML
                }

                if hasattr(locals(), 'LINK_PREVIEW') and LINK_PREVIEW:
                    if hasattr(locals(), 'ABOVE_PREVIEW') and ABOVE_PREVIEW:
                        edit_params["invert_media"] = True
                else:
                    edit_params["disable_web_page_preview"] = True

                await bot.edit_message_text(**edit_params)

        except (MessageIdInvalid, MessageNotModified):
            # Message was deleted or no changes needed
            pass
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Try to delete old message and send new one
            try:
                await bot.delete_messages(MOVIE_UPDATE_CHANNEL, message_id)
            except:
                pass
            await send_movie_update(bot, movie_name)

    except Exception as e:
        logger.error(f"Failed to update movie message: {e}")

def generate_movie_message(movie_doc, movie_name):
    """Generate movie update message text"""
    files = movie_doc.get("files", [])

    # Aggregate information from all files
    all_qualities = set()
    all_languages = set()
    total_files = len(files)

    for file_data in files:
        if file_data["quality"] != "N/A":
            all_qualities.update(q.strip() for q in file_data["quality"].split(","))
        if file_data["language"] != "N/A":
            all_languages.update(l.strip() for l in file_data["language"].split(","))

    quality_str = ", ".join(sorted(all_qualities)) if all_qualities else "N/A"
    language_str = ", ".join(sorted(all_languages)) if all_languages else "N/A"

    # Build message
    message_parts = [
        f"🎬 <b>{movie_name}</b>",
        ""
    ]

    if movie_doc.get("genres") and movie_doc["genres"] != "N/A":
        message_parts.append(f"🎭 <b>Genre:</b> {movie_doc['genres']}")

    if movie_doc.get("year") and movie_doc["year"] != "N/A":
        message_parts.append(f"📅 <b>Year:</b> {movie_doc['year']}")

    if movie_doc.get("rating") and movie_doc["rating"] != "N/A":
        message_parts.append(f"⭐ <b>Rating:</b> {movie_doc['rating']}/10")

    message_parts.extend([
        f"🎥 <b>Quality:</b> {quality_str}",
        f"🗣️ <b>Language:</b> {language_str}",
        f"📁 <b>Total Files:</b> {total_files}",
        "",
        f"🔍 <b>Search:</b> <code>{movie_name}</code>"
    ])

    return "\n".join(message_parts)

@Client.on_message(filters.chat(CHANNELS) & (filters.document | filters.video | filters.audio))
async def media_handler(bot, message):
    """Handle media files from configured channels"""
    try:
        # Get media object
        media = None
        file_type = None

        if message.document:
            media = message.document
            file_type = "document"
        elif message.video:
            media = message.video
            file_type = "video"
        elif message.audio:
            media = message.audio
            file_type = "audio"

        if not media:
            return

        # Set media properties
        media.file_type = file_type
        media.caption = message.caption or ""

        # Get file details
        file_name, file_id, file_ref = unpack_new_file_id(media.file_id)

        # Save file to database
        result = await save_file(media)

        # Process movie update if it's a video file
        if media.file_name and MOVIE_UPDATE_CHANNEL:
            video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
            if any(media.file_name.lower().endswith(ext) for ext in video_extensions):
                await process_and_send_movie_update(
                    bot,
                    media.file_name,
                    media.caption or "",
                    media.file_size
                )

        # Send confirmation message
        if result:
            file_type_name = "Video" if file_type == "video" else "File"
            await message.reply_text(
                f"**{file_type_name} Saved Successfully ✅**\n\n**File Name:** {file_name}",
                quote=True
            )
        else:
            file_type_name = "Video" if file_type == "video" else "File"
            await message.reply_text(
                f"**{file_type_name} Already Exists ⚠️**",
                quote=True
            )

    except Exception as e:
        logger.error(f"Error in media handler: {e}")
        # Still save the file even if movie update fails
        try:
            await save_file(media)
        except Exception as save_error:
            logger.error(f"Failed to save file: {save_error}")
        pass

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def private_media_handler(bot, message):
    """Handle media files sent privately to bot"""
    try:
        # Get media object
        media = None
        file_type = None

        if message.document:
            media = message.document
            file_type = "document"
        elif message.video:
            media = message.video
            file_type = "video"
        elif message.audio:
            media = message.audio
            file_type = "audio"

        if not media:
            return

        # Set media properties
        media.file_type = file_type
        media.caption = message.caption or ""

        # Get file details
        file_name, file_id, file_ref = unpack_new_file_id(media.file_id)

        # Save file to database
        result = await save_file(media)

        # Send confirmation message
        if result:
            file_type_name = "Video" if file_type == "video" else "File"
            await message.reply_text(
                f"**{file_type_name} Saved Successfully ✅**\n\n**File Name:** {file_name}",
                quote=True
            )
        else:
            file_type_name = "Video" if file_type == "video" else "File"
            await message.reply_text(
                f"**{file_type_name} Already Exists ⚠️**",
                quote=True
            )

    except Exception as e:
        logger.error(f"Error in private media handler: {e}")
        await message.reply_text(
            "**Something went wrong. Please check logs.**",
            quote=True
        )