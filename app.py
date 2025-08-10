# --- COPY THIS ENTIRE CODE BLOCK ---
import streamlit as st
import pandas as pd
import yt_dlp
import re

# --- Language Code to Full Name Mapping ---
LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
    'de': 'German', 'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean',
    'pt': 'Portuguese', 'ru': 'Russian', 'zh-Hans': 'Chinese (Simplified)'
}

# --- Page Configuration ---
st.set_page_config(
    page_title="YouTube Channel Scraper",
    page_icon="▶️",
    layout="centered"
)

st.title("▶️ YouTube Channel Scraper Pro")
st.write("This tool scrapes video details and transcripts from a YouTube channel.")

# --- Helper Functions (Refactored from your original script) ---

def check_available_languages(channel_url):
    """
    Checks for available subtitle languages for the first video in a channel.
    This now uses the yt-dlp Python library instead of a subprocess.
    """
    ydl_opts = {
        'listsubtitles': True,
        'playlist_items': '1', # Only check the first video to be fast
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info and info[0]:
                video_info = info['entries'][0]
                if 'subtitles' in video_info and video_info['subtitles']:
                    return sorted(list(video_info['subtitles'].keys()))
    except Exception as e:
        st.error(f"Could not check languages. Error: {e}")
        return []
    return []

def get_filtered_video_list(channel_url, content_type, sort_by, limit):
    """
    Fetches a list of video URLs based on the user's filters.
    This has been refactored to use the yt-dlp library directly.
    """
    filter_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist', # More efficient than full extraction
        'no_warnings': True,
    }

    if content_type == "Longs":
        filter_opts['match_filter'] = yt_dlp.utils.match_filter_func('duration >= 60')
    elif content_type == "Shorts":
        filter_opts['match_filter'] = yt_dlp.utils.match_filter_func('duration < 60')

    if sort_by == "Latest":
        filter_opts['playlistend'] = limit
    
    with st.spinner(f"Fetching video list... This may take a moment."):
        try:
            with yt_dlp.YoutubeDL(filter_opts) as ydl:
                playlist_info = ydl.extract_info(channel_url, download=False)
                video_entries = playlist_info.get('entries', [])

                if not video_entries:
                    st.warning("No videos found matching your filter criteria.")
                    return []
                
                # If sorting by "Most Popular", we need to fetch view counts, which is slower.
                if sort_by == "Most Popular":
                    st.info("Fetching view counts for 'Most Popular' sort... this is slower.")
                    # We need to re-fetch with more info for sorting
                    popular_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False, # Need full info for views
                        'playlistend': 50 if limit < 50 else limit # Fetch a larger pool to sort from
                    }
                    with yt_dlp.YoutubeDL(popular_opts) as pop_ydl:
                         playlist_info_pop = pop_ydl.extract_info(channel_url, download=False)
                         video_entries = playlist_info_pop.get('entries', [])
                         # Filter out entries without view_count
                         video_entries = [v for v in video_entries if v and v.get('view_count')]
                         # Sort by view count descending
                         video_entries.sort(key=lambda x: x.get('view_count', 0), reverse=True)


                # Limit the results and return the URLs
                return [entry['url'] for entry in video_entries[:limit] if entry]

        except Exception as e:
            st.error(f"Could not fetch video list: {e}")
            return []


def clean_srt(srt_content):
    """Cleans SRT content to get plain text."""
    if not srt_content: return ""
    # Remove timestamps and sequence numbers
    text_only = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', srt_content)
    text_only = re.sub(r'^\d+\n', '', text_only, flags=re.MULTILINE)
    return text_only.replace('\n', ' ').strip()


# --- Streamlit UI Layout ---

# Initialize session state to store data between reruns
if 'languages' not in st.session_state:
    st.session_state['languages'] = []
if 'processing_started' not in st.session_state:
    st.session_state['processing_started'] = False

# --- 1. URL Input and Language Check ---
st.header("1. Enter YouTube Channel URL")
channel_url = st.text_input("Channel URL", placeholder="e.g., https://www.youtube.com/@MrBeast")

if st.button("Check Available Languages", key='check_lang'):
    if not channel_url:
        st.warning("Please enter a channel URL first.")
    else:
        with st.spinner("Checking..."):
            st.session_state['languages'] = check_available_languages(channel_url)
            if not st.session_state['languages']:
                st.error("No subtitle languages found for this channel.")
            else:
                st.success("Languages found! Please proceed to step 2.")

# --- 2. Filters and Options ---
if st.session_state['languages']:
    st.header("2. Set Filters and Options")

    # Create formatted list for the selectbox
    formatted_langs = [f"{LANG_MAP.get(code, code)} ({code})" for code in st.session_state['languages']]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_lang_formatted = st.selectbox("Select Language", formatted_langs)
        # Extract the language code (e.g., 'en') from the selection
        lang_code = selected_lang_formatted.split('(')[-1].replace(')', '')
    
    with col2:
        content_type = st.radio("Content Type", ["All", "Longs", "Shorts"], horizontal=True)

    with col3:
        sort_by = st.radio("Sort By", ["Latest", "Most Popular"], horizontal=True)

    limit = st.number_input("Number of videos to process", min_value=1, max_value=100, value=10)

    # --- 3. Start Processing ---
    st.header("3. Start Processing")
    if st.button("Start Scraping", type="primary"):
        st.session_state['processing_started'] = True

# --- 4. Processing Logic and Output ---
if st.session_state.get('processing_started'):
    # This block runs after the "Start Scraping" button is pressed
    video_urls = get_filtered_video_list(channel_url, content_type, sort_by, limit)
    total_videos = len(video_urls)
    all_video_data = []

    if total_videos > 0:
        st.info(f"Found {total_videos} videos. Starting data extraction...")
        progress_bar = st.progress(0)
        log_area = st.empty()

        for i, video_url in enumerate(video_urls):
            log_area.info(f"Processing video {i+1}/{total_videos}...")
            ydl_opts = {
                'writesubtitles': True,
                'subtitleslangs': [lang_code],
                'writeautomaticsub': True,
                'subtitlesformat': 'srt',
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    transcript_text = ""
                    # The downloaded subtitle content is in the 'requested_subtitles' key
                    if 'requested_subtitles' in info and info['requested_subtitles']:
                        sub_info = info['requested_subtitles'][lang_code]
                        if 'data' in sub_info:
                           transcript_text = clean_srt(sub_info['data'])

                    all_video_data.append({
                        'title': info.get('title'),
                        'view_count': info.get('view_count'),
                        'upload_date': info.get('upload_date'),
                        'duration': info.get('duration'),
                        'video_url': info.get('webpage_url'),
                        'transcript': transcript_text
                    })
            except Exception:
                log_area.warning(f"Failed to process video {i+1}. Skipping.")

            progress_bar.progress((i + 1) / total_videos)
        
        log_area.success("Processing Complete!")
        
        # Create a DataFrame and allow download
        df = pd.DataFrame(all_video_data)
        csv_data = df.to_csv(index=False).encode('utf-8')
        
        # Get channel name for the filename
        channel_name = channel_url.split('@')[-1].split('/')[0]

        st.download_button(
           label="📥 Download Data as CSV",
           data=csv_data,
           file_name=f"{channel_name}_data.csv",
           mime="text/csv",
        )
        
        st.dataframe(df) # Display the results on the page

    st.session_state['processing_started'] = False # Reset for next run
# --- END OF CODE BLOCK ---
