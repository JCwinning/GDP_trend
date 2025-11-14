# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This GDP Trend Dashboard project downloads and visualizes economic data from the World Bank API. It consists of two main components:

1. **Data Pipeline** (`download_data.py`): Python script that downloads GDP, GDP per capita, and population data for all countries from 2000-present
2. **Interactive Dashboard** (`app.py`): Streamlit web application for exploring and querying the downloaded economic data
3. **Language Module** (`language.py`): Centralized translation system supporting English and Chinese interfaces

## Key Architecture

### Data Flow
1. **Data Collection**: World Bank API → `wbgapi` Python package → CSV files in `data/` directory
2. **Data Storage**: Two main CSV files:
   - `all_countries_with_iso_continents.csv`: Country metadata (ISO codes, continents, Chinese names)
   - `gdp_data_2000_present.csv`: Economic indicators in long format (country, year, indicator, value)
3. **Data Visualization**: Streamlit reads CSV → DuckDB SQL queries → Plotly charts

### Data Schema
- **Main GDP Table** (`gdp_data_2000_present.csv`):
  - Columns: `country_name`, `country_code_2`, `country_code_3`, `continent`, `year`, `indicator`, `value`
  - Indicators: `gdp_current_usd`, `gdp_per_capita_current_usd`, `population_total`, `gdp_per_capita_current_usd_yoy`
- **Country Reference**: ISO codes, continents, and multilingual country names

### Dashboard Features
- **Trend Visualization**: Interactive line charts with country filtering and consistent color mapping
- **SQL Query Interface**: Direct database querying with DuckDB integration
- **AI-Powered Analytics**: Natural language to SQL conversion using ModelScope API with cached summaries
- **Session Management**: Persistent query results, AI summaries, and user inputs across interactions
- **Bilingual Interface**: Complete English/Chinese language toggle functionality

## Development Commands

### Running the Application
```bash
# Start the Streamlit dashboard
streamlit run app.py
```

### Data Management
```bash
# Download fresh data from World Bank API
python download_data.py
```

### Dependencies
```bash
# Install required packages
pip install streamlit pandas plotly duckdb openai python-dotenv wbgapi pycountry quarto
```

**Key Dependencies:**
- `streamlit`: Web application framework
- `pandas`: Data manipulation and analysis
- `plotly`: Interactive visualizations
- `duckdb`: SQL database engine for querying
- `openai`: API client for ModelScope integration
- `wbgapi`: World Bank API client
- `pycountry`: Country code mappings

## Configuration

### Environment Variables
Create a `.env` file with:
```
modelscope=your_api_key_here
```

### API Integration
- **World Bank API**: Used via `wbgapi` package for data downloads
- **ModelScope API**: Used for AI-powered SQL generation and data analysis
  - Base URL: `https://api-inference.modelscope.cn/v1`
  - Models: `ZhipuAI/GLM-4.6` for both SQL generation and AI summary generation
  - SQL generation uses schema-aware prompts with country code requirements

## Important Notes

- **API Rate Limits**: The data download script includes delays to respect World Bank API limits
- **Data Processing**: YoY GDP growth is calculated dynamically in the Streamlit app using pandas `pct_change()`
- **Session State**: The dashboard maintains query results, AI summaries, and user inputs across interactions using multiple session state variables
- **Error Handling**: Graceful degradation when data files are missing or API keys are unavailable
- **Internationalization**: Country names include Chinese translations for broader accessibility
- **Language System**: Centralized in `language.py` module with dynamic language switching based on session state
- **AI Summary Behavior**: AI summaries are cached and persist across different dashboard actions, only regenerating when new AI queries are executed
- **Language-Aware AI**: AI summaries and SQL generation responses match selected interface language (English/Chinese)