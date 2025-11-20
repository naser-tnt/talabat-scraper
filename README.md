# Talabat Menu Scraper 

A Streamlit web application to scrape menu data from Talabat restaurant pages, supporting both English and Arabic menus, image downloading, and CSV/JSON export.

## Features
- **Dual Language Scraping**: Automatically fetches English and Arabic menus.
- **Data Merging**: Combines data into a single CSV with aligned columns.
- **Image Downloading**: Downloads item images with rate limiting.
- **Real-time Logging**: Terminal-style logs in the UI.
- **Persistent History**: Saves scraped data to timestamped folders (locally).

## Local Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd talabat_scraper
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app**:
    ```bash
    streamlit run app.py
    ```

## Deployment (Streamlit Cloud)

1.  **Push to GitHub**:
    -   Create a new repository on GitHub.
    -   Push your code:
        ```bash
        git init
        git add .
        git commit -m "Initial commit"
        git branch -M main
        git remote add origin <your-repo-url>
        git push -u origin main
        ```

2.  **Deploy**:
    -   Go to [share.streamlit.io](https://share.streamlit.io/).
    -   Connect your GitHub account.
    -   Select your repository (`talabat_scraper`) and main file (`app.py`).
    -   Click **Deploy**!

## Note on Cloud Storage
On Streamlit Cloud, the `scraped_data/` folder is **temporary**. It will be cleared when the app restarts. Please download your results (CSV/ZIP) immediately after scraping.
