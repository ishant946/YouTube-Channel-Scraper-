# --- FINAL CORRECTED CODE ---
import streamlit as st
import pandas as pd
import yt_dlp
import re

st.set_page_config(page_title="YouTube Channel Scraper", page_icon="▶️", layout="centered")

# --- Language Code to Full Name Mapping ---
LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
    'de': 'German', 'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean',
    'pt': 'Portuguese', 'ru': 'Russian', 'zh-Hans': 'Chinese (Simplified)'
}

def check_available_languages(channel_url):
    # --- NEW STRATEGY: Append /videos to the URL ---
    if not channel_url.endswith('/videos'):
        channel_url = channel_url.rstrip('/') + '/videos'

    ydl_opts = {
        'playlist_items': '1', 'quiet': True, 'no_warnings': True, 'extract_flat': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(channel_url, download=False)
            if 'entries' in playlist_info and playlist_info['entries']:
                video_id = playlist_info['entries'][0]['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                sub_opts = {'listsubtitles': True, 'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(sub_opts) as sub_ydl:
                    video_info = sub_ydl.extract_info(video_url, download=False)
                    if 'subtitles' in video_info and video_info['subtitles']:
                        return sorted(list(video_info['subtitles'].keys()))
    except Exception as e:
        st.error("Could not check languages. This may be due to YouTube blocking requests from this server.")
        st.code(f"Debug details: {e}")
        return []
    return []

def get_filtered_video_list(channel_url, content_type, sort_by, limit):
    if not channel_url.endswith('/videos'):
        channel_url = channel_url.rstrip('/') + '/videos'
    
    filter_opts = {
        'quiet': True, 'extract_flat': 'in_playlist', 'no_warnings': True
    }
    if content_type == "Longs":
        filter_opts['match_filter'] = yt_dlp.utils.match_filter_func('duration >= 60')
    elif content_type == "Shorts":
        filter_opts['match_filter'] = yt_dlp.utils.match_filter_func('duration < 60')
    if sort_by == "Latest":
        filter_opts['playlistend'] = limit
    
    with st.spinner("Fetching video list..."):
        try:
            with yt_dlp.YoutubeDL(filter_opts) as ydl:
                playlist_info = ydl.extract_info(channel_url, download=False)
                entries = playlist_info.get('entries', [])
                if not entries:
                    st.warning("No videos found matching your filter criteria.")
                    return []
                if sort_by == "Most Popular":
                    st.info("Fetching view counts for sorting... this is slower.")
                    ids = [entry['id'] for entry in entries[:limit * 2] if entry]
                    pop_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
                    with yt_dlp.YoutubeDL(pop_opts) as pop_ydl:
                        video_details = pop_ydl.extract_info(f"https://www.youtube.com/watch?v={','.join(ids)}", download=False)
                        sorted_videos = sorted(video_details['entries'], key=lambda x: x.get('view_count', 0), reverse=True)
                        return [v['webpage_url'] for v in sorted_videos[:limit]]
                return [entry['url'] for entry in entries[:limit] if entry]
        except Exception as e:
            st.error(f"Could not fetch video list: {e}")
            return []

def clean_transcript(vtt_content):
    if not vtt_content: return ""
    lines = vtt_content.splitlines()
    transcript_lines = []
    for line in lines:
        if not line.strip() or '-->' in line or line.startswith(('WEBVTT', 'Kind:', 'Language:')):
            continue
        cleaned_line = re.sub(r'<[^>]+>', '', line)
        transcript_lines.append(cleaned_line.strip())
    return " ".join(transcript_lines)

# --- Streamlit UI ---
st.title("▶️ YouTube Channel Scraper Pro")
st.write("This tool scrapes video details and transcripts from a YouTube channel.")

if 'languages' not in st.session_state:
    st.session_state.languages = []
if 'processing_started' not in st.session_state:
    st.session_state.processing_started = False

st.header("1. Enter YouTube Channel URL")
channel_url = st.text_input("Channel URL", placeholder="e.g., https://www.youtube.com/@MrBeast")

if st.button("Check Available Languages"):
    st.session_state.languages = []
    st.session_state.processing_started = False
    if not channel_url:
        st.warning("Please enter a channel URL first.")
    else:
        with st.spinner("Inspecting channel for available subtitles..."):
            st.session_state.languages = check_available_languages(channel_url)
            if st.session_state.languages:
                st.success("Languages found! Please proceed to step 2.")
            else:
                st.error("No subtitle languages found. The channel may have no videos or YouTube may be blocking requests from this server.")

if st.session_state.languages:
    st.header("2. Set Filters and Options")
    lang_code = st.selectbox("Select Language", st.session_state.languages, format_func=lambda x: f"{LANG_MAP.get(x, x)} ({x})")
    content_type = st.radio("Content Type", ["All", "Longs", "Shorts"
