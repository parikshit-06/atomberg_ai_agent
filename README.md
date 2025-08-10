# Multi-Platform Share of Voice (SoV) Analyzer

This project is an **AI-powered multi-platform Share of Voice dashboard** that collects brand mentions and sentiment data from **Google Search**, **YouTube**, and optionally **Twitter** and visualizes the results in a **Streamlit app**.

---

## Features
- **Multi-platform data collection**:
  - Google Search (via SerpAPI or fallback scraper)
  - YouTube Data API
  - (Optional) Twitter scraping via `snscrape`
- **Sentiment analysis** using HuggingFace Transformers
- **Share of Voice calculation** with weighted frequency & sentiment
- ***Interactive dashboard** built with Streamlit
- Auto-saves results to CSV for further analysis

---

## Project Structure
```

.
├── sov\_agent\_multiplatform.py    # Main scraping & analysis agent
├── streamlit\_app.py              # Streamlit dashboard UI
├── requirements.txt              # Python dependencies
├── sov\_multi\_details.csv         # Detailed results (auto-generated)
├── sov\_multi\_summary.csv         # Overall SoV summary (auto-generated)
└── sov\_multi\_platform\_summary.csv# Per-platform SoV summary (auto-generated)

````

---

## Setup

### Clone the repo
```bash
git clone https://github.com/parikshit-06/atomberg_ai_agent
cd atomberg_ai_agent
````

### Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Add API keys

Create a `.env` file:

```env
SERPAPI_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_key
YOUTUBE_API_KEY=your_youtube_api_key
```

---

## Configuration

You can change:

* **Keywords** to track
* **Competitors** list
* Number of results per platform
  By editing the constants at the top of `sov_agent_multiplatform.py`.

---

## Output CSVs

* `sov_multi_summary.csv`: Overall brand SoV
* `sov_multi_platform_summary.csv`: Platform-wise SoV
* `sov_multi_details.csv`: Full data with mentions, sentiment, and engagement

---

## License

MIT License

---

## Credits

* [Streamlit](https://streamlit.io/)
* [HuggingFace Transformers](https://huggingface.co/)
* [SerpAPI](https://serpapi.com/)
* [YouTube Data API](https://developers.google.com/youtube/v3)
