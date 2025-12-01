"""
Language translations for GDP Trend Dashboard
Supports English and Chinese languages
"""

translations = {
    "en": {
        "title": "🌍 GDP Trend Dashboard",
        "gdp_trend": "GDP Trend",
        "query": "Query",
        "filter_options": "Filter Options",
        "select_countries": "Select Countries:",
        "select_indicator": "Select Indicator:",
        "select_year_range": "Select Year Range:",
        "data_table": "Data Table",
        "show_raw_data": "Show Raw Data",
        "no_data_warning": "No data available for the selected filters. Please adjust your selections.",
        "ai_powered_chat": "AI-Powered Data Chat",
        "ai_chat_description": "Ask a question about the GDP data, and the AI will generate a SQL query to answer it.",
        "your_question": "Your Question:",
        "run_ai": "Run AI",
        "generated_sql": "Generated SQL Query",
        "query_result": "Query Result",
        "ai_summary": "AI Summary",
        "query_with_sql": "Query GDP Data with SQL",
        "sql_query": "SQL Query",
        "run_query": "Run Query",
        "data_source": "Data Source: World Bank",
        "last_updated": "Last Updated: 2024",
        "default_question": "What is the average GDP per capita for each: China, Japan, and Korea during 2020 to 2023?",
        "api_key_error": "API key from 'modelscope' environment variable not found.",
        "api_key_instruction": "Please make sure you have a `.env` file in your project directory with the following content:",
        "please_enter_question": "Please enter a question.",
        "no_data_to_summarize": "No data available to summarize.",
        "ai_summary_unavailable": "AI summary unavailable: API key not found."
    },
    "zh": {
        "title": "🌍 GDP趋势仪表板",
        "gdp_trend": "GDP趋势",
        "query": "查询",
        "filter_options": "筛选选项",
        "select_countries": "选择国家:",
        "select_indicator": "选择指标:",
        "select_year_range": "选择年份范围:",
        "data_table": "数据表",
        "show_raw_data": "显示原始数据",
        "no_data_warning": "所选筛选条件无可用数据。请调整您的选择。",
        "ai_powered_chat": "AI数据对话",
        "ai_chat_description": "询问关于GDP数据的问题，AI将生成SQL查询来回答。",
        "your_question": "您的问题:",
        "run_ai": "运行AI",
        "generated_sql": "生成的SQL查询",
        "query_result": "查询结果",
        "ai_summary": "AI摘要",
        "query_with_sql": "使用SQL查询GDP数据",
        "sql_query": "SQL查询",
        "run_query": "运行查询",
        "data_source": "数据来源：世界银行",
        "last_updated": "最后更新：2024",
        "default_question": "2020到2024年，中国，泰国人均GDP",
        "api_key_error": "未找到'modelscope'环境变量的API密钥。",
        "api_key_instruction": "请确保您的项目目录中有`.env`文件，内容如下：",
        "please_enter_question": "请输入问题。",
        "no_data_to_summarize": "没有可用的数据进行总结。",
        "ai_summary_unavailable": "AI摘要不可用：未找到API密钥。"
    }
}


def get_text(key):
    """
    Get translated text for the given key using current session language.

    Args:
        key (str): Translation key

    Returns:
        str: Translated text
    """
    import streamlit as st
    language = st.session_state.get("language", "en")
    return translations.get(language, {}).get(key, key)