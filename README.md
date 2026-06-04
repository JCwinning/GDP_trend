[English](README.md) | [中文](_README_CN.md)

# GDP Trend Dashboard 🌍

An interactive web application for visualizing and analyzing economic data from the World Bank API. This dashboard allows users to explore GDP trends, population data, and economic indicators for countries worldwide with AI-powered analytics.

![Screenshot](images/0.png)

## AI writing SQL code

![Screenshot](images/1.png)

## AI writing summary for the data

![Screenshot](images/2.png)

## Live Demo

https://world-GDP-trend.streamlit.app/

## Features

- 📊 **Interactive Visualizations**: Explore GDP, GDP per capita, GDP PPP, and population trends over time
- 🗺️ **Global Coverage**: Data for 200+ countries including Taiwan with continent filtering
- 🔍 **SQL Query Interface**: Direct database querying with DuckDB integration
- 🤖 **AI-Powered Analytics**: Natural language to SQL conversion and data analysis using ModelScope API
- 📈 **Year-over-Year Growth**: Automatic calculation of GDP per capita growth rates
- 🌐 **Multilingual Support**: Full English and Chinese interface with country name translations
- 💾 **Data Persistence**: Session-based query result storage
- 🌏 **Multi-Source Data**: Integrated data from World Bank API and IMF DataMapper

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   
   ```bash
   git clone <repository-url>
   cd GDP_trend
   ```

2. **Install dependencies**
   
   ```bash
   pip install streamlit pandas plotly duckdb openai python-dotenv wbgapi pycountry
   ```

3. **Set up API key**
   
   Create a `.env` file in the project root:
   
   ```env
   modelscope=your_api_key_here
   ```
   
   Get your API key from [ModelScope](https://modelscope.cn).

4. **Download the data**
   
   ```bash
   python download_data.py
   ```
   
   This will download the latest economic data from the World Bank API and save it to the `data/` directory.

5. **Run the application**
   
   ```bash
   streamlit run app.py
   ```

The dashboard will open in your web browser at `http://localhost:8501`.

## Usage

### GDP Trend Visualization

1. Select countries from the dropdown (default: China, Japan, South Korea)
2. Choose an economic indicator:
   - GDP (Current USD)
   - GDP Per Capita (Current USD)
   - Total GDP PPP (Purchasing Power Parity)
   - GDP Per Capita PPP
   - Population Total
   - Inflation CPI, unemployment, trade shares, tax revenue, and sector value added
   - Big Mac Index vs USD
   - GDP Per Capita YoY Growth (%)
3. Adjust the year range using the slider
4. View interactive line charts and data tables

### SQL Query Interface

- Use the `df_gdp` table name in your SQL queries
- Examples:
  
  ```sql
  SELECT * FROM df_gdp WHERE country_code_3 = 'CHN' AND year >= 2020
  SELECT country_name, AVG(value) as avg_gdp FROM df_gdp WHERE indicator = 'gdp_per_capita_current_usd' AND year >= 2020 GROUP BY country_name ORDER BY avg_gdp DESC
  ```

### AI-Powered Data Chat

Ask questions in natural language:

- "What is the average GDP per capita for China, Japan, and Korea from 2020 to 2023?"
- "Which countries had the highest GDP growth in 2023?"
- "Show me population trends for Asian countries"

The AI will generate and execute SQL queries to answer your questions.

## Project Structure

```
GDP_trend/
├── app.py                          # Main Streamlit application
├── download_data.py               # Data download script (World Bank + IMF + Big Mac data)
├── language.py                     # Bilingual translation module
├── data/
│   ├── all_countries_with_iso_continents.csv  # Country metadata
│   └── gdp_data_2000_present.csv              # Economic indicators data
├── images/                         # Screenshot images for README
├── CLAUDE.md                       # Development guidance for Claude Code
├── README.md                       # This file (English)
├── _README_CN.md                   # Chinese version of README
├── favicon.svg                     # Application icon
├── requirements.txt                # Python dependencies
└── .env                           # Environment variables (create this)
```

## Data Sources

- **World Bank API**: Economic indicators for 200+ countries
  - GDP (current USD)
  - GDP per capita (current USD)
  - GDP PPP (current international $)
  - GDP per capita PPP (current international $)
  - Total population
  - Inflation CPI, unemployment, exports/imports as % of GDP, tax revenue as % of GDP
  - Manufacturing and services value added as % of GDP
- **IMF DataMapper API**: Economic data for Taiwan
  - GDP, GDP per capita, GDP PPP, GDP per capita PPP, population, inflation, and unemployment
- **The Economist Big Mac Data**: Big Mac index data from `TheEconomist/big-mac-data`
  - Annual latest observation of the raw USD Big Mac index, expressed as %
- **pycountry**: ISO country codes and names
- **Time Range**: 2000 to the latest available year by source
- **Update Frequency**: Manual via `download_data.py` script

## Available Indicators

- `gdp_current_usd`: GDP at market prices (current US$)
- `gdp_per_capita_current_usd`: GDP per capita (current US$)
- `gdp_ppp_current_intl`: GDP based on purchasing power parity (current international $)
- `gdp_per_capita_ppp_current_intl`: GDP per capita based on purchasing power parity (current international $)
- `population_total`: Total population
- `inflation_cpi_annual_pct`: Inflation, consumer prices (annual %)
- `unemployment_total_pct`: Unemployment, total (% of total labor force)
- `exports_goods_services_pct_gdp`: Exports of goods and services (% of GDP)
- `imports_goods_services_pct_gdp`: Imports of goods and services (% of GDP)
- `tax_revenue_pct_gdp`: Tax revenue (% of GDP)
- `manufacturing_value_added_pct_gdp`: Manufacturing value added (% of GDP)
- `services_value_added_pct_gdp`: Services value added (% of GDP)
- `big_mac_index_usd`: Big Mac raw index vs USD (% over/undervaluation)
- `gdp_per_capita_current_usd_yoy`: Year-over-year GDP per capita growth rate (%, calculated)

## API Integration

### World Bank API

- Accessed via the `wbgapi` Python package
- Rate limiting implemented with delays between requests
- Automatic error handling for missing data
- Covers 200+ countries and territories for World Bank indicators, with coverage varying by indicator

### IMF DataMapper API

- Direct REST API calls for Taiwan economic data
- Base URL: `https://www.imf.org/external/datamapper/api/v1`
- Provides GDP, GDP PPP, population, inflation, and unemployment data for Taiwan

### The Economist Big Mac Data

- Direct CSV download from `https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv`
- Keeps the latest Big Mac survey observation in each year for each country
- Stores the raw USD index as percentage over/undervaluation versus the US dollar

### ModelScope API

- Used for AI-powered SQL generation and data analysis
- Base URL: `https://api-inference.modelscope.cn/v1`
- Model: `ZhipuAI/GLM-4.6` for SQL generation and data summarization
- Supports bilingual output (English/Chinese)

**Data Sources**: World Bank, IMF DataMapper, The Economist Big Mac data
