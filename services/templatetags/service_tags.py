# services/templatetags/service_tags.py

from django import template
import re

register = template.Library()

@register.filter
def youtube_embed_url(url):
    """
    Convierte una URL de YouTube en una URL de embed.
    
    Ejemplos:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ -> https://www.youtube.com/embed/dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ -> https://www.youtube.com/embed/dQw4w9WgXcQ
    """
    # Patrón para URLs de YouTube normales
    pattern1 = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)'
    # Patrón para URLs acortadas de YouTube
    pattern2 = r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)'
    
    match = re.match(pattern1, url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
        
    match = re.match(pattern2, url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
        
    return url  # Si no coincide con ningún patrón, devuelve la URL original