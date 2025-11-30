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
        st.session_state.language = "zh" if st.session_state.language == "en" else "en"
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


def calculate_yoy_gdp_growth(df):
    """
    Calculate year-over-year GDP per capita growth rate for each country
    Returns DataFrame with new indicator 'gdp_per_capita_current_usd_yoy'
    """
    # Filter for GDP per capita data
    gdp_per_capita_df = df[df["indicator"] == "gdp_per_capita_current_usd"].copy()

    if gdp_per_capita_df.empty:
        return df

    # Sort by country and year to ensure proper calculation
    gdp_per_capita_df = gdp_per_capita_df.sort_values(["country_name", "year"])

    # Calculate year-over-year growth rate
    gdp_per_capita_df["pct_change"] = (
        gdp_per_capita_df.groupby("country_name")["value"].pct_change() * 100
    )

    # Create new indicator rows
    yoy_growth_df = gdp_per_capita_df.dropna(subset=["pct_change"]).copy()
    yoy_growth_df["indicator"] = "gdp_per_capita_current_usd_yoy"
    yoy_growth_df["value"] = yoy_growth_df["pct_change"]
    yoy_growth_df = yoy_growth_df.drop(columns=["pct_change"])

    # Combine with original data
    result_df = pd.concat([df, yoy_growth_df], ignore_index=True)

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
            model="deepseek-ai/DeepSeek-V3.2-Exp",
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

    # Calculate YoY GDP growth
    df_gdp = calculate_yoy_gdp_growth(df_gdp)

    # Create a consistent color map for all countries
    all_countries_list = sorted(df_gdp["country_name"].unique())
    color_scale = px.colors.qualitative.Plotly
    color_map = {
        country: color_scale[i % len(color_scale)]
        for i, country in enumerate(all_countries_list)
    }

    # Create indicator display name mapping
    indicator_display_names = {
        "gdp_current_usd": "GDP (Current USD)",
        "gdp_per_capita_current_usd": "GDP Per Capita (Current USD)",
        "population_total": "Population Total",
        "gdp_ppp_current_intl": "Total GDP PPP",
        "gdp_per_capita_ppp_current_intl": "GDP Per Capita PPP",
        "gdp_per_capita_current_usd_yoy": "GDP Per Capita YoY Growth (%)",
    }

    # Create tabs using radio button for persistence
    tab_options = ["gdp_trend", "query"]
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
            default_countries = ["China", "Korea, Republic of", "Japan"]
            selected_countries = st.multiselect(
                get_text("select_countries"), all_countries, default=default_countries
            )

            # Indicator selection
            indicators = df_gdp["indicator"].unique().tolist()
            # Create display options with friendly names
            indicator_options = [
                indicator_display_names.get(ind, ind.replace("_", " ").title())
                for ind in indicators
            ]
            # Get default index
            default_index = (
                indicators.index("gdp_per_capita_ppp_current_intl")
                if "gdp_per_capita_ppp_current_intl" in indicators
                else 0
            )
            # Display selection with friendly names
            selected_display_name = st.selectbox(
                get_text("select_indicator"),
                indicator_options,
                index=default_index,
            )
            # Map back to technical name for filtering
            selected_indicator = indicators[indicator_options.index(selected_display_name)]

            # Year range selection
            min_year = int(df_gdp["year"].min())
            max_year = int(df_gdp["year"].max())
            selected_years = st.slider(
                get_text("select_year_range"),
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
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
                    f"{selected_indicator.replace('_', ' ').title()} Over Time"
                )

                fig = px.line(
                    filtered_df,
                    x="year",
                    y="value",
                    color="country_name",
                    color_discrete_map=color_map,
                    title=f"{selected_indicator.replace('_', ' ').title()} by Country",
                    labels={
                        "year": "Year",
                        "value": selected_indicator.replace("_", " ").title(),
                        "country_name": "Country",
                    },
                )

                fig.update_layout(
                    xaxis_title="Year",
                    yaxis_title=selected_indicator.replace("_", " ").title(),
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
