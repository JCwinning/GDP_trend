#!/usr/bin/env python3
"""
GDP Data Downloader
================

This script downloads economic data from the World Bank API for all countries
from 2000-present and saves it to CSV files for use in the GDP Trend Dashboard.

Author: Tony D
"""

import pycountry
import pandas as pd
import wbgapi as wb
import time
import os
import requests
import json

# Countries to exclude from download (no data available in World Bank API)
EXCLUDE_COUNTRIES = [
    "Anguilla",
    "Åland Islands",
    "Antarctica",
    "French Southern Territories",
    "Bonaire, Sint Eustatius and Saba",
    "Bahamas",
    "Saint Barthélemy",
    "Bouvet Island",
    "Cocos (Keeling) Islands",
    "Cook Islands",
    "Christmas Island",
    "Western Sahara",
    "Falkland Islands (Malvinas)",
    "Guernsey",
    "Guadeloupe",
    "French Guiana",
    "Heard Island and McDonald Islands",
    "British Indian Ocean Territory",
    "Jersey",
    "Montserrat",
    "Martinique",
    "Mayotte",
    "Norfolk Island",
    "Niue",
    "Pitcairn",
    "Réunion",
    "South Georgia and the South Sandwich Islands",
    "Saint Helena, Ascension and Tristan da Cunha",
    "Svalbard and Jan Mayen",
    "Saint Pierre and Miquelon",
    "Tokelau",
    "Taiwan, Province of China",
    "United States Minor Outlying Islands",
    "Holy See (Vatican City State)",
    "Wallis and Futuna",
]


