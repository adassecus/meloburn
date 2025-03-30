import os
import sys
import shutil
import threading
import ctypes
import subprocess
import re
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.font import Font
import json
from datetime import datetime
import traceback
import unicodedata
import time
from urllib.parse import quote_plus
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.aac import AAC

BG_COLOR = "#ffffff"
FG_COLOR = "#333333"
ACCENT_COLOR = "#4A6FFF"
ACCENT_HOVER = "#3558cc"
SECONDARY_BG = "#f8f8f8"
BORDER_COLOR = "#e0e0e0"
ERROR_COLOR = "#ff5252"
WARNING_COLOR = "#D84315"
SUCCESS_COLOR = "#4CAF50"

CACHE_FILE = os.path.join(os.path.expanduser("~"), ".meloburn_cache.json")
USER_AGENT = "Meloburn/0.7"
API_KEYS = {
    "lastfm": "d88ab9b09547dd20ace556b57261fd77",
    "discogs": "hZgXwVrDVJKsHazhyzMZ",
    "musicbrainz": "Meloburn/0.7 (https://github.com/adassecus/meloburn)"
}

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', '', text).lower().strip()
    return text

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"artists": {}, "tracks": {}, "albums": {}, "album_art": {}}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

api_cache = load_cache()

def get_lastfm_data(method, **params):
    base_url = "http://ws.audioscrobbler.com/2.0/"
    params.update({
        "method": method,
        "api_key": API_KEYS["lastfm"],
        "format": "json"
    })
    
    url = base_url + "?" + "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def get_musicbrainz_data(entity, query):
    base_url = f"https://musicbrainz.org/ws/2/{entity}"
    params = {
        "query": query,
        "fmt": "json"
    }
    
    try:
        response = requests.get(
            base_url,
            params=params,
            headers={"User-Agent": API_KEYS["musicbrainz"]},
            timeout=10
        )
        if response.status_code == 200:
            time.sleep(1)
            return response.json()
    except Exception:
        pass
    return None

