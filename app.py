import streamlit as st
import os
import shutil
import json
import pandas as pd
from scraper import fetch_html, extract_menu_data, process_menu_data, download_image, merge_data
from urllib.parse import urlparse
from datetime import datetime

st.set_page_config(page_title="Talabat Menu Scraper", layout="wide")

st.title("Talabat Menu Scraper")
st.markdown("Extract menu items, prices, and images from Talabat restaurant pages.")

# --- Sidebar Options ---
st.sidebar.header("Configuration")
download_images = st.sidebar.checkbox("Download Images", value=True)
output_format = st.sidebar.radio("Output Format", ["CSV", "JSON", "Both"], index=0)

# --- Main Input ---
url_input = st.text_input("Enter Talabat Restaurant URL (English or Arabic)", placeholder="https://www.talabat.com/jordan/restaurant/...")

# --- Session State Initialization ---
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'csv_path' not in st.session_state:
    st.session_state.csv_path = None
if 'json_paths' not in st.session_state:
    st.session_state.json_paths = {}
if 'zip_path' not in st.session_state:
    st.session_state.zip_path = None

def run_scraper():
    if not url_input:
        st.error("Please enter a URL.")
        return

    # Create a timestamped session ID for file storage
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Try to get a restaurant name from URL for the folder
    try:
        path_parts = urlparse(url_input).path.split('/')
        # usually /country/restaurant/id/name
        # find the part after 'restaurant' if possible, or just use the last part
        if 'restaurant' in path_parts:
            idx = path_parts.index('restaurant')
            if idx + 2 < len(path_parts):
                rest_name = path_parts[idx+2]
            else:
                rest_name = "unknown"
        else:
            rest_name = "unknown"
    except:
        rest_name = "unknown"

    session_id = os.path.join("scraped_data", f"{timestamp}_{rest_name}")
    os.makedirs(session_id, exist_ok=True)
    images_dir = os.path.join(session_id, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    st.session_state.session_id = session_id

    # Determine URLs
    url_en = ""
    url_ar = ""
    
    parsed_url = urlparse(url_input)
    path = parsed_url.path
    
    if "/ar/" in path:
        url_ar = url_input
        # Try to construct English URL
        path_en = path.replace("/ar/", "/")
        url_en = f"{parsed_url.scheme}://{parsed_url.netloc}{path_en}?{parsed_url.query}"
    else:
        url_en = url_input
        # Try to construct Arabic URL
        url_ar = f"{parsed_url.scheme}://{parsed_url.netloc}/ar{path}?{parsed_url.query}"

    st.info(f"Processing URLs:\n- EN: {url_en}\n- AR: {url_ar}")
    
    progress_bar = st.progress(0)
    
    # --- Logging Setup ---
    log_container = st.empty()
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    # Clear logs for new run
    st.session_state.logs = []

    def log(message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.logs.append(f"[{timestamp}] {message}")
        # Join logs with newlines and display in a code block for terminal look
        log_text = "\n".join(st.session_state.logs)
        log_container.code(log_text, language="text")

    # --- Scraping ---
    data_en = []
    data_ar = []
    
    # 1. Scrape English
    log("Fetching English Menu...")
    try:
        html_en = fetch_html(url_en)
        json_en = extract_menu_data(html_en)
        if json_en:
            data_en = process_menu_data(json_en)
            log(f"Found {len(data_en)} items in English menu.")
            # Save raw JSON
            json_path = os.path.join(session_id, "menu_en.json")
            with open(json_path, "w") as f:
                json.dump(json_en, f, indent=2)
            st.session_state.json_paths['en'] = json_path
        else:
            log("WARNING: Could not extract English menu data.")
    except Exception as e:
        log(f"ERROR fetching English URL: {e}")
    
    progress_bar.progress(30)
    
    # 2. Scrape Arabic
    log("Fetching Arabic Menu...")
    try:
        html_ar = fetch_html(url_ar)
        json_ar = extract_menu_data(html_ar)
        if json_ar:
            data_ar = process_menu_data(json_ar)
            log(f"Found {len(data_ar)} items in Arabic menu.")
            # Save raw JSON
            json_path = os.path.join(session_id, "menu_ar.json")
            with open(json_path, "w") as f:
                json.dump(json_ar, f, indent=2)
            st.session_state.json_paths['ar'] = json_path
        else:
            log("WARNING: Could not extract Arabic menu data.")
    except Exception as e:
        log(f"ERROR fetching Arabic URL: {e}")
        
    progress_bar.progress(60)
    
    # 3. Merge Data
    log("Merging Data...")
    df = merge_data(data_en, data_ar)
    st.dataframe(df.head())
    
    csv_path = os.path.join(session_id, "menu_data.csv")
    df.to_csv(csv_path, index=False)
    st.session_state.csv_path = csv_path
    
    progress_bar.progress(70)
    
    # 4. Download Images
    if download_images and not df.empty:
        log("Downloading Images (this may take a while)...")
        total_images = len(df)
        
        # Use 'originalImage' column
        if 'originalImage' in df.columns:
            downloaded_count = 0
            for i, row in df.iterrows():
                img_url = row['originalImage']
                if img_url and pd.notna(img_url):
                    # Use ID or Name for filename
                    prefix = f"{row.get('id', i)}_"
                    path = download_image(img_url, images_dir, filename_prefix=prefix)
                    if path:
                        downloaded_count += 1
                        # Log every 10 images to avoid spamming too much
                        if downloaded_count % 10 == 0:
                            log(f"Downloaded {downloaded_count}/{total_images} images...")
                
                # Update progress for images (mapped to 70-100 range)
                current_progress = 70 + int((i / total_images) * 30)
                progress_bar.progress(min(current_progress, 99))
            log(f"Finished downloading {downloaded_count} images.")
        else:
            log("WARNING: No image column found in data.")
    
    progress_bar.progress(100)
    log("Done! Ready for download.")
    
    # Create Zip
    if download_images:
        shutil.make_archive(os.path.join(session_id, "images"), 'zip', images_dir)
        st.session_state.zip_path = os.path.join(session_id, "images.zip")

    st.session_state.data_processed = True


if st.button("Start Scraping"):
    run_scraper()

# --- Display Downloads if Data Exists ---
if st.session_state.data_processed:
    st.subheader("Downloads")
    st.success(f"Data saved to: {st.session_state.session_id}")
    
    # CSV Download
    if st.session_state.csv_path and os.path.exists(st.session_state.csv_path):
        with open(st.session_state.csv_path, "rb") as f:
            st.download_button("Download CSV", f, file_name="menu_data.csv", mime="text/csv")
            
    # JSON Downloads
    if output_format in ["JSON", "Both"]:
        if 'en' in st.session_state.json_paths and os.path.exists(st.session_state.json_paths['en']):
            with open(st.session_state.json_paths['en'], "rb") as f:
                st.download_button("Download English JSON", f, file_name="menu_en.json", mime="application/json")
        if 'ar' in st.session_state.json_paths and os.path.exists(st.session_state.json_paths['ar']):
            with open(st.session_state.json_paths['ar'], "rb") as f:
                st.download_button("Download Arabic JSON", f, file_name="menu_ar.json", mime="application/json")

    # Images Zip
    if st.session_state.zip_path and os.path.exists(st.session_state.zip_path):
        with open(st.session_state.zip_path, "rb") as f:
            st.download_button("Download Images ZIP", f, file_name="images.zip", mime="application/zip")