def create_country_reference_table():
    """
    Create a comprehensive country reference table with ISO codes, continents,
    and Chinese names.

    Returns:
        pd.DataFrame: Country metadata with ISO codes, continents, and translations
    """
    print("Creating country reference table...")

    # Get all countries from pycountry
    countries = list(pycountry.countries)

    # Create dataframe with country information
    df_all = pd.DataFrame(
        [
            {
                "country_name": country.name,
                "country_code_2": country.alpha_2,
                "country_code_3": country.alpha_3,
            }
            for country in countries
        ]
    )

    # Predefined ISO Alpha-2 to continent mapping
    iso_to_continent = {
        "AF": "Asia",
        "AX": "Europe",
        "AL": "Europe",
        "DZ": "Africa",
        "AS": "Oceania",
        "AD": "Europe",
        "AO": "Africa",
        "AI": "North America",
        "AQ": "Antarctica",
        "AG": "North America",
        "AR": "South America",
        "AM": "Asia",
        "AW": "North America",
        "AU": "Oceania",
        "AT": "Europe",
        "AZ": "Asia",
        "BS": "North America",
        "BH": "Asia",
        "BD": "Asia",
        "BB": "North America",
        "BY": "Europe",
        "BE": "Europe",
        "BZ": "North America",
        "BJ": "Africa",
        "BM": "North America",
        "BT": "Asia",
        "BO": "South America",
        "BQ": "North America",
        "BA": "Europe",
        "BW": "Africa",
        "BV": "Antarctica",
        "BR": "South America",
        "IO": "Asia",
        "BN": "Asia",
        "BG": "Europe",
        "BF": "Africa",
        "BI": "Africa",
        "KH": "Asia",
        "CM": "Africa",
        "CA": "North America",
        "CV": "Africa",
        "KY": "North America",
        "CF": "Africa",
        "TD": "Africa",
        "CL": "South America",
        "CN": "Asia",
        "CX": "Asia",
        "CC": "Asia",
        "CO": "South America",
        "KM": "Africa",
        "CD": "Africa",
        "CG": "Africa",
        "CK": "Oceania",
        "CR": "North America",
        "CI": "Africa",
        "HR": "Europe",
        "CU": "North America",
        "CW": "North America",
        "CY": "Asia",
        "CZ": "Europe",
        "DK": "Europe",
        "DJ": "Africa",
        "DM": "North America",
        "DO": "North America",
        "EC": "South America",
        "EG": "Africa",
        "SV": "North America",
        "GQ": "Africa",
        "ER": "Africa",
        "EE": "Europe",
        "SZ": "Africa",
        "ET": "Africa",
        "FK": "South America",
        "FO": "Europe",
        "FJ": "Oceania",
        "FI": "Europe",
        "FR": "Europe",
        "GF": "South America",
        "PF": "Oceania",
        "TF": "Antarctica",
        "GA": "Africa",
        "GM": "Africa",
        "GE": "Asia",
        "DE": "Europe",
        "GH": "Africa",
        "GI": "Europe",
        "GR": "Europe",
        "GL": "North America",
        "GD": "North America",
        "GP": "North America",
        "GU": "Oceania",
        "GT": "North America",
        "GG": "Europe",
        "GN": "Africa",
        "GW": "Africa",
        "GY": "South America",
        "HT": "North America",
        "HM": "Antarctica",
        "VA": "Europe",
        "HN": "North America",
        "HK": "Asia",
        "HU": "Europe",
        "IS": "Europe",
        "IN": "Asia",
        "ID": "Asia",
        "IR": "Asia",
        "IQ": "Asia",
        "IE": "Europe",
        "IM": "Europe",
        "IL": "Asia",
        "IT": "Europe",
        "JM": "North America",
        "JP": "Asia",
        "JE": "Europe",
        "JO": "Asia",
        "KZ": "Asia",
        "KE": "Africa",
        "KI": "Oceania",
        "KP": "Asia",
        "KR": "Asia",
        "KW": "Asia",
        "KG": "Asia",
        "LA": "Asia",
        "LV": "Europe",
        "LB": "Asia",
        "LS": "Africa",
        "LR": "Africa",
        "LY": "Africa",
        "LI": "Europe",
        "LT": "Europe",
        "LU": "Europe",
        "MO": "Asia",
        "MG": "Africa",
        "MW": "Africa",
        "MY": "Asia",
        "MV": "Asia",
        "ML": "Africa",
        "MT": "Europe",
        "MH": "Oceania",
        "MQ": "North America",
        "MR": "Africa",
        "MU": "Africa",
        "YT": "Africa",
        "MX": "North America",
        "FM": "Oceania",
        "MD": "Europe",
        "MC": "Europe",
        "MN": "Asia",
        "ME": "Europe",
        "MS": "North America",
        "MA": "Africa",
        "MZ": "Africa",
        "MM": "Asia",
        "NA": "Africa",
        "NR": "Oceania",
        "NP": "Asia",
        "NL": "Europe",
        "NC": "Oceania",
        "NZ": "Oceania",
        "NI": "North America",
        "NE": "Africa",
        "NG": "Africa",
        "NU": "Oceania",
        "NF": "Oceania",
        "MK": "Europe",
        "MP": "Oceania",
        "NO": "Europe",
        "OM": "Asia",
        "PK": "Asia",
        "PW": "Oceania",
        "PS": "Asia",
        "PA": "North America",
        "PG": "Oceania",
        "PY": "South America",
        "PE": "South America",
        "PH": "Asia",
        "PN": "Oceania",
        "PL": "Europe",
        "PT": "Europe",
        "PR": "North America",
        "QA": "Asia",
        "RE": "Africa",
        "RO": "Europe",
        "RU": "Europe",
        "RW": "Africa",
        "BL": "North America",
        "SH": "Africa",
        "KN": "North America",
        "LC": "North America",
        "MF": "North America",
        "PM": "North America",
        "VC": "North America",
        "WS": "Oceania",
        "SM": "Europe",
        "ST": "Africa",
        "SA": "Asia",
        "SN": "Africa",
        "RS": "Europe",
        "SC": "Africa",
        "SL": "Africa",
        "SG": "Asia",
        "SX": "North America",
        "SK": "Europe",
        "SI": "Europe",
        "SB": "Oceania",
        "SO": "Africa",
        "ZA": "Africa",
        "GS": "Antarctica",
        "SS": "Africa",
        "ES": "Europe",
        "LK": "Asia",
        "SD": "Africa",
        "SR": "South America",
        "SJ": "Europe",
        "SE": "Europe",
        "CH": "Europe",
        "SY": "Asia",
        "TW": "Asia",
        "TJ": "Asia",
        "TZ": "Africa",
        "TH": "Asia",
        "TL": "Asia",
        "TG": "Africa",
        "TK": "Oceania",
        "TO": "Oceania",
        "TT": "North America",
        "TN": "Africa",
        "TR": "Asia",
        "TM": "Asia",
        "TC": "North America",
        "TV": "Oceania",
        "UG": "Africa",
        "UA": "Europe",
        "AE": "Asia",
        "GB": "Europe",
        "US": "North America",
        "UM": "Oceania",
        "UY": "South America",
        "UZ": "Asia",
        "VU": "Oceania",
        "VE": "South America",
        "VN": "Asia",
        "VG": "North America",
        "VI": "North America",
        "WF": "Oceania",
        "EH": "Africa",
        "YE": "Asia",
        "ZM": "Africa",
        "ZW": "Africa",
    }

    # Apply continent mapping to dataframe
    df_all["continent"] = df_all["country_code_2"].map(iso_to_continent)

    # Add Chinese country names for bilingual support
    english_to_chinese = {
        "Afghanistan": "阿富汗",
        "Albania": "阿尔巴尼亚",
        "Algeria": "阿尔及利亚",
        "American Samoa": "美属萨摩亚",
        "Andorra": "安道尔",
        "Angola": "安哥拉",
        "Anguilla": "安圭拉",
        "Antarctica": "南极洲",
        "Antigua and Barbuda": "安提瓜和巴布达",
        "Argentina": "阿根廷",
        "Armenia": "亚美尼亚",
        "Aruba": "阿鲁巴",
        "Australia": "澳大利亚",
        "Austria": "奥地利",
        "Azerbaijan": "阿塞拜疆",
        "Bahamas": "巴哈马",
        "Bahrain": "巴林",
        "Bangladesh": "孟加拉国",
        "Barbados": "巴巴多斯",
        "Belarus": "白俄罗斯",
        "Belgium": "比利时",
        "Belize": "伯利兹",
        "Benin": "贝宁",
        "Bermuda": "百慕大",
        "Bhutan": "不丹",
        "Bolivia, Plurinational State of": "玻利维亚多民族国",
        "Bonaire, Sint Eustatius and Saba": "博内尔、圣尤斯特歇斯和萨巴",
        "Bosnia and Herzegovina": "波斯尼亚和黑塞哥维那",
        "Botswana": "博茨瓦纳",
        "Bouvet Island": "布韦岛",
        "Brazil": "巴西",
        "British Indian Ocean Territory": "英属印度洋领地",
        "Brunei Darussalam": "文莱达鲁萨兰国",
        "Bulgaria": "保加利亚",
        "Burkina Faso": "布基纳法索",
        "Burundi": "布隆迪",
        "Cambodia": "柬埔寨",
        "Cameroon": "喀麦隆",
        "Canada": "加拿大",
        "Cape Verde": "佛得角",
        "Cayman Islands": "开曼群岛",
        "Central African Republic": "中非共和国",
        "Chad": "乍得",
        "Chile": "智利",
        "China": "中国",
        "Christmas Island": "圣诞岛",
        "Cocos (Keeling) Islands": "科科斯（基林）群岛",
        "Colombia": "哥伦比亚",
        "Comoros": "科摩罗",
        "Congo": "刚果",
        "Congo, The Democratic Republic of the": "刚果民主共和国",
        "Cook Islands": "库克群岛",
        "Costa Rica": "哥斯达黎加",
        "Croatia": "克罗地亚",
        "Cuba": "古巴",
        "Curaçao": "库拉索",
        "Cyprus": "塞浦路斯",
        "Czechia": "捷克",
        "Côte d'Ivoire": "科特迪瓦",
        "Denmark": "丹麦",
        "Djibouti": "吉布提",
        "Dominica": "多米尼克",
        "Dominican Republic": "多米尼加共和国",
        "Ecuador": "厄瓜多尔",
        "Egypt": "埃及",
        "El Salvador": "萨尔瓦多",
        "Equatorial Guinea": "赤道几内亚",
        "Eritrea": "厄立特里亚",
        "Estonia": "爱沙尼亚",
        "Eswatini": "斯威士兰",
        "Ethiopia": "埃塞俄比亚",
        "Falkland Islands (Malvinas)": "福克兰群岛（马尔维纳斯）",
        "Faroe Islands": "法罗群岛",
        "Fiji": "斐济",
        "Finland": "芬兰",
        "France": "法国",
        "French Guiana": "法属圭亚那",
        "French Polynesia": "法属波利尼西亚",
        "French Southern Territories": "法国南部领土",
        "Gabon": "加蓬",
        "Gambia": "冈比亚",
        "Georgia": "格鲁吉亚",
        "Germany": "德国",
        "Ghana": "加纳",
        "Gibraltar": "直布罗陀",
        "Greece": "希腊",
        "Greenland": "格陵兰",
        "Grenada": "格林纳达",
        "Guadeloupe": "瓜德罗普",
        "Guam": "关岛",
        "Guatemala": "危地马拉",
        "Guernsey": "根西岛",
        "Guinea": "几内亚",
        "Guinea-Bissau": "几内亚比绍",
        "Guyana": "圭亚那",
        "Haiti": "海地",
        "Heard Island and McDonald Islands": "赫德岛和麦克唐纳群岛",
        "Holy See (Vatican City State)": "教廷（梵蒂冈城国）",
        "Honduras": "洪都拉斯",
        "Hong Kong": "香港",
        "Hungary": "匈牙利",
        "Iceland": "冰岛",
        "India": "印度",
        "Indonesia": "印度尼西亚",
        "Iran, Islamic Republic of": "伊朗伊斯兰共和国",
        "Iraq": "伊拉克",
        "Ireland": "爱尔兰",
        "Isle of Man": "马恩岛",
        "Israel": "以色列",
        "Italy": "意大利",
        "Jamaica": "牙买加",
        "Japan": "日本",
        "Jersey": "泽西岛",
        "Jordan": "约旦",
        "Kazakhstan": "哈萨克斯坦",
        "Kenya": "肯尼亚",
        "Kiribati": "基里巴斯",
        "Korea, Democratic People's Republic of": "朝鲜民主主义人民共和国",
        "Korea, Republic of": "韩国",
        "Kuwait": "科威特",
        "Kyrgyzstan": "吉尔吉斯斯坦",
        "Lao People's Democratic Republic": "老挝人民民主共和国",
        "Latvia": "拉脱维亚",
        "Lebanon": "黎巴嫩",
        "Lesotho": "莱索托",
        "Liberia": "利比里亚",
        "Libya": "利比亚",
        "Liechtenstein": "列支敦士登",
        "Lithuania": "立陶宛",
        "Luxembourg": "卢森堡",
        "Macao": "澳门",
        "Madagascar": "马达加斯加",
        "Malawi": "马拉维",
        "Malaysia": "马来西亚",
        "Maldives": "马尔代夫",
        "Mali": "马里",
        "Malta": "马耳他",
        "Marshall Islands": "马绍尔群岛",
        "Martinique": "马提尼克",
        "Mauritania": "毛里塔尼亚",
        "Mauritius": "毛里求斯",
        "Mayotte": "马约特",
        "Mexico": "墨西哥",
        "Micronesia, Federated States of": "密克罗尼西亚联邦",
        "Moldova, Republic of": "摩尔多瓦共和国",
        "Monaco": "摩纳哥",
        "Mongolia": "蒙古",
        "Montenegro": "黑山",
        "Montserrat": "蒙特塞拉特",
        "Morocco": "摩洛哥",
        "Mozambique": "莫桑比克",
        "Myanmar": "缅甸",
        "Namibia": "纳米比亚",
        "Nauru": "瑙鲁",
        "Nepal": "尼泊尔",
        "Netherlands": "荷兰",
        "New Caledonia": "新喀里多尼亚",
        "New Zealand": "新西兰",
        "Nicaragua": "尼加拉瓜",
        "Niger": "尼日尔",
        "Nigeria": "尼日利亚",
        "Niue": "纽埃",
        "Norfolk Island": "诺福克岛",
        "North Macedonia": "北马其顿",
        "Northern Mariana Islands": "北马里亚纳群岛",
        "Norway": "挪威",
        "Oman": "阿曼",
        "Pakistan": "巴基斯坦",
        "Palau": "帕劳",
        "Palestine, State of": "巴勒斯坦国",
        "Panama": "巴拿马",
        "Papua New Guinea": "巴布亚新几内亚",
        "Paraguay": "巴拉圭",
        "Peru": "秘鲁",
        "Philippines": "菲律宾",
        "Pitcairn": "皮特凯恩",
        "Poland": "波兰",
        "Portugal": "葡萄牙",
        "Puerto Rico": "波多黎各",
        "Qatar": "卡塔尔",
        "Romania": "罗马尼亚",
        "Russian Federation": "俄罗斯联邦",
        "Rwanda": "卢旺达",
        "Réunion": "留尼汪",
        "Saint Barthélemy": "圣巴泰勒米",
        "Saint Helena, Ascension and Tristan da Cunha": "圣赫勒拿、阿森松和特里斯坦达库尼亚",
        "Saint Kitts and Nevis": "圣基茨和尼维斯",
        "Saint Lucia": "圣卢西亚",
        "Saint Martin (French part)": "圣马丁（法属）",
        "Saint Pierre and Miquelon": "圣皮埃尔和密克隆",
        "Saint Vincent and the Grenadines": "圣文森特和格林纳丁斯",
        "Samoa": "萨摩亚",
        "San Marino": "圣马力诺",
        "Sao Tome and Principe": "圣多美和普林西比",
        "Saudi Arabia": "沙特阿拉伯",
        "Senegal": "塞内加尔",
        "Serbia": "塞尔维亚",
        "Seychelles": "塞舌尔",
        "Sierra Leone": "塞拉利昂",
        "Singapore": "新加坡",
        "Sint Maarten (Dutch part)": "圣马丁（荷属）",
        "Slovakia": "斯洛伐克",
        "Slovenia": "斯洛文尼亚",
        "Solomon Islands": "所罗门群岛",
        "Somalia": "索马里",
        "South Africa": "南非",
        "South Georgia and the South Sandwich Islands": "南乔治亚岛和南桑威奇群岛",
        "South Sudan": "南苏丹",
        "Spain": "西班牙",
        "Sri Lanka": "斯里兰卡",
        "Sudan": "苏丹",
        "Suriname": "苏里南",
        "Svalbard and Jan Mayen": "斯瓦尔巴和扬马延",
        "Sweden": "瑞典",
        "Switzerland": "瑞士",
        "Syrian Arab Republic": "阿拉伯叙利亚共和国",
        "Taiwan, Province of China": "中国台湾省",
        "Tajikistan": "塔吉克斯坦",
        "Tanzania, United Republic of": "坦桑尼亚联合共和国",
        "Thailand": "泰国",
        "Timor-Leste": "东帝汶",
        "Togo": "多哥",
        "Tokelau": "托克劳",
        "Tonga": "汤加",
        "Trinidad and Tobago": "特立尼达和多巴哥",
        "Tunisia": "突尼斯",
        "Turkey": "土耳其",
        "Turkmenistan": "土库曼斯坦",
        "Turks and Caicos Islands": "特克斯和凯科斯群岛",
        "Tuvalu": "图瓦卢",
        "Uganda": "乌干达",
        "Ukraine": "乌克兰",
        "United Arab Emirates": "阿联酋",
        "United Kingdom": "英国",
        "United States": "美国",
        "United States Minor Outlying Islands": "美国本土外小岛屿",
        "Uruguay": "乌拉圭",
        "Uzbekistan": "乌兹别克斯坦",
        "Vanuatu": "瓦努阿图",
        "Venezuela, Bolivarian Republic of": "委内瑞拉玻利瓦尔共和国",
        "Viet Nam": "越南",
        "Virgin Islands, British": "英属维尔京群岛",
        "Virgin Islands, U.S.": "美属维尔京群岛",
        "Wallis and Futuna": "瓦利斯和富图纳",
        "Western Sahara": "西撒哈拉",
        "Yemen": "也门",
        "Zambia": "赞比亚",
        "Zimbabwe": "津巴布韦",
        "Åland Islands": "奥兰群岛",
    }

    # Add Chinese names to dataframe
    df_all["country_name_cn"] = df_all["country_name"].map(english_to_chinese)

    # For countries without Chinese translations, keep the English name
    df_all["country_name_cn"] = df_all["country_name_cn"].fillna(df_all["country_name"])

    return df_all