def get_discogs_data(search_type, query):
    base_url = "https://api.discogs.com/database/search"
    params = {
        "type": search_type,
        "q": query,
        "token": API_KEYS["discogs"]
    }
    
    try:
        response = requests.get(
            base_url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def search_audio_db(query_type, query):
    if query_type == 'track':
        url = f"https://theaudiodb.com/api/v1/json/2/searchtrack.php?t={quote_plus(query)}"
    elif query_type == 'artist':
        url = f"https://theaudiodb.com/api/v1/json/2/searchtrack.php?s={quote_plus(query)}"
    else:
        return None
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

def get_album_art_url(artist, album):
    cache_key = f"{normalize_text(artist)}_{normalize_text(album)}"
    if cache_key in api_cache.get("album_art", {}):
        return api_cache["album_art"][cache_key]
    
    try:
        lastfm_data = get_lastfm_data("album.getinfo", artist=artist, album=album)
        if lastfm_data and "album" in lastfm_data and "image" in lastfm_data["album"]:
            for img in lastfm_data["album"]["image"]:
                if img["size"] == "extralarge" and img["#text"]:
                    api_cache.setdefault("album_art", {})[cache_key] = img["#text"]
                    save_cache(api_cache)
                    return img["#text"]
    except Exception:
        pass
    
    try:
        discogs_data = get_discogs_data("release", f"{artist} {album}")
        if discogs_data and "results" in discogs_data and len(discogs_data["results"]) > 0:
            for result in discogs_data["results"]:
                if "cover_image" in result and result["cover_image"]:
                    api_cache.setdefault("album_art", {})[cache_key] = result["cover_image"]
                    save_cache(api_cache)
                    return result["cover_image"]
    except Exception:
        pass
    
    return None

def download_album_art(url):
    if not url:
        return None
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    
    return None

def lookup_artist_by_track(track_title):
    if not track_title:
        return None
        
    normalized_title = normalize_text(track_title)
    if normalized_title in api_cache.get("tracks", {}):
        return api_cache["tracks"][normalized_title]
    
    artist = None
    
    try:
        audio_db_data = search_audio_db('track', track_title)
        if audio_db_data and audio_db_data.get("track") and len(audio_db_data["track"]) > 0:
            artist = audio_db_data["track"][0].get("strArtist")
    except Exception:
        pass
    
    if not artist:
        try:
            lastfm_data = get_lastfm_data("track.search", track=track_title)
            if lastfm_data and "results" in lastfm_data and "trackmatches" in lastfm_data["results"]:
                tracks = lastfm_data["results"]["trackmatches"].get("track", [])
                if tracks and len(tracks) > 0:
                    artist = tracks[0].get("artist")
        except Exception:
            pass
    
    if not artist:
        try:
            mb_data = get_musicbrainz_data("recording", f'recording:"{track_title}"')
            if mb_data and "recordings" in mb_data and len(mb_data["recordings"]) > 0:
                recording = mb_data["recordings"][0]
                if "artist-credit" in recording and len(recording["artist-credit"]) > 0:
                    artist = recording["artist-credit"][0].get("artist", {}).get("name")
        except Exception:
            pass
    
    if artist:
        api_cache.setdefault("tracks", {})[normalized_title] = artist
        save_cache(api_cache)
    
    return artist

def lookup_track_by_artist(artist):
    if not artist:
        return None
        
    normalized_artist = normalize_text(artist)
    if normalized_artist in api_cache.get("artists", {}):
        return api_cache["artists"][normalized_artist]
    
    track = None
    
    try:
        audio_db_data = search_audio_db('artist', artist)
        if audio_db_data and audio_db_data.get("track") and len(audio_db_data["track"]) > 0:
            track = audio_db_data["track"][0].get("strTrack")
    except Exception:
        pass
    
    if not track:
        try:
            lastfm_data = get_lastfm_data("artist.getTopTracks", artist=artist)
            if lastfm_data and "toptracks" in lastfm_data and "track" in lastfm_data["toptracks"]:
                tracks = lastfm_data["toptracks"]["track"]
                if tracks and len(tracks) > 0:
                    track = tracks[0].get("name")
        except Exception:
            pass
    
    if not track:
        try:
            mb_data = get_musicbrainz_data("artist", f'artist:"{artist}"')
            if mb_data and "artists" in mb_data and len(mb_data["artists"]) > 0:
                artist_id = mb_data["artists"][0].get("id")
                if artist_id:
                    work_data = get_musicbrainz_data("work", f'arid:{artist_id}')
                    if work_data and "works" in work_data and len(work_data["works"]) > 0:
                        track = work_data["works"][0].get("title")
        except Exception:
            pass
    
    if track:
        api_cache.setdefault("artists", {})[normalized_artist] = track
        save_cache(api_cache)
    
    return track

def lookup_album_by_track_artist(track, artist):
    if not track or not artist:
        return None
        
    cache_key = f"{normalize_text(artist)}_{normalize_text(track)}"
    if cache_key in api_cache.get("albums", {}):
        return api_cache["albums"][cache_key]
    
    album = None
    
    try:
        lastfm_data = get_lastfm_data("track.getInfo", track=track, artist=artist)
        if lastfm_data and "track" in lastfm_data and "album" in lastfm_data["track"]:
            album = lastfm_data["track"]["album"].get("title")
    except Exception:
        pass
    
    if not album:
        try:
            mb_data = get_musicbrainz_data("recording", f'recording:"{track}" AND artist:"{artist}"')
            if mb_data and "recordings" in mb_data and len(mb_data["recordings"]) > 0:
                for recording in mb_data["recordings"]:
                    if "releases" in recording and len(recording["releases"]) > 0:
                        album = recording["releases"][0].get("title")
                        break
        except Exception:
            pass
    
    if album:
        api_cache.setdefault("albums", {})[cache_key] = album
        save_cache(api_cache)
    
    return album

def enhance_metadata(artist, title, album=None):
    updated_artist = artist if artist and artist.lower() not in ["desconhecido", "unknown", "unknown artist", ""] else None
    updated_title = title if title and title.lower() not in ["desconhecido", "unknown", ""] else None
    updated_album = album if album and album.lower() not in ["desconhecido", "unknown", ""] else None
    
    if updated_title and not updated_artist:
        new_artist = lookup_artist_by_track(updated_title)
        if new_artist:
            updated_artist = new_artist
    
    if updated_artist and not updated_title:
        new_title = lookup_track_by_artist(updated_artist)
        if new_title:
            updated_title = new_title
    
    if updated_artist and updated_title and not updated_album:
        new_album = lookup_album_by_track_artist(updated_title, updated_artist)
        if new_album:
            updated_album = new_album
    
    return updated_artist or "Desconhecido", updated_title or "Desconhecido", updated_album or "Desconhecido"

def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return True

def sanitize_string(s):
    if not s:
        return "Desconhecido"
    
    replacements = {
        '&': 'e',
        '+': 'mais',
        '@': 'em',
        '<': '',
        '>': '',
        ':': '-',
        '"': "'",
        '/': '-',
        '\\': '-',
        '|': '-',
        '?': '',
        '*': '',
        '  ': ' '
    }
    
    result = s
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    
    while result.endswith('.') or result.endswith(' '):
        result = result[:-1]
    
    result = ''.join(ch for ch in result if ord(ch) >= 32)
    result = result.strip()[:100]
    
    return result if result else "Desconhecido"

def get_audio_metadata(file_path):
    metadata = {
        'artist': None,
        'album': None,
        'title': None,
        'track_number': None,
        'album_art': None,
        'year': None,
        'genre': None
    }
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.mp3':
            try:
                tags = EasyID3(file_path)
                metadata['artist'] = tags.get('artist', [''])[0]
                metadata['album'] = tags.get('album', [''])[0]
                metadata['title'] = tags.get('title', [''])[0]
                metadata['track_number'] = tags.get('tracknumber', [''])[0]
                metadata['year'] = tags.get('date', [''])[0]
                metadata['genre'] = tags.get('genre', [''])[0]
                
                try:
                    id3 = ID3(file_path)
                    for tag in id3.values():
                        if tag.FrameID == 'APIC':
                            metadata['album_art'] = tag.data
                            break
                except Exception:
                    pass
            except Exception:
                try:
                    EasyID3.create(file_path)
                    tags = EasyID3(file_path)
                except Exception:
                    pass
        
        elif file_ext == '.flac':
            try:
                audio = FLAC(file_path)
                metadata['artist'] = audio.get('artist', [''])[0] if 'artist' in audio else ''
                metadata['album'] = audio.get('album', [''])[0] if 'album' in audio else ''
                metadata['title'] = audio.get('title', [''])[0] if 'title' in audio else ''
                metadata['track_number'] = audio.get('tracknumber', [''])[0] if 'tracknumber' in audio else ''
                metadata['year'] = audio.get('date', [''])[0] if 'date' in audio else ''
                metadata['genre'] = audio.get('genre', [''])[0] if 'genre' in audio else ''
                
                if audio.pictures:
                    metadata['album_art'] = audio.pictures[0].data
            except Exception:
                pass
        
        elif file_ext in ['.m4a', '.aac']:
            try:
                audio = AAC(file_path)
                if hasattr(audio, 'tags') and audio.tags:
                    metadata['title'] = audio.tags.get('title', [''])[0] if 'title' in audio.tags else ''
                    metadata['artist'] = audio.tags.get('artist', [''])[0] if 'artist' in audio.tags else ''
                    metadata['album'] = audio.tags.get('album', [''])[0] if 'album' in audio.tags else ''
            except Exception:
                pass
        
        elif file_ext == '.wav':
            try:
                audio = WAVE(file_path)
                if hasattr(audio, 'tags') and audio.tags:
                    metadata['title'] = audio.tags.get('title', [''])[0] if 'title' in audio.tags else ''
                    metadata['artist'] = audio.tags.get('artist', [''])[0] if 'artist' in audio.tags else ''
                    metadata['album'] = audio.tags.get('album', [''])[0] if 'album' in audio.tags else ''
            except Exception:
                pass
    
    except Exception:
        pass
    
    return metadata

def get_audio_format_info(file_path):
    info = {}
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.mp3':
            audio = MP3(file_path)
            info['bitrate'] = f"{int(audio.info.bitrate / 1000)} kbps"
            info['sample_rate'] = f"{int(audio.info.sample_rate / 1000):.1f} kHz"
            info['length'] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}"
            info['channels'] = audio.info.channels
            info['format'] = 'MP3'
        
        elif file_ext == '.flac':
            audio = FLAC(file_path)
            info['bitrate'] = f"{int((os.path.getsize(file_path) * 8) / (audio.info.length * 1000))} kbps"
            info['sample_rate'] = f"{int(audio.info.sample_rate / 1000):.1f} kHz"
            info['length'] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}"
            info['channels'] = audio.info.channels
            info['format'] = 'FLAC'
            info['bits_per_sample'] = audio.info.bits_per_sample
        
        elif file_ext == '.wav':
            audio = WAVE(file_path)
            info['bitrate'] = f"{int((os.path.getsize(file_path) * 8) / (audio.info.length * 1000))} kbps"
            info['sample_rate'] = f"{int(audio.info.sample_rate / 1000):.1f} kHz"
            info['length'] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}"
            info['channels'] = audio.info.channels
            info['format'] = 'WAV'
        
        else:
            info['format'] = os.path.splitext(file_path)[1].upper().strip('.')
            info['size'] = f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MB"
    
    except Exception:
        info['format'] = os.path.splitext(file_path)[1].upper().strip('.')
        try:
            info['size'] = f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MB"
        except:
            pass
    
    return info

