import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from language import get_text

load_dotenv()
# Initialize session state for storing query results
if "sql_result" not in st.session_state:
    st.session_state.sql_result = None
if "sql_query" not in st.session_state:
    st.session_state.sql_query = "SELECT * FROM df_gdp LIMIT 10;"
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None
if "ai_query" not in st.session_state:
    st.session_state.ai_query = None
if "ai_raw_response" not in st.session_state:
    st.session_state.ai_raw_response = None
if "should_generate_ai_summary" not in st.session_state:
    st.session_state.should_generate_ai_summary = False
if "last_ai_summary" not in st.session_state:
    st.session_state.last_ai_summary = None
# Initialize language state
if "language" not in st.session_state:
    st.session_state.language = "en"
# Initialize session state with translated default question
if "user_question" not in st.session_state:
    st.session_state.user_question = get_text("default_question")
# Initialize tab selection state
if "tab_selection" not in st.session_state:
    st.session_state.tab_selection = "gdp_trend"
# Initialize GDP Trend selections state (will be set after data loading)
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = ["China", "Korea, Republic of", "Japan"]
if "selected_base_indicator" not in st.session_state:
    st.session_state.selected_base_indicator = "real GDP per capita"
if "selected_format" not in st.session_state:
    st.session_state.selected_format = "number"
if "selected_indicator" not in st.session_state:
    st.session_state.selected_indicator = "gdp_per_capita_constant_2015_usd"
if "selected_years" not in st.session_state:
    st.session_state.selected_years = (2000, 2024)  # Default, will be updated after data loads
# Set page configuration
st.set_page_config(
    page_title="GDP Trend Dashboard", layout="wide", page_icon="favicon.svg"
)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
    }
    .language-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title with language toggle button
col1, col2, col3 = st.columns([3, 0.5, 0.5])
with col1:
    st.title(get_text("title"))
with col3:
    st.markdown("<br>", unsafe_allow_html=True)  # Add space to lower the button
    current_lang = "中文" if st.session_state.language == "en" else "EN"
    if st.button(current_lang, help="Toggle language / 切换语言"):
        # Save current tab selection before changing language
        current_tab = st.session_state.get("tab_selection", "gdp_trend")
        st.session_state.language = "zh" if st.session_state.language == "en" else "en"
        # Restore tab selection after language change
        st.session_state.tab_selection = current_tab
        # Update the default question to match the new language
        st.session_state.user_question = get_text("default_question")
        st.rerun()


# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/gdp_data_2000_present.csv")
    return df


# Load country information
@st.cache_data
def load_country_info():
    df = pd.read_csv("data/all_countries_with_iso_continents.csv")
    return df


def get_table_schema(df):
    schema = pd.DataFrame(
        {"column_name": df.columns, "data_type": [str(dtype) for dtype in df.dtypes]}
    )
    return schema


def calculate_derived_indicators(df):
    """
    Calculate derived indicators like Real GDP Per Capita
    """
    pivot_df = df.pivot_table(
        index=['country_name', 'country_code_2', 'country_code_3', 'continent', 'year'], 
        columns='indicator', values='value').reset_index()
    
    derived_dfs = []
    
    if "gdp_constant_2015_usd" in pivot_df.columns and "population_total" in pivot_df.columns:
        temp_df = pivot_df.dropna(subset=['gdp_constant_2015_usd', 'population_total']).copy()
        temp_df['value'] = temp_df['gdp_constant_2015_usd'] / temp_df['population_total']
        temp_df['indicator'] = 'gdp_per_capita_constant_2015_usd'
        temp_df = temp_df[['country_name', 'country_code_2', 'country_code_3', 'continent', 'year', 'indicator', 'value']]
        derived_dfs.append(temp_df)

    if derived_dfs:
        res = pd.concat([df] + derived_dfs, ignore_index=True)
        return res
    return df