def download_taiwan_data_from_imf():
    """
    Download Taiwan economic data from IMF DataMapper API.

    Returns:
        pd.DataFrame: Economic data for Taiwan from IMF
    """
    print("Downloading Taiwan data from IMF API...")

    # IMF indicators mapping
    imf_indicators = {
        "NGDPD": "gdp_current_usd",  # GDP (current US$)
        "NGDPDPC": "gdp_per_capita_current_usd",  # GDP per capita (current US$)
        "LP": "population_total",  # Population (millions, need to convert)
        "PPPGDP": "gdp_ppp_current_intl",  # GDP, PPP (current international $)
        "PPPPC": "gdp_per_capita_ppp_current_intl",  # GDP per capita, PPP (current international $)
    }

    taiwan_data = []
    start_year = 2000
    end_year = 2024

    # Generate year list as string for API
    years = ",".join(str(year) for year in range(start_year, end_year + 1))

    for imf_code, indicator_name in imf_indicators.items():
        try:
            # IMF API URL
            url = f"https://www.imf.org/external/datamapper/api/v1/{imf_code}/TWN?periods={years}"

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Extract Taiwan data from response
                # Note: IMF API structure is data["values"][indicator_code]["TWN"]
                if (
                    "values" in data
                    and imf_code in data["values"]
                    and "TWN" in data["values"][imf_code]
                ):
                    twn_values = data["values"][imf_code]["TWN"]

                    for year_str, value in twn_values.items():
                        if value is not None:
                            year = int(year_str)

                            # Convert and round values
                            if indicator_name == "population_total":
                                # IMF population is in millions, convert to actual count
                                rounded_value = round(value * 1_000_000)
                            elif indicator_name == "gdp_current_usd":
                                # IMF GDP is in billions, convert to actual USD
                                rounded_value = round(value * 1_000_000_000)
                            elif indicator_name == "gdp_ppp_current_intl":
                                # IMF PPP GDP is in billions, convert to actual
                                rounded_value = round(value * 1_000_000_000)
                            elif indicator_name in [
                                "gdp_per_capita_current_usd",
                                "gdp_per_capita_ppp_current_intl",
                            ]:
                                # Per capita values are already in correct units
                                rounded_value = round(value)
                            else:
                                rounded_value = round(value)

                            taiwan_data.append(
                                {
                                    "country_name": "Taiwan",
                                    "country_code_2": "TW",
                                    "country_code_3": "TWN",
                                    "continent": "Asia",
                                    "year": year,
                                    "indicator": indicator_name,
                                    "value": rounded_value,
                                }
                            )

                print(f"Successfully fetched {indicator_name} for Taiwan from IMF")
            else:
                print(
                    f"Warning: Failed to fetch {imf_code} from IMF API (status code: {response.status_code})"
                )

        except Exception as e:
            print(f"Warning: Error fetching {imf_code} for Taiwan from IMF: {str(e)}")
            continue

    print(f"Downloaded {len(taiwan_data)} data points for Taiwan from IMF")
    return pd.DataFrame(taiwan_data)