def detect_language(text):
    if not text:
        return "unknown"
    
    lang_words = {
        "pt": ["de", "a", "o", "e", "do", "da", "em", "para", "com", "um", "uma"],
        "en": ["the", "a", "of", "in", "and", "to", "for", "with", "by", "at"],
        "es": ["el", "la", "de", "y", "en", "un", "una", "para", "con", "por"]
    }
    
    words = re.findall(r'\b\w+\b', text.lower())
    counts = {lang: 0 for lang in lang_words}
    
    for word in words:
        for lang, lang_word_list in lang_words.items():
            if word in lang_word_list:
                counts[lang] += 1
    
    max_count = 0
    detected_lang = "unknown"
    for lang, count in counts.items():
        if count > max_count:
            max_count = count
            detected_lang = lang
    
    return detected_lang

def organize_music(source_folder, output_folder, update_progress, check_cancel):
    music_dict = {}
    unknown_metadata = []
    abs_output = os.path.abspath(output_folder)
    
    total_files = sum(len(files) for _, _, files in os.walk(source_folder))
    processed_files = 0
    
    for root_dir, dirs, files in os.walk(source_folder):
        if check_cancel():
            raise Exception("Processo cancelado pelo usuário.")
        
        if os.path.abspath(root_dir).startswith(abs_output):
            continue
        
        for file in files:
            if check_cancel():
                raise Exception("Processo cancelado pelo usuário.")
            
            supported_formats = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma')
            if file.lower().endswith(supported_formats):
                file_path = os.path.join(root_dir, file)
                
                try:
                    metadata = get_audio_metadata(file_path)
                    
                    artist = metadata['artist']
                    album = metadata['album']
                    title = metadata['title']
                    track_num = metadata['track_number']
                    album_art = metadata['album_art']
                    year = metadata['year']
                    genre = metadata['genre']
                    
                    if not artist or artist.strip() == "":
                        artist = "Desconhecido"
                        unknown_metadata.append(file)
                    
                    if not album or album.strip() == "":
                        album = "Desconhecido"
                        unknown_metadata.append(file)
                    
                    if not title or title.strip() == "":
                        title = os.path.splitext(file)[0]
                        unknown_metadata.append(file)
                    
                    artist = artist.replace("_", " ")
                    album = album.replace("_", " ")
                    title = title.replace("_", " ")
                    
                    if artist.isupper():
                        artist = artist.title()
                    if album.isupper():
                        album = album.title()
                    if title.isupper():
                        title = title.title()
                    
                    title = re.sub(r'^\d+\s*[-_.]?\s*', '', title).strip()
                    
                    try:
                        enhanced_artist, enhanced_title, enhanced_album = enhance_metadata(artist, title, album)
                        if enhanced_artist and enhanced_artist != "Desconhecido":
                            artist = enhanced_artist
                        if enhanced_title and enhanced_title != "Desconhecido":
                            title = enhanced_title
                        if enhanced_album and enhanced_album != "Desconhecido" and album == "Desconhecido":
                            album = enhanced_album
                    except Exception:
                        pass
                    
                    if album == "Desconhecido" and artist != "Desconhecido" and title != "Desconhecido":
                        try:
                            found_album = lookup_album_by_track_artist(title, artist)
                            if found_album:
                                album = found_album
                        except Exception:
                            pass
                    
                    artist = sanitize_string(artist)
                    album = sanitize_string(album)
                    title = sanitize_string(title)
                    
                    track_number = None
                    if track_num:
                        match = re.match(r'^(\d+)', track_num)
                        if match:
                            track_number = int(match.group(1))
                    
                    if not album_art and artist != "Desconhecido" and album != "Desconhecido":
                        album_art_url = get_album_art_url(artist, album)
                        if album_art_url:
                            album_art = download_album_art(album_art_url)
                    
                    audio_info = get_audio_format_info(file_path)
                    lang = detect_language(f"{artist} {album} {title}")
                    
                    if year:
                        year_match = re.search(r'\b(19|20)\d{2}\b', year)
                        if year_match:
                            year = year_match.group(0)
                        else:
                            year = None
                    
                    if album != "Desconhecido" and year:
                        album = f"{album} ({year})"
                    
                    music_dict.setdefault(artist, {}).setdefault(album, []).append({
                        'file_path': file_path,
                        'title': title,
                        'track_number': track_number,
                        'album_art': album_art,
                        'audio_info': audio_info,
                        'language': lang,
                        'year': year,
                        'genre': genre
                    })
                except Exception:
                    music_dict.setdefault("Desconhecido", {}).setdefault("Desconhecido", []).append({
                        'file_path': file_path,
                        'title': os.path.splitext(file)[0],
                        'track_number': None,
                        'album_art': None,
                        'audio_info': get_audio_format_info(file_path),
                        'language': "unknown",
                        'year': None,
                        'genre': None
                    })
                    unknown_metadata.append(file)
            
            processed_files += 1
            update_progress(processed_files, total_files, "Analisando arquivos")
    
    total_tracks = sum(len(files) for albums in music_dict.values() for files in albums.values())
    processed_tracks = 0
    
    try:
        for artist, albums in music_dict.items():
            if check_cancel():
                raise Exception("Processo cancelado pelo usuário.")
            
            artist_folder = os.path.join(output_folder, artist)
            os.makedirs(artist_folder, exist_ok=True)
            
            for album, files in albums.items():
                if check_cancel():
                    raise Exception("Processo cancelado pelo usuário.")
                
                album_folder = os.path.join(artist_folder, album)
                os.makedirs(album_folder, exist_ok=True)
                
                files_sorted = sorted(files, key=lambda x: (x['track_number'] or float('inf'), x['title']))
                
                for idx, file_info in enumerate(files_sorted, start=1):
                    if check_cancel():
                        raise Exception("Processo cancelado pelo usuário.")
                    
                    orig_path = file_info['file_path']
                    title = file_info['title']
                    ext = os.path.splitext(orig_path)[1]
                    
                    track_num = file_info['track_number'] or idx
                    new_filename = f"{track_num:02d} - {title}{ext}"
                    dest_path = os.path.join(album_folder, new_filename)
                    
                    try:
                        if len(dest_path) > 255:
                            shorter_title = title[:20] + "..." + title[-5:]
                            new_filename = f"{track_num:02d} - {shorter_title}{ext}"
                            dest_path = os.path.join(album_folder, new_filename)
                        
                        shutil.copy2(orig_path, dest_path)
                        
                        processed_tracks += 1
                        update_progress(processed_tracks, total_tracks, "Organizando arquivos")
                    except Exception:
                        pass
                
                if files and files[0]['album_art']:
                    try:
                        cover_path = os.path.join(album_folder, "cover.jpg")
                        with open(cover_path, 'wb') as f:
                            f.write(files[0]['album_art'])
                    except Exception:
                        pass
    
    except Exception as e:
        if "Processo cancelado pelo usuário" in str(e):
            raise e
    
    return unknown_metadata

