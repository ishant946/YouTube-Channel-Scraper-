import tkinter
import customtkinter
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import json
import csv
import re
import shutil

# --- Set the appearance of the app ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# --- Language Code to Full Name Mapping ---
LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French',
    'de': 'German', 'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean',
    'pt': 'Portuguese', 'ru': 'Russian', 'zh-Hans': 'Chinese (Simplified)'
}

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Configure the main window ---
        self.title("YouTube Channel Scraper Pro")
        self.geometry("800x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Frame for URL and Language Check ---
        self.setup_frame = customtkinter.CTkFrame(self)
        self.setup_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.setup_frame.grid_columnconfigure(0, weight=1)

        self.url_label = customtkinter.CTkLabel(self.setup_frame, text="1. Enter YouTube Channel URL", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.url_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.url_entry = customtkinter.CTkEntry(self.setup_frame, placeholder_text="e.g., https://www.youtube.com/@MrBeast")
        self.url_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.check_langs_button = customtkinter.CTkButton(self.setup_frame, text="2. Check Available Languages", command=self.start_language_check_thread)
        self.check_langs_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Frame for Filters and Options ---
        self.options_frame = customtkinter.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.options_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.lang_label = customtkinter.CTkLabel(self.options_frame, text="3. Select Language", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.lang_label.grid(row=0, column=0, padx=10, pady=(10,0), sticky="w")
        self.lang_var = customtkinter.StringVar(value="Check languages first")
        self.lang_menu = customtkinter.CTkOptionMenu(self.options_frame, variable=self.lang_var, values=["Check languages first"])
        self.lang_menu.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.content_label = customtkinter.CTkLabel(self.options_frame, text="Content Type", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.content_label.grid(row=0, column=1, padx=10, pady=(10,0), sticky="w")
        self.content_type_var = customtkinter.StringVar(value="All")
        customtkinter.CTkRadioButton(self.options_frame, text="All", variable=self.content_type_var, value="All").grid(row=1, column=1, padx=10, pady=10, sticky="w")
        customtkinter.CTkRadioButton(self.options_frame, text="Longs", variable=self.content_type_var, value="Longs").grid(row=2, column=1, padx=10, pady=5, sticky="w")
        customtkinter.CTkRadioButton(self.options_frame, text="Shorts", variable=self.content_type_var, value="Shorts").grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.sort_label = customtkinter.CTkLabel(self.options_frame, text="Sort & Limit", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.sort_label.grid(row=0, column=2, padx=10, pady=(10,0), sticky="w")
        self.sort_by_var = customtkinter.StringVar(value="Latest")
        customtkinter.CTkRadioButton(self.options_frame, text="Latest", variable=self.sort_by_var, value="Latest").grid(row=1, column=2, padx=10, pady=10, sticky="w")
        customtkinter.CTkRadioButton(self.options_frame, text="Most Popular", variable=self.sort_by_var, value="Most Popular").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        self.limit_entry = customtkinter.CTkEntry(self.options_frame, placeholder_text="Limit", width=120)
        self.limit_entry.insert(0, "20")
        self.limit_entry.grid(row=3, column=2, padx=10, pady=10, sticky="w")
        
        # --- Frame for Output Location and Actions ---
        self.action_frame = customtkinter.CTkFrame(self)
        self.action_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.output_label = customtkinter.CTkLabel(self.action_frame, text="4. Select Output Location", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.output_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
        self.output_dir_var = customtkinter.StringVar()
        self.output_entry = customtkinter.CTkEntry(self.action_frame, textvariable=self.output_dir_var, state='readonly')
        self.output_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.browse_button = customtkinter.CTkButton(self.action_frame, text="Browse...", command=self.select_output_dir, width=100)
        self.browse_button.grid(row=1, column=1, padx=10, pady=10)

        self.start_button = customtkinter.CTkButton(self.action_frame, text="5. Start Processing", command=self.start_processing_thread, font=customtkinter.CTkFont(size=14, weight="bold"))
        self.start_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.start_button.configure(state="disabled")

        # --- Progress Log ---
        self.log_area = customtkinter.CTkTextbox(self, wrap=tkinter.WORD)
        self.log_area.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # --- Exit Button ---
        self.exit_button = customtkinter.CTkButton(self, text="Exit", command=self.destroy, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        self.exit_button.grid(row=4, column=0, padx=20, pady=10, sticky="e")

    def log(self, message):
        self.after(0, self.log_area.insert, "end", message + "\n")
        self.after(0, self.log_area.see, "end")

    def select_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def start_language_check_thread(self):
        url = self.url_entry.get()
        if not url: return messagebox.showerror("Error", "Please enter a channel URL first.")
        self.check_langs_button.configure(state="disabled", text="Checking...")
        self.start_button.configure(state="disabled")
        threading.Thread(target=self.check_available_languages, args=(url,)).start()

    def check_available_languages(self, url):
        self.log("Checking available languages...")
        try:
            command = ['yt-dlp', '--list-subs', '--playlist-items', '1', url]
            process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
            languages_found = set(re.findall(r'^([a-zA-Z-]+)\s', process.stdout, re.MULTILINE))
            self.after(0, self.update_language_dropdown, sorted(list(languages_found)))
        except Exception as e:
            messagebox.showerror("Language Check Failed", f"Could not check languages. Error: {e}")
        finally:
            self.check_langs_button.configure(state="normal", text="2. Check Available Languages")

    def update_language_dropdown(self, lang_codes):
        if not lang_codes:
            self.log("No subtitles found for this channel.")
            return messagebox.showwarning("No Subtitles", "Could not find any available subtitle languages for this channel.")
        
        formatted_langs = [f"{LANG_MAP.get(code, code)} ({code})" for code in lang_codes]
        self.lang_menu.configure(values=formatted_langs)
        self.lang_var.set(formatted_langs[0])
        self.log("Languages found! Please set filters and start.")
        self.start_button.configure(state="normal")
        
    def start_processing_thread(self):
        # Validation checks
        if not self.output_dir_var.get():
            return messagebox.showerror("Error", "Please select an output location first.")
        try:
            # THIS IS THE CORRECTED LINE
            limit = int(self.limit_entry.get())
            if limit <= 0: raise ValueError
        except ValueError:
            return messagebox.showerror("Error", "Please enter a valid, positive number for the video limit.")

        self.start_button.configure(state="disabled", text="Working...")
        self.check_langs_button.configure(state="disabled")
        threading.Thread(target=self.run_full_process).start()
    
    def run_full_process(self):
        # All variables are now correctly referenced with 'self.'
        channel_url = self.url_entry.get()
        lang_code = self.lang_var.get().split('(')[-1].replace(')', '')
        content_type = self.content_type_var.get()
        sort_by = self.sort_by_var.get()
        limit = int(self.limit_entry.get())
        output_dir = self.output_dir_var.get()
        temp_dir = os.path.join(output_dir, "temp_youtube_data")
        
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        self.log_area.delete('1.0', "end")
        
        all_video_data = []
        try:
            video_urls = self.get_filtered_video_list(channel_url, content_type, sort_by, limit)
            total_videos = len(video_urls)
            if total_videos == 0:
                raise Exception("No videos found matching your filter criteria.")
            
            self.log(f"Found {total_videos} videos to process...")
            
            for i, video_url in enumerate(video_urls):
                video_id = video_url.split("v=")[-1]
                self.log(f"--- Processing video {i+1}/{total_videos} (ID: {video_id}) ---")
                try:
                    command = ['yt-dlp', '--write-auto-sub', '--sub-lang', lang_code, '--sub-format', 'srt', '--write-info-json', '--skip-download', '-o', os.path.join(temp_dir, '%(id)s.%(ext)s'), video_url]
                    subprocess.run(command, check=True, capture_output=True, timeout=60)

                    json_path = os.path.join(temp_dir, f"{video_id}.info.json")
                    srt_path = os.path.join(temp_dir, f"{video_id}.{lang_code}.srt")
                    
                    with open(json_path, 'r', encoding='utf-8') as f: metadata = json.load(f)
                    transcript = self.clean_srt_and_get_text(srt_path)
                    
                    all_video_data.append({'title': metadata.get('title'), 'view_count': metadata.get('view_count'), 'upload_date': metadata.get('upload_date'), 'duration': metadata.get('duration'), 'video_url': metadata.get('webpage_url'), 'transcript': transcript})
                    self.log(f"SUCCESS: {metadata.get('title')}")

                except subprocess.TimeoutExpired:
                    self.log(f"SKIPPED: Video {video_id} took too long.")
                except Exception as e:
                    self.log(f"ERROR on video {video_id}. Skipping.")
            
            output_filename = os.path.join(output_dir, f"{channel_url.split('@')[-1].replace('/', '_')}_data.csv")
            with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                headers = ['title', 'view_count', 'upload_date', 'duration', 'video_url', 'transcript']
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(all_video_data)
            messagebox.showinfo("Success!", f"Process complete! Data for {len(all_video_data)} videos saved to:\n{output_filename}")

        except Exception as e:
            messagebox.showerror("A Major Error Occurred", str(e))
        finally:
            self.log("--- Cleaning up temporary files ---\nDone.")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            self.enable_buttons()

    def enable_buttons(self):
        self.start_button.configure(state="normal", text="5. Start Processing")
        self.check_langs_button.configure(state="normal", text="2. Check Available Languages")

    def get_filtered_video_list(self, channel_url, content_type, sort_by, limit):
        self.log(f"Fetching and filtering video list...")
        command = ['yt-dlp', '--flat-playlist']
        if content_type == "Longs": command.extend(['--match-filter', 'duration >= 60'])
        elif content_type == "Shorts": command.extend(['--match-filter', 'duration < 60'])
        if sort_by == "Latest": command.extend(['--playlist-end', str(limit), '--get-id'])
        else: command.extend(['--print', '%(id)s,%(view_count)s'])
        command.append(channel_url)
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=180)
            output_lines = process.stdout.strip().split('\n')
            if sort_by == "Latest":
                video_ids = [line for line in output_lines if line]
                return [f"https://www.youtube.com/watch?v={vid_id}" for vid_id in video_ids]
            else:
                video_data = []
                for line in output_lines:
                    if ',' in line:
                        vid_id, view_count_str = line.split(',', 1)
                        if vid_id and view_count_str and view_count_str.isdigit():
                            video_data.append({'id': vid_id, 'views': int(view_count_str)})
                sorted_videos = sorted(video_data, key=lambda x: x['views'], reverse=True)
                limited_videos = sorted_videos[:limit]
                return [f"https://www.youtube.com/watch?v={item['id']}" for item in limited_videos]
        except Exception as e:
            raise Exception(f"Could not fetch video list: {e}")

    def clean_srt_and_get_text(self, srt_file_path):
        if not os.path.exists(srt_file_path): return ""
        try:
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                text_only = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
                text_only = re.sub(r'^\d+\n', '', text_only, flags=re.MULTILINE)
                return text_only.replace('\n', ' ').strip()
        except Exception as e:
            print(f"Error reading SRT {srt_file_path}: {e}")
            return ""

if __name__ == "__main__":
    app = App()
    app.mainloop()
