import yfinance as yf
import pandas as pd
import numpy as np
import requests
import streamlit as st
from datetime import datetime, timedelta

# Set up the Streamlit web app
st.title("Advanced Stock Ticker Picker")
st.sidebar.header("Stock Selection Filters")

# User Inputs
market_cap_filter = st.sidebar.selectbox("Market Cap", ["All", "Large Cap", "Mid Cap", "Small Cap"])
pe_ratio_range = st.sidebar.slider("P/E Ratio Range", 0, 100, (5, 25))
sector_filter = st.sidebar.selectbox("Sector", ["All", "Technology", "Finance", "Healthcare", "Consumer Discretionary", "Industrials"])
volatility_filter = st.sidebar.slider("Volatility (30-day)", 0.0, 5.0, (0.5, 2.0))

# Stock Universe (Using S&P 500 as a base example)
@st.cache_data
def load_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table['Symbol'].tolist()

tickers = load_sp500_tickers()

# Fetch Yahoo Finance Data
@st.cache_data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    return stock, hist

# Predict Stock Trend
def predict_trend(hist):
    short_ma = hist['Close'].rolling(window=20).mean()
    long_ma = hist['Close'].rolling(window=50).mean()
    rsi = 100 - (100 / (1 + hist['Close'].pct_change().rolling(window=14).mean()))
    
    if short_ma.iloc[-1] > long_ma.iloc[-1] and rsi.iloc[-1] < 70:
        return "Bullish"
    elif short_ma.iloc[-1] < long_ma.iloc[-1] and rsi.iloc[-1] > 30:
        return "Bearish"
    else:
        return "Neutral"

# Screening Function
def screen_stocks():
    selected_stocks = []
    
    for ticker in tickers[:20]:  # Limiting to 20 for performance
        try:
            stock, hist = get_stock_data(ticker)
            info = stock.info
            
            # Apply filters
            if market_cap_filter != "All":
                if market_cap_filter == "Large Cap" and info.get("marketCap", 0) < 10e9:
                    continue
                elif market_cap_filter == "Mid Cap" and not (2e9 <= info.get("marketCap", 0) < 10e9):
                    continue
                elif market_cap_filter == "Small Cap" and info.get("marketCap", 0) < 2e9:
                    continue
                
            if not (pe_ratio_range[0] <= info.get("trailingPE", 0) <= pe_ratio_range[1]):
                continue
            
            if sector_filter != "All" and info.get("sector", "") != sector_filter:
                continue
            
            # Volatility Filter
            daily_returns = hist['Close'].pct_change()
            volatility = np.std(daily_returns) * np.sqrt(252)
            if not (volatility_filter[0] <= volatility <= volatility_filter[1]):
                continue
            
            trend = predict_trend(hist)
            
            selected_stocks.append({
                "Ticker": ticker,
                "Name": info.get("longName", "Unknown"),
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Volatility": round(volatility, 2),
                "Prediction": trend
            })
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    
    return pd.DataFrame(selected_stocks)

# Run screening and display results
if st.sidebar.button("Find Stocks"):
    result_df = screen_stocks()
    st.write("### Selected Stocks Based on Filters:")
    st.dataframe(result_df)