def count_files(folder):
    total = 0
    try:
        for _, _, files in os.walk(folder):
            total += len(files)
    except Exception:
        pass
    return total

def copy_folder(source, destination, update_progress, total_files, progress_counter, check_cancel):
    try:
        for root_dir, dirs, files in os.walk(source):
            if check_cancel():
                raise Exception("Processo cancelado pelo usuário.")
            
            rel_path = os.path.relpath(root_dir, source)
            dest_dir = os.path.join(destination, rel_path)
            
            try:
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
            except Exception:
                pass
            
            for file in files:
                if check_cancel():
                    raise Exception("Processo cancelado pelo usuário.")
                
                src_file = os.path.join(root_dir, file)
                dst_file = os.path.join(dest_dir, file)
                
                try:
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    shutil.copy2(src_file, dst_file)
                except Exception:
                    pass
                
                progress_counter[0] += 1
                update_progress(progress_counter[0], total_files, "Copiando para o pen drive")
    except Exception as e:
        if "Processo cancelado pelo usuário" not in str(e):
            pass
        raise e

def copy_to_pen_drive(organized_folder, pen_drive_folder, mode, update_progress, check_cancel):
    dest_folder = os.path.join(pen_drive_folder, "Music")
    
    try:
        if mode == "formatar":
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            os.makedirs(dest_folder, exist_ok=True)
        else:
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder, exist_ok=True)
    except Exception:
        return
    
    total_files = count_files(organized_folder)
    if total_files == 0:
        return
    
    progress_counter = [0]
    
    try:
        copy_folder(organized_folder, dest_folder, update_progress, total_files, progress_counter, check_cancel)
    except Exception as e:
        if "Processo cancelado pelo usuário" in str(e):
            pass
        else:
            pass

def format_pen_drive(drive_path):
    drive_letter = os.path.splitdrive(drive_path)[0]
    if not drive_letter:
        return False
    
    try:
        if sys.platform == "win32":
            command = f'echo Y | format {drive_letter} /FS:FAT32 /Q'
            ret = os.system(command)
            if ret != 0:
                return False
        else:
            drive_dev = drive_path
            command = f'sudo mkfs.fat -F32 {drive_dev}'
            ret = os.system(command)
            if ret != 0:
                return False
    except Exception:
        return False
    
    return True