def calculate_yoy_gdp_growth(df):
    """
    Calculate year-over-year growth rates for all indicators dynamically
    """
    yoy_dfs = []

    indicators = df["indicator"].unique()
    for ind in indicators:
        if ind.endswith("_yoy"):
            continue

        source_df = df[df["indicator"] == ind].copy()
        if source_df.empty:
            continue

        # Sort by country and year to ensure proper calculation
        source_df = source_df.sort_values(["country_name", "year"])

        # Calculate year-over-year growth rate
        source_df["pct_change"] = (
            source_df.groupby("country_name")["value"].pct_change() * 100
        )

        # Create new indicator rows
        yoy_df = source_df.dropna(subset=["pct_change"]).copy()
        yoy_df["indicator"] = ind + "_yoy"
        yoy_df["value"] = yoy_df["pct_change"]
        yoy_df = yoy_df.drop(columns=["pct_change"])
        yoy_dfs.append(yoy_df)

    # Combine with original data
    if yoy_dfs:
        result_df = pd.concat([df] + yoy_dfs, ignore_index=True)
    else:
        result_df = df

    return result_df


def extract_sql_from_markdown(markdown_string):
    # First, try to find a fenced code block with 'sql'
    match = re.search(r"```sql(.*)```", markdown_string, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If not found, try to find any fenced code block
    match = re.search(r"```(.*)```", markdown_string, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no fenced code block is found, just strip the backticks
    return markdown_string.strip("`").strip()


def generate_ai_summary(result_df, sql_query):
    """
    Generate AI summary based on SQL query results in the selected language
    """
    if result_df is None or result_df.empty:
        return get_text("no_data_to_summarize")

    # Check for OpenAI API key
    api_key = os.getenv("modelscope")
    if not api_key:
        return get_text("ai_summary_unavailable")

    try:
        # Determine language for output
        output_language = "Chinese" if st.session_state.language == "zh" else "English"

        # Prepare data summary for AI with language specification
        summary_prompt = f"""You are a data analyst specializing in economic data analysis.

        Analyze the following SQL query results and provide a comprehensive summary.

        SQL Query that was executed:
        {sql_query}

        Query Results (first 500 rows):
        {result_df.head(500).to_string()}

        Data Summary:
        - Total rows: {len(result_df)}
        - Columns: {list(result_df.columns)}
        - Numeric columns summary:
        {result_df.describe(include=[np.number]).to_string()}

        Please provide a summary that includes:
        1. What the data shows
        2. Key insights or trends
        3. Any notable patterns or anomalies
       

        Keep the summary concise and insightful (100-200 words).
        Please output in {output_language}.
        """

        # Call OpenAI API
        client = OpenAI(
            api_key=api_key,
            base_url="https://api-inference.modelscope.cn/v1",
            #base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            #model="ZhipuAI/GLM-4.6",
            #model="Qwen/Qwen3-235B-A22B-Instruct-2507",
            model="deepseek-ai/DeepSeek-V3.2",
            #model="kwaipilot/kat-coder-pro:free",
            #model="MiniMax/MiniMax-M2",
            messages=[{"role": "user", "content": summary_prompt}],
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"AI summary generation error: {str(e)}"


try:
    # Load the data
    df_gdp = load_data()
    df_countries = load_country_info()

    # Calculate derived first, then YoY
    df_gdp = calculate_derived_indicators(df_gdp)
    df_gdp = calculate_yoy_gdp_growth(df_gdp)

    # Update session state with proper year range if not yet set or using defaults
    if st.session_state.selected_years == (2000, 2024):  # Still using default values
        min_year = int(df_gdp["year"].min())
        max_year = int(df_gdp["year"].max())
        st.session_state.selected_years = (min_year, max_year)

    # Create tabs using radio button for persistence
    tab_options = ["gdp_trend", "query"]
    # Ensure tab_selection is in session state
    if "tab_selection" not in st.session_state:
        st.session_state.tab_selection = "gdp_trend"
    selected_tab = st.radio(
        "",
        tab_options,
        format_func=get_text,
        horizontal=True,
        key="tab_selection",
        label_visibility="collapsed"
    )

    if selected_tab == "gdp_trend":
        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.header(get_text("filter_options"))

            # Country selection
            all_countries = df_gdp["country_name"].unique().tolist()
            selected_countries = st.multiselect(
                get_text("select_countries"), all_countries, key="selected_countries"
            )

            # Define Base Indicator mappings
            base_indicator_map = {
                "GDP": "gdp_current_usd",
                "real GDP": "gdp_constant_2015_usd",
                "PPP": "gdp_ppp_current_intl",
                "GDP per capita": "gdp_per_capita_current_usd",
                "real GDP per capita": "gdp_per_capita_constant_2015_usd",
                "PPP per capita": "gdp_per_capita_ppp_current_intl",
                "Population": "population_total"
            }
            base_options = list(base_indicator_map.keys())

            # Format options
            format_options = ["number", "growth"]

            col_ind, col_fmt = st.columns(2)
            with col_ind:
                current_base = st.session_state.get("selected_base_indicator", "real GDP per capita")
                current_base_idx = base_options.index(current_base) if current_base in base_options else 4
                selected_base = st.selectbox(
                    "Indicator",
                    base_options,
                    index=current_base_idx,
                )
                st.session_state.selected_base_indicator = selected_base

            with col_fmt:
                current_format = st.session_state.get("selected_format", "number")
                current_format_idx = format_options.index(current_format) if current_format in format_options else 0
                selected_format = st.selectbox(
                    "Format",
                    format_options,
                    index=current_format_idx,
                )
                st.session_state.selected_format = selected_format

            # Compute actual internal indicator code
            base_code = base_indicator_map[selected_base]
            if selected_format == "growth":
                selected_indicator = base_code + "_yoy"
                display_name = f"{selected_base} YoY Growth (%)"
            else:
                selected_indicator = base_code
                display_name = selected_base

            st.session_state.selected_indicator = selected_indicator

            # Year range selection
            min_year = int(df_gdp["year"].min())
            max_year = int(df_gdp["year"].max())
            selected_years = st.slider(
                get_text("select_year_range"),
                min_value=min_year,
                max_value=max_year,
                key="selected_years",
            )

        with right_col:
            # Filter data based on selections
            if selected_countries:
                filtered_df = df_gdp[
                    (df_gdp["country_name"].isin(selected_countries))
                    & (df_gdp["indicator"] == selected_indicator)
                    & (df_gdp["year"] >= selected_years[0])
                    & (df_gdp["year"] <= selected_years[1])
                ]
            else:
                filtered_df = df_gdp[
                    (df_gdp["indicator"] == selected_indicator)
                    & (df_gdp["year"] >= selected_years[0])
                    & (df_gdp["year"] <= selected_years[1])
                ]

            # Main panel
            if not filtered_df.empty:
                # Line chart
                st.subheader(
                    f"{display_name} Over Time"
                )

                # Dynamically create color map for selected countries to ensure distinct colors
                # Use a larger palette (Alphabet has 26 colors)
                color_scale = px.colors.qualitative.Alphabet
                # If more than 26 countries, we might cycle, but this is much better than 10
                current_color_map = {
                    country: color_scale[i % len(color_scale)]
                    for i, country in enumerate(sorted(selected_countries))
                }

                fig = px.line(
                    filtered_df,
                    x="year",
                    y="value",
                    color="country_name",
                    color_discrete_map=current_color_map,
                    title=f"{display_name} by Country",
                    labels={
                        "year": "Year",
                        "value": display_name,
                        "country_name": "Country",
                    },
                )

                fig.update_layout(
                    xaxis_title="Year",
                    yaxis_title=display_name,
                    legend_title="Country",
                    hovermode="x unified",
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display data table
                st.subheader(get_text("data_table"))
                # Sort by year descending before creating pivot table
                table_data = filtered_df[["country_name", "year", "value"]].sort_values(
                    "year", ascending=False
                )
                st.dataframe(
                    table_data.pivot(
                        index="year", columns="country_name", values="value"
                    )
                )

                # Display raw data
                if st.checkbox(get_text("show_raw_data")):
                    st.write(filtered_df)
            else:
                st.warning(get_text("no_data_warning"))

    if selected_tab == "query":
        ai_col, query_col = st.columns(2)

        with ai_col:
            st.subheader(get_text("ai_powered_chat"))
            st.markdown(get_text("ai_chat_description"))

            # Check for OpenAI API key
            api_key = os.getenv("modelscope")
            #api_key = os.getenv("openrouter")
            if not api_key:
                st.error(get_text("api_key_error"))
                st.markdown(get_text("api_key_instruction"))
                st.code("modelscope=your_api_key")
            else:
                # Use session state to store the user question
                user_question = st.text_area(
                    get_text("your_question"), st.session_state.user_question
                )

                # Update session state when text area changes
                st.session_state.user_question = user_question

                if st.button(get_text("run_ai"), key="run_ai"):
                    if user_question:
                        with st.status("🤔 Thinking...", expanded=True) as status:
                            try:
                                # Get table schema
                                st.write("📊 Analyzing your question...")
                                schema = get_table_schema(df_gdp)

                                # Create a prompt for the AI
                                indicators_list = df_gdp["indicator"].unique().tolist()
                                prompt = f"""You are a data analyst. Your task is to convert a natural language question into a SQL query.
                                You will be given a question, the schema of a pandas DataFrame named 'df_gdp', and the first 5 rows of the data.
                                Your response should be only the SQL query.

                                Here is the schema of the `df_gdp` table:
                                {schema.to_string(index=False)}

                                Here are the first 5 rows of the `df_gdp` table:
                                {df_gdp.head().to_string()}

                                The available indicators are: {indicators_list}
                                Please use one of these indicators in the SQL query if the question is about a specific indicator.
                                Please use ISO 3166-1 alpha-3 3 letter to select country everytime.its call "country_code_3" in our database.

                                Question: {user_question}

                                only return SQL Query:
                                """

                                # Call OpenAI API
                                st.write("🧠 Generating SQL query from your question...")
                                client = OpenAI(
                                    api_key=api_key,
                                    base_url="https://api-inference.modelscope.cn/v1",
                                    #base_url="https://openrouter.ai/api/v1",
                                )
                                response = client.chat.completions.create(
                                     #model="ZhipuAI/GLM-4.6",
                                     model="Qwen/Qwen3-235B-A22B-Instruct-2507",
                                    #model="MiniMax/MiniMax-M2",
                                    #model="deepseek-ai/DeepSeek-V3.2-Exp",
                                    #model="kwaipilot/kat-coder-pro:free",
                                    messages=[{"role": "user", "content": prompt}],
                                )

                                sql_query_raw = response.choices[0].message.content.strip()
                                sql_query = extract_sql_from_markdown(sql_query_raw)

                                # Store results in session state
                                st.session_state.ai_query = sql_query
                                st.session_state.ai_raw_response = sql_query_raw

                                # Execute the query
                                st.write("⚡ Executing query...")
                                result_df = duckdb.query(sql_query).to_df()
                                st.session_state.ai_result = result_df
                                st.session_state.should_generate_ai_summary = True
                                
                                status.update(label="✅ Complete!", state="complete", expanded=False)

                            except Exception as e:
                                st.error(f"An error occurred: {e}")
                                st.session_state.ai_result = None
                                st.session_state.should_generate_ai_summary = False
                                status.update(label="❌ Error occurred", state="error", expanded=False)
                    else:
                        st.warning(get_text("please_enter_question"))
                        st.session_state.should_generate_ai_summary = False

                # Display results from session state

                if st.session_state.ai_query is not None:
                    st.subheader(get_text("generated_sql"))
                    st.code(st.session_state.ai_query, language="sql")

                if st.session_state.ai_result is not None:
                    st.subheader(get_text("query_result"))
                    st.dataframe(st.session_state.ai_result)

                    # Add AI Summary section
                    if st.session_state.should_generate_ai_summary and st.session_state.ai_result is not None:
                        st.subheader(get_text("ai_summary"))
                        with st.spinner("Generating AI analysis..."):
                            ai_summary = generate_ai_summary(
                                st.session_state.ai_result, st.session_state.ai_query
                            )
                        st.info(ai_summary)
                        # Store the summary and reset flag after generating
                        st.session_state.last_ai_summary = ai_summary
                        st.session_state.should_generate_ai_summary = False
                    elif st.session_state.last_ai_summary is not None:
                        # Show existing summary without regenerating
                        st.subheader(get_text("ai_summary"))
                        st.info(st.session_state.last_ai_summary)

        with query_col:
            st.subheader(get_text("query_with_sql"))
            st.markdown("Use the table name `df_gdp` in your queries.")

            # Use session state to store the query
            query = st.text_area(get_text("sql_query"), st.session_state.sql_query)

            # Update session state when text area changes
            st.session_state.sql_query = query

            if st.button(get_text("run_query"), key="run_sql"):
                try:
                    result_df = duckdb.query(query).to_df()
                    st.session_state.sql_result = result_df
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.session_state.sql_result = None

            # Display result from session state
            if st.session_state.sql_result is not None:
                st.dataframe(st.session_state.sql_result)

except FileNotFoundError:
    st.error("Data files not found. Please run the data download script first.")
except Exception as e:
    st.error(f"An error occurred while loading the data: {str(e)}")

# Additional information
st.markdown("---")
st.info(f"""{get_text("data_source")}
{get_text("last_updated")}""")
