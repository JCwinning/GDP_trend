# GDP Trend Dashboard

## Project Overview
This is an interactive Streamlit web application for visualizing and analyzing global economic data (GDP, Population, PPP, etc.). It aggregates data from the World Bank and IMF (via `download_data.py`) and allows users to:
1.  Visualize trends via interactive Plotly charts.
2.  Query the data using SQL (powered by DuckDB).
3.  Ask natural language questions which are converted to SQL by an AI model (ModelScope).

## Architecture
-   **Frontend:** Streamlit (`app.py`)
-   **Data Storage:** CSV files in `data/` loaded into an in-memory DuckDB instance.
-   **Data Source:** World Bank API (`wbgapi`) and IMF DataMapper API.
-   **AI Integration:** ModelScope API (via `openai` client) for NL-to-SQL and summarization.
-   **Visualization:** Plotly Express.

## Key Files
-   `app.py`: The main entry point for the Streamlit application. Handles UI, state management, and DuckDB integration.
-   `download_data.py`: Script to fetch the latest economic data from external APIs and save it to `data/`.
-   `language.py`: Handles internationalization (English/Chinese).
-   `requirements.txt`: Python dependencies.
-   `data/`: Directory storing the processed CSV datasets.
-   `.env`: Configuration file for API keys (not committed).

## Setup & Development

### Prerequisites
-   Python 3.8+
-   API Key from ModelScope (for AI features)

### Installation
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Configuration:**
    Create a `.env` file in the project root:
    ```env
    modelscope=your_api_key_here
    ```

3.  **Data Preparation:**
    If `data/` is empty or outdated, run:
    ```bash
    python download_data.py
    ```

### Running the Application
Start the Streamlit server:
```bash
streamlit run app.py
```
The app will be accessible at `http://localhost:8501`.

## Development Conventions
-   **State Management:** The app heavily relies on `st.session_state` to persist data (queries, AI results, user selections) across re-runs. Check the initialization block in `app.py`.
-   **Database:** The dataframe is registered as a virtual table `df_gdp` in DuckDB. All SQL queries should target this table.
-   **Internationalization:** Use `language.get_text(key)` for UI strings to support bilingual switching.
-   **Styling:** Custom CSS is injected via `st.markdown` in `app.py`.