def rename_pen_drive(pen_drive_folder, new_name):
    try:
        drive = os.path.splitdrive(pen_drive_folder)[0]
        if not drive:
            return False
        
        letter = drive.rstrip(":")
        
        if sys.platform == "win32":
            subprocess.run(["powershell", "-Command", f"Set-Volume -DriveLetter {letter} -NewFileSystemLabel \"{new_name}\""], check=True)
            return True
        else:
            return False
    except Exception:
        return False

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        self.default_bg = kwargs.get('bg', ACCENT_COLOR)
        self.hover_bg = self._calculate_hover_color(self.default_bg)
        self.default_fg = kwargs.get('fg', 'white')
        
        if 'font' not in kwargs:
            kwargs['font'] = ('Segoe UI', 10)
        
        if 'relief' not in kwargs:
            kwargs['relief'] = 'flat'
            
        if 'borderwidth' not in kwargs:
            kwargs['borderwidth'] = 0
            
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _calculate_hover_color(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        if r + g + b > 600:
            r = max(r - 20, 0)
            g = max(g - 20, 0)
            b = max(b - 20, 0)
        else:
            r = min(r + 20, 255)
            g = min(g + 20, 255)
            b = min(b + 20, 255)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_enter(self, event):
        self.config(bg=self.hover_bg)
    
    def _on_leave(self, event):
        self.config(bg=self.default_bg)

class ModernEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        if 'font' not in kwargs:
            kwargs['font'] = ('Segoe UI', 10)
        
        if 'relief' not in kwargs:
            kwargs['relief'] = 'solid'
            
        if 'borderwidth' not in kwargs:
            kwargs['borderwidth'] = 1
            
        if 'bg' not in kwargs:
            kwargs['bg'] = SECONDARY_BG
            
        super().__init__(master, **kwargs)
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
    def _on_focus_in(self, event):
        self.config(bg='white')
        
    def _on_focus_out(self, event):
        self.config(bg=SECONDARY_BG)

class ProcessWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Progresso do Processo")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self.transient(parent)
        self.grab_set()
        
        self.title_font = ('Segoe UI', 16, 'bold')
        self.subtitle_font = ('Segoe UI', 12)
        self.normal_font = ('Segoe UI', 10)
        
        self.cancel_flag = False
        self.parent = parent
        
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        self.center_window()
        
    def create_widgets(self):
        self.status_label = tk.Label(
            self,
            text="Processando...",
            font=self.title_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        self.status_label.grid(row=0, column=0, pady=(30, 10))
        
        self.detail_label = tk.Label(
            self,
            text="Preparando o processo...",
            font=self.subtitle_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        self.detail_label.grid(row=1, column=0, pady=(0, 30))
        
        progress_frame = tk.Frame(self, bg=BG_COLOR, padx=50)
        progress_frame.grid(row=2, column=0, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="TProgressbar",
            orient="horizontal",
            length=500,
            mode="determinate"
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0%",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        self.progress_label.grid(row=1, column=0, pady=5)
        
        self.stats_label = tk.Label(
            progress_frame,
            text="Processados: 0 / 0",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        self.stats_label.grid(row=2, column=0, pady=5)
        
        self.cancel_button = ModernButton(
            self,
            text="Cancelar",
            command=self.cancel_process,
            bg=ERROR_COLOR,
            font=self.normal_font,
            padx=20,
            pady=5
        )
        self.cancel_button.grid(row=3, column=0, pady=40)
        
        self.style = ttk.Style()
        self.style.configure("TProgressbar", thickness=15, troughcolor=SECONDARY_BG, background=ACCENT_COLOR)
        
    def update_progress(self, current, total, stage):
        percent = (current / total) * 100 if total > 0 else 0
        self.progress_bar["value"] = percent
        self.progress_label.config(text=f"{percent:.1f}%")
        self.stats_label.config(text=f"Processados: {current} / {total}")
        self.detail_label.config(text=stage)
        self.update_idletasks()
    
    def set_status(self, status):
        self.status_label.config(text=status)
        self.update_idletasks()
    
    def cancel_process(self):
        self.cancel_flag = True
        self.detail_label.config(text="Cancelando processo, aguarde...")
        self.cancel_button.config(state="disabled")
        
    def is_cancelled(self):
        return self.cancel_flag
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

class MeloBurnApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Meloburn - Organizador de Músicas")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_COLOR)
        
        self.title_font = ('Segoe UI', 20, 'bold')
        self.heading_font = ('Segoe UI', 14, 'bold')
        self.normal_font = ('Segoe UI', 11)
        self.small_font = ('Segoe UI', 9)
        
        self.source_folder = ""
        self.pen_drive_folder = ""
        self.operation_mode = tk.StringVar(value="formatar")
        self.pen_drive_name = tk.StringVar(value="MUSIC")
        
        # Initialize current_frame to None
        self.current_frame = None
        self.frames = {}
        
        # Check admin privileges first
        self.check_admin()
        
        # Create all frames
        self.create_welcome_screen()
        self.create_source_step()
        self.create_destination_step()
        self.create_options_step()
        self.create_summary_step()
        
        # Explicitly show welcome frame
        self.show_frame("welcome")
        
        # Center the window on screen
        self.center_window()
        
    def check_admin(self):
        if not check_admin() and sys.platform == "win32":
            try:
                import ctypes
                import sys as sys_module
                
                script = sys_module.argv[0]
                params = ' '.join([f'"{item}"' for item in sys_module.argv[1:]])
                
                if script.endswith('.py'):
                    executable = sys_module.executable
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", executable, f'"{script}" {params}', None, 1
                    )
                else:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", script, params, None, 1
                    )
                
                self.root.destroy()
                sys_module.exit(0)
            except Exception:
                messagebox.showerror("Erro de Permissão", "Este programa requer privilégios de administrador para funcionar corretamente. Por favor, execute-o como administrador.")
                self.root.destroy()
                return
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_welcome_screen(self):
        welcome_frame = tk.Frame(self.root, bg=BG_COLOR)
        welcome_frame.grid(row=0, column=0, sticky="nsew")
        welcome_frame.grid_columnconfigure(0, weight=1)
        welcome_frame.grid_rowconfigure(3, weight=1)
        
        title_label = tk.Label(
            welcome_frame,
            text="Meloburn",
            font=self.title_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        title_label.grid(row=0, column=0, pady=(80, 5))
        
        subtitle_label = tk.Label(
            welcome_frame,
            text="Organizador de Músicas",
            font=self.heading_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 30))
        
        description_text = (
            "Bem-vindo ao Meloburn, o assistente para organizar suas músicas por artista e álbum.\n"
            "Este programa vai ajudar a organizar sua coleção musical para dispositivos de áudio."
        )
        
        description_label = tk.Label(
            welcome_frame,
            text=description_text,
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            justify="center",
            wraplength=500
        )
        description_label.grid(row=2, column=0, pady=(0, 50))
        
        start_button = ModernButton(
            welcome_frame,
            text="Iniciar",
            command=self.show_source_step,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.heading_font,
            padx=30,
            pady=10
        )
        start_button.grid(row=3, column=0, pady=(0, 80))
        
        self.frames["welcome"] = welcome_frame
    
    def create_source_step(self):
        source_frame = tk.Frame(self.root, bg=BG_COLOR)
        source_frame.grid(row=0, column=0, sticky="nsew")
        source_frame.grid_columnconfigure(0, weight=1)
        
        step_label = tk.Label(
            source_frame,
            text="Etapa 1 de 3",
            font=self.small_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        step_label.grid(row=0, column=0, pady=(30, 0))
        
        title_label = tk.Label(
            source_frame,
            text="Selecione a Pasta de Origem",
            font=self.heading_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        title_label.grid(row=1, column=0, pady=(5, 30))
        
        input_frame = tk.Frame(source_frame, bg=BG_COLOR, padx=50)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        description_label = tk.Label(
            input_frame,
            text="Selecione a pasta que contém os arquivos de música que você deseja organizar:",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            anchor="w",
            justify="left",
            wraplength=500
        )
        description_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        path_frame = tk.Frame(input_frame, bg=BG_COLOR)
        path_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        path_frame.grid_columnconfigure(0, weight=1)
        
        self.source_entry = ModernEntry(
            path_frame,
            font=self.normal_font,
            width=30
        )
        self.source_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_button = ModernButton(
            path_frame,
            text="Procurar",
            command=self.browse_source,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font
        )
        browse_button.grid(row=0, column=1)
        
        note_label = tk.Label(
            input_frame,
            text="Nota: O programa irá verificar recursivamente todas as subpastas dentro da pasta selecionada.",
            font=self.small_font,
            bg=BG_COLOR,
            fg="gray",
            anchor="w",
            justify="left",
            wraplength=500
        )
        note_label.grid(row=2, column=0, sticky="w", pady=(0, 20))
        
        button_frame = tk.Frame(source_frame, bg=BG_COLOR)
        button_frame.grid(row=3, column=0, pady=(50, 30))
        
        back_button = ModernButton(
            button_frame,
            text="Voltar",
            command=lambda: self.show_frame("welcome"),
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            font=self.normal_font,
            padx=15,
            pady=5
        )
        back_button.grid(row=0, column=0, padx=10)
        
        next_button = ModernButton(
            button_frame,
            text="Próximo",
            command=self.validate_source_and_continue,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font,
            padx=15,
            pady=5
        )
        next_button.grid(row=0, column=1, padx=10)
        
        self.frames["source"] = source_frame
    
    def create_destination_step(self):
        dest_frame = tk.Frame(self.root, bg=BG_COLOR)
        dest_frame.grid(row=0, column=0, sticky="nsew")
        dest_frame.grid_columnconfigure(0, weight=1)
        
        step_label = tk.Label(
            dest_frame,
            text="Etapa 2 de 3",
            font=self.small_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        step_label.grid(row=0, column=0, pady=(30, 0))
        
        title_label = tk.Label(
            dest_frame,
            text="Selecione o Pen Drive",
            font=self.heading_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        title_label.grid(row=1, column=0, pady=(5, 30))
        
        input_frame = tk.Frame(dest_frame, bg=BG_COLOR, padx=50)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        description_label = tk.Label(
            input_frame,
            text="Selecione o pen drive ou dispositivo de destino onde suas músicas serão organizadas:",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            anchor="w",
            justify="left",
            wraplength=500
        )
        description_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        path_frame = tk.Frame(input_frame, bg=BG_COLOR)
        path_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        path_frame.grid_columnconfigure(0, weight=1)
        
        self.dest_entry = ModernEntry(
            path_frame,
            font=self.normal_font,
            width=30
        )
        self.dest_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_button = ModernButton(
            path_frame,
            text="Procurar",
            command=self.browse_destination,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font
        )
        browse_button.grid(row=0, column=1)
        
        warning_label = tk.Label(
            input_frame,
            text="Aviso: Selecione com cuidado, pois dependendo das opções escolhidas, o conteúdo do dispositivo poderá ser apagado.",
            font=self.small_font,
            bg=BG_COLOR,
            fg=WARNING_COLOR,
            anchor="w",
            justify="left",
            wraplength=500
        )
        warning_label.grid(row=2, column=0, sticky="w", pady=(0, 20))
        
        button_frame = tk.Frame(dest_frame, bg=BG_COLOR)
        button_frame.grid(row=3, column=0, pady=(50, 30))
        
        back_button = ModernButton(
            button_frame,
            text="Voltar",
            command=lambda: self.show_frame("source"),
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            font=self.normal_font,
            padx=15,
            pady=5
        )
        back_button.grid(row=0, column=0, padx=10)
        
        next_button = ModernButton(
            button_frame,
            text="Próximo",
            command=self.validate_destination_and_continue,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font,
            padx=15,
            pady=5
        )
        next_button.grid(row=0, column=1, padx=10)
        
        self.frames["destination"] = dest_frame
    
    def create_options_step(self):
        options_frame = tk.Frame(self.root, bg=BG_COLOR)
        options_frame.grid(row=0, column=0, sticky="nsew")
        options_frame.grid_columnconfigure(0, weight=1)
        
        step_label = tk.Label(
            options_frame,
            text="Etapa 3 de 3",
            font=self.small_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        step_label.grid(row=0, column=0, pady=(30, 0))
        
        title_label = tk.Label(
            options_frame,
            text="Configurações",
            font=self.heading_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        title_label.grid(row=1, column=0, pady=(5, 30))
        
        input_frame = tk.Frame(options_frame, bg=BG_COLOR, padx=50)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        mode_label = tk.Label(
            input_frame,
            text="Modo de Operação:",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            anchor="w"
        )
        mode_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        format_radio = tk.Radiobutton(
            input_frame,
            text="Formatar o pen drive (apaga todo o conteúdo existente)",
            variable=self.operation_mode,
            value="formatar",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=SECONDARY_BG
        )
        format_radio.grid(row=1, column=0, sticky="w", padx=20, pady=5)
        
        add_radio = tk.Radiobutton(
            input_frame,
            text="Adicionar músicas (mantém o conteúdo existente)",
            variable=self.operation_mode,
            value="adicionar",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=SECONDARY_BG
        )
        add_radio.grid(row=2, column=0, sticky="w", padx=20, pady=5)
        
        name_frame = tk.Frame(input_frame, bg=BG_COLOR, pady=20)
        name_frame.grid(row=3, column=0, sticky="w")
        
        name_label = tk.Label(
            name_frame,
            text="Nome do pen drive:",
            font=self.normal_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        name_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        name_entry = ModernEntry(
            name_frame,
            textvariable=self.pen_drive_name,
            font=self.normal_font,
            width=15
        )
        name_entry.grid(row=0, column=1, sticky="w")
        
        button_frame = tk.Frame(options_frame, bg=BG_COLOR)
        button_frame.grid(row=3, column=0, pady=(50, 30))
        
        back_button = ModernButton(
            button_frame,
            text="Voltar",
            command=lambda: self.show_frame("destination"),
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            font=self.normal_font,
            padx=15,
            pady=5
        )
        back_button.grid(row=0, column=0, padx=10)
        
        next_button = ModernButton(
            button_frame,
            text="Próximo",
            command=self.validate_options_and_continue,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font,
            padx=15,
            pady=5
        )
        next_button.grid(row=0, column=1, padx=10)
        
        self.frames["options"] = options_frame
    
    def create_summary_step(self):
        summary_frame = tk.Frame(self.root, bg=BG_COLOR)
        summary_frame.grid(row=0, column=0, sticky="nsew")
        summary_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            summary_frame,
            text="Resumo da Operação",
            font=self.heading_font,
            bg=BG_COLOR,
            fg=FG_COLOR
        )
        title_label.grid(row=0, column=0, pady=(30, 30))
        
        summary_container = tk.Frame(summary_frame, bg=SECONDARY_BG, padx=30, pady=20, bd=1, relief="solid")
        summary_container.grid(row=1, column=0, padx=50, sticky="ew")
        summary_container.grid_columnconfigure(1, weight=1)
        
        source_label = tk.Label(
            summary_container,
            text="Pasta de origem:",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        source_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.summary_source = tk.Label(
            summary_container,
            text="",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        self.summary_source.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        dest_label = tk.Label(
            summary_container,
            text="Pen drive:",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        dest_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.summary_dest = tk.Label(
            summary_container,
            text="",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        self.summary_dest.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        mode_label = tk.Label(
            summary_container,
            text="Modo:",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        mode_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.summary_mode = tk.Label(
            summary_container,
            text="",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        self.summary_mode.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        name_label = tk.Label(
            summary_container,
            text="Nome do dispositivo:",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        name_label.grid(row=3, column=0, sticky="w", pady=5)
        
        self.summary_name = tk.Label(
            summary_container,
            text="",
            font=self.normal_font,
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            anchor="w"
        )
        self.summary_name.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        warning_text = (
            "Ao clicar em 'Iniciar Processo', o programa começará a organizar suas músicas. "
            "Dependendo da quantidade de arquivos, isso pode levar algum tempo. "
            "Por favor, não desconecte o pen drive durante o processo."
        )
        
        warning_label = tk.Label(
            summary_frame,
            text=warning_text,
            font=self.normal_font,
            bg=BG_COLOR,
            fg=WARNING_COLOR,
            justify="center",
            wraplength=550
        )
        warning_label.grid(row=2, column=0, pady=30)
        
        button_frame = tk.Frame(summary_frame, bg=BG_COLOR)
        button_frame.grid(row=3, column=0, pady=(20, 30))
        
        back_button = ModernButton(
            button_frame,
            text="Voltar",
            command=lambda: self.show_frame("options"),
            bg=SECONDARY_BG,
            fg=FG_COLOR,
            font=self.normal_font,
            padx=15,
            pady=5
        )
        back_button.grid(row=0, column=0, padx=10)
        
        start_button = ModernButton(
            button_frame,
            text="Iniciar Processo",
            command=self.start_process,
            bg=ACCENT_COLOR,
            fg="white",
            font=self.normal_font,
            padx=15,
            pady=5
        )
        start_button.grid(row=0, column=1, padx=10)
        
        self.frames["summary"] = summary_frame
    
    def show_frame(self, frame_name):
        # Hide all frames first
        for frame in self.frames.values():
            frame.grid_remove()
        
        # Show the requested frame
        self.frames[frame_name].grid(row=0, column=0, sticky="nsew")
        self.current_frame = self.frames[frame_name]
        
        # Configure grid to expand correctly
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def show_source_step(self):
        self.show_frame("source")
    
    def browse_source(self):
        folder = filedialog.askdirectory(title="Selecione a pasta com as músicas")
        if folder:
            self.source_folder = folder
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)
    
    def validate_source_and_continue(self):
        if not self.source_entry.get().strip():
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de origem.")
            return
        
        self.source_folder = self.source_entry.get().strip()
        
        if not os.path.exists(self.source_folder):
            messagebox.showerror("Erro", "A pasta selecionada não existe.")
            return
        
        self.show_frame("destination")
    
    def browse_destination(self):
        folder = filedialog.askdirectory(title="Selecione o pen drive")
        if folder:
            self.pen_drive_folder = folder
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)
    
    def validate_destination_and_continue(self):
        if not self.dest_entry.get().strip():
            messagebox.showerror("Erro", "Por favor, selecione o pen drive ou dispositivo de destino.")
            return
        
        self.pen_drive_folder = self.dest_entry.get().strip()
        
        if not os.path.exists(self.pen_drive_folder):
            messagebox.showerror("Erro", "O dispositivo selecionado não existe.")
            return
        
        self.show_frame("options")
    
    def validate_options_and_continue(self):
        if self.operation_mode.get() == "formatar":
            result = messagebox.askyesno(
                "Confirmação",
                "Você selecionou a opção de formatar o pen drive. "
                "Isso apagará TODOS os dados existentes no dispositivo. "
                "Tem certeza que deseja continuar?",
                icon=messagebox.WARNING
            )
            
            if not result:
                return
        
        self.update_summary_info()
        self.show_frame("summary")
    
    def update_summary_info(self):
        self.summary_source.config(text=self.source_folder)
        self.summary_dest.config(text=self.pen_drive_folder)
        
        if self.operation_mode.get() == "formatar":
            mode_text = "Formatar (apagar todo o conteúdo)"
        else:
            mode_text = "Adicionar (manter conteúdo existente)"
            
        self.summary_mode.config(text=mode_text)
        self.summary_name.config(text=self.pen_drive_name.get())
    
    def start_process(self):
        process_window = ProcessWindow(self.root)
        
        def process_thread():
            temp_folder = os.path.join(os.path.expanduser("~"), ".meloburn_temp")
            
            try:
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
                os.makedirs(temp_folder, exist_ok=True)
                
                process_window.set_status("Analisando músicas")
                
                unknown_files = organize_music(
                    self.source_folder,
                    temp_folder,
                    process_window.update_progress,
                    process_window.is_cancelled
                )
                
                if process_window.is_cancelled():
                    raise Exception("Processo cancelado pelo usuário.")
                
                if self.operation_mode.get() == "formatar":
                    process_window.set_status("Formatando pen drive")
                    success = format_pen_drive(self.pen_drive_folder)
                    if not success:
                        raise Exception("Falha ao formatar o pen drive.")
                
                process_window.set_status("Copiando para o pen drive")
                
                copy_to_pen_drive(
                    temp_folder,
                    self.pen_drive_folder,
                    self.operation_mode.get(),
                    process_window.update_progress,
                    process_window.is_cancelled
                )
                
                if process_window.is_cancelled():
                    raise Exception("Processo cancelado pelo usuário.")
                
                if self.pen_drive_name.get().strip():
                    process_window.set_status("Configurando nome do dispositivo")
                    rename_pen_drive(self.pen_drive_folder, self.pen_drive_name.get())
                
                process_window.set_status("Concluído")
                
                if not process_window.is_cancelled():
                    self.show_completion_safe(process_window, unknown_files)
            
            except Exception as e:
                error_msg = str(e)
                if "Processo cancelado pelo usuário" in error_msg:
                    self.show_cancellation_safe(process_window)
                else:
                    self.show_error_safe(process_window, error_msg)
            
            finally:
                try:
                    if os.path.exists(temp_folder):
                        shutil.rmtree(temp_folder)
                except Exception:
                    pass
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def show_completion_safe(self, process_window, unknown_files):
        def callback():
            try:
                process_window.destroy()
                
                result_message = "Processo concluído com sucesso! Suas músicas foram organizadas no dispositivo."
                
                if unknown_files and len(unknown_files) > 0:
                    result_message += f"\n\n{len(unknown_files)} arquivos não tinham metadados completos e foram organizados na pasta 'Desconhecido'."
                
                messagebox.showinfo("Concluído", result_message)
                self.show_frame("welcome")
            except Exception:
                pass
        
        self.root.after(1000, callback)
    
    def show_cancellation_safe(self, process_window):
        def callback():
            try:
                process_window.destroy()
                messagebox.showinfo("Cancelado", "O processo foi cancelado pelo usuário.")
            except Exception:
                pass
        
        self.root.after(0, callback)
    
    def show_error_safe(self, process_window, error_message):
        def callback():
            try:
                process_window.destroy()
                messagebox.showerror("Erro", f"Ocorreu um erro durante o processo:\n\n{error_message}")
            except Exception:
                pass
        
        self.root.after(0, callback)

if __name__ == "__main__":
    def handle_exception(exc_type, exc_value, exc_traceback):
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        messagebox.showerror(
            "Erro Não Esperado",
            f"Ocorreu um erro inesperado:\n\n{str(exc_value)}\n\nPor favor, reporte este erro para o desenvolvedor."
        )
        print(error_msg)
    
    sys.excepthook = handle_exception
    
    try:
        root = tk.Tk()
        app = MeloBurnApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erro de Inicialização", f"Erro ao iniciar o aplicativo:\n\n{str(e)}")
        traceback.print_exc()
