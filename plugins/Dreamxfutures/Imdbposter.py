
import aiohttp
import asyncio
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

async def get_movie_details(movie_name):
    """Get movie details from IMDB"""
    try:
        # This is a placeholder implementation
        # You can implement actual IMDB API calls here
        return {
            "poster_url": None,
            "backdrop_url": None,
            "genres": "N/A",
            "rating": "N/A",
            "year": "N/A",
            "url": ""
        }
    except Exception as e:
        logger.error(f"Error getting IMDB details: {e}")
        return {}

async def get_movie_detailsx(movie_name):
    """Get movie details from TMDB"""
    try:
        # This is a placeholder implementation
        # You can implement actual TMDB API calls here
        return {
            "poster_url": None,
            "backdrop_url": None,
            "genres": "N/A",
            "rating": "N/A",
            "year": "N/A",
            "tmdb_url": "",
            "error": False
        }
    except Exception as e:
        logger.error(f"Error getting TMDB details: {e}")
        return {"error": True}

async def fetch_image(url, size=(853, 1280)):
    """Fetch and resize image from URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    
                    # Resize image
                    image = image.resize(size, Image.Resampling.LANCZOS)
                    
                    # Convert to bytes
                    output = BytesIO()
                    image.save(output, format='JPEG', quality=85)
                    output.seek(0)
                    
                    return output.getvalue()
    except Exception as e:
        logger.error(f"Error fetching image: {e}")
        return None