def download_economic_data(df_countries):
    """
    Download GDP, GDP per capita, and population data from World Bank API.

    Args:
        df_countries (pd.DataFrame): DataFrame with country information

    Returns:
        pd.DataFrame: Economic data for all countries and years
    """
    print("Downloading economic data from World Bank API...")

    # World Bank indicators to download
    indicators = {
        "NY.GDP.MKTP.CD": "gdp_current_usd",  # GDP at market prices (current US$)
        "NY.GDP.PCAP.CD": "gdp_per_capita_current_usd",  # GDP per capita (current US$)
        "SP.POP.TOTL": "population_total",  # Total population
        "NY.GDP.MKTP.PP.CD": "gdp_ppp_current_intl",  # GDP, PPP (current international $)
        "NY.GDP.PCAP.PP.CD": "gdp_per_capita_ppp_current_intl",  # GDP per capita, PPP (current international $)
    }

    # Create empty list to store data
    all_data = []

    # Set time range (2000 to most recent complete year)
    start_year = 2000
    end_year = 2024  # Most recent complete year

    print(
        f"Downloading data for {len(df_countries)} countries from {start_year} to {end_year}..."
    )

    # Process countries in batches to avoid API rate limits
    batch_size = 5
    countries_processed = 0
    countries_with_data = 0

    for i in range(0, len(df_countries), batch_size):
        batch = df_countries.iloc[i : i + batch_size]

        for index, country in batch.iterrows():
            country_code = country["country_code_3"]  # Use ISO3 code for World Bank API
            country_name = country["country_name"]
            continent = country["continent"]

            # Skip countries in the exclude list (no data available in World Bank API)
            if country_name in EXCLUDE_COUNTRIES:
                countries_processed += 1
                continue

            # Skip countries without ISO3 code
            if pd.isna(country_code):
                continue

            country_data_count = 0
            try:
                # Fetch data for each indicator
                for indicator_code, indicator_name in indicators.items():
                    try:
                        data = wb.data.fetch(
                            indicator_code,
                            country_code,
                            time=range(start_year, end_year + 1),
                        )

                        # Process the data
                        data_list = list(data)
                        for point in data_list:
                            if point["value"] is not None:
                                # Extract year from time string (e.g., 'YR2020' -> 2020)
                                year_str = point["time"]
                                if year_str.startswith("YR"):
                                    year = int(year_str[2:])
                                else:
                                    year = int(year_str)

                                # Round values based on indicator type for consistency
                                raw_value = point["value"]
                                if indicator_name == "gdp_current_usd":
                                    # Round GDP to whole numbers
                                    rounded_value = round(raw_value)
                                elif indicator_name == "gdp_per_capita_current_usd":
                                    # Round GDP per capita to 0 decimal places
                                    rounded_value = round(raw_value)
                                elif indicator_name == "population_total":
                                    # Round population to whole numbers
                                    rounded_value = round(raw_value)
                                else:
                                    # Default rounding for any other indicators
                                    rounded_value = round(raw_value)

                                all_data.append(
                                    {
                                        "country_name": country_name,
                                        "country_code_2": country["country_code_2"],
                                        "country_code_3": country_code,
                                        "continent": continent,
                                        "year": year,
                                        "indicator": indicator_name,
                                        "value": rounded_value,
                                    }
                                )
                                country_data_count += 1

                    except Exception as e:
                        print(
                            f"Warning: Error fetching {indicator_name} for {country_name}: {str(e)}"
                        )
                        continue

                if country_data_count > 0:
                    countries_with_data += 1

                countries_processed += 1

            except Exception as e:
                print(f"Error processing {country_name}: {str(e)}")
                countries_processed += 1
                continue

        print(
            f"Processed {min(i + batch_size, len(df_countries))} of {len(df_countries)} countries... "
            f"Collected data for {countries_with_data} countries so far."
        )

        # Add delay to respect API rate limits
        time.sleep(0.5)

    return pd.DataFrame(all_data), countries_processed, countries_with_data


