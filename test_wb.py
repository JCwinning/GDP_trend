import wbgapi as wb

indicators = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD": "gdp_constant_2015_usd",
    "NY.GDP.PCAP.CD": "gdp_per_capita_current_usd",
    "SP.POP.TOTL": "population_total",
    "NY.GDP.MKTP.PP.CD": "gdp_ppp_current_intl",
    "NY.GDP.PCAP.PP.CD": "gdp_per_capita_ppp_current_intl",
}

print("Fetching all countries for these indicators...")
try:
    df = wb.data.DataFrame(list(indicators.keys()), time=range(2000, 2024), skipBlanks=True, columns='series')
    print(df.head())
    print("Shape:", df.shape)
except Exception as e:
    print("Error:", e)