def save_data_files(df_countries, df_gdp):
    """
    Save data to CSV files in the data directory.

    Args:
        df_countries (pd.DataFrame): Country reference data
        df_gdp (pd.DataFrame): Economic data
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Save country reference table
    file_path_countries = "data/all_countries_with_iso_continents.csv"
    df_countries.to_csv(file_path_countries, index=False)
    print(f"Country reference table saved to: {file_path_countries}")

    # Save economic data
    file_path_gdp = "data/gdp_data_2000_present.csv"
    df_gdp.to_csv(file_path_gdp, index=False)
    print(f"Economic data saved to: {file_path_gdp}")


def main():
    """
    Main function to orchestrate the data download process.
    """
    print("=" * 60)
    print("GDP Data Downloader - Starting...")
    print("=" * 60)

    try:
        # Step 1: Create country reference table
        df_countries = create_country_reference_table()
        print(f"Created reference table for {len(df_countries)} countries")

        # Step 2: Download economic data from World Bank
        df_gdp, countries_processed, countries_with_data = download_economic_data(
            df_countries
        )

        # Step 3: Download Taiwan data from IMF (since it's not in World Bank)
        df_taiwan = download_taiwan_data_from_imf()

        # Step 4: Merge Taiwan data with World Bank data
        if len(df_taiwan) > 0:
            df_gdp = pd.concat([df_gdp, df_taiwan], ignore_index=True)
            print(f"Added Taiwan data from IMF: {len(df_taiwan)} data points")
            countries_with_data += 1

        # Step 5: Save data to files
        save_data_files(df_countries, df_gdp)

        # Step 6: Print summary
        print("\n" + "=" * 60)
        print("Download Complete!")
        print("=" * 60)
        print(f"Total data points: {len(df_gdp)}")
        print(f"Total countries processed: {countries_processed}")
        print(f"Countries with data: {countries_with_data} (including Taiwan from IMF)")
        if len(df_gdp) > 0:
            print(f"Years covered: {df_gdp['year'].min()} to {df_gdp['year'].max()}")
        print("=" * 60)

    except Exception as e:
        print(f"Error during data download: {str(e)}")
        raise


if __name__ == "__main__":
    main()
