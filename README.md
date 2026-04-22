## Note- If the website shows it hits the rate limit, just download the files and run it locally in VS Code or the terminal; it only supports US stocks and options, as yfinance only has US options data without any premium.
# To Run
Type in the terminal:

pip install -r requirements.txt

streamlit run app.py


# App Link
https://optionchain-analyzer-strategybuilder.streamlit.app/

# 📈 Advanced Financial Options Modeling Dashboard

An open-source, cloud-hosted financial tool designed to visualize, calculate, and model complex stock market options strategies. Built entirely in Python using Streamlit, this dashboard bridges the gap between expensive professional trading software (like Opstra or Sensibull) and retail traders by providing real-time data, complex mathematical modeling, and interactive risk analysis completely for free.

## 🧠 What Does This App Do?
At its core, options trading is highly non-linear mathematics. The value of an options strategy changes based on the future price of a stock. 

This application acts as a **Mathematical Simulation Engine**. It takes user inputs (strike prices, premiums, and quantities), simulates a massive range of potential future stock prices, and calculates the exact profit, loss, and breakeven points for the strategy. It then renders these mathematical arrays into interactive, highly readable visual graphs.

---

## ✨ Core Features & Explanations

### 1. 🏗️ The Custom Strategy Builder (Opstra-Style Architecture)
The flagship feature of this dashboard is the **Custom Strategy Builder**, available in both Live Data and Manual modes.
* **How it works:** Instead of forcing the user to pick from pre-defined strategies, this tool allows users to act as financial architects. Users can stack an infinite number of "Legs" (e.g., Buy 2 Calls, Sell 1 Put, Buy 100 Shares of Stock).
* **The Logic:** The backend engine loops through every active leg in the user's custom checklist, dynamically multiplies the premiums and payoff formulas by the selected quantities, and aggregates them into a single, unified risk profile.

### 2. 📊 The Mathematical & Analytics Engine
The app doesn't just draw lines; it calculates precise financial metrics for any strategy (standard or custom).
* **Net Premium Tracking:** Automatically calculates whether a complex multi-leg trade is a **Net Debit** (costs money to enter) or a **Net Credit** (pays money to enter).
* **Absolute Risk Bounds:** Computes the exact Maximum Profit and Maximum Risk/Loss potential for the trade.
* **Breakeven Analysis:** Mathematically determines the exact price the underlying stock must reach for the trade to break even.

### 3. 📉 Interactive Data Visualization
The mathematical arrays are fed into **Plotly** to generate two distinct, interactive charts:
* **Net Profit (P&L) Chart:** Displays the actual realized profit or loss after subtracting the initial premiums paid. Highlights the "Profit Zone" (Green) and "Loss Zone" (Red).
* **Gross Payoff Chart:** Displays the intrinsic value of the options at expiration before the cost of the premiums is factored in.

### 4. ⚡ Live Market Data & Smart Caching
The application connects directly to global stock markets via the `yfinance` API.
* **Real-Time Options Chains:** Instantly downloads the current Spot Price and the entire Options Chain for the nearest expiration date.
* **Smart Caching:** To prevent slow loading times and API rate limits, the app utilizes Streamlit's `@st.cache_data`. It stores heavy data pulls in server RAM for 5 minutes, allowing users to adjust sliders and change strategies with zero lag.
* **Smart-Linking Strikes:** A UX feature that automatically aligns secondary strike prices (`K2`) to maintain logical spread widths when the primary strike (`K1`) is adjusted.

### 5. 💱 Real-Time Currency Conversion (USD ↔ INR)
Because global tech stocks (like Apple or Tesla) are priced in USD, it is difficult for Indian retail traders to visualize the actual capital required. 
* **Dynamic Multiplier:** The app fetches the live USD/INR exchange rate upon loading. If the user toggles to INR, the entire dashboard—including spot prices, option premiums, strike prices, and graph axes—dynamically scales to Indian Rupees before the math engine processes it, preserving perfect mathematical integrity.

### 6. 🛠️ Manual Data Entry Fallback (For NSE/BSE)
Free financial APIs often restrict data for Indian indices like NIFTY or BANKNIFTY. To ensure the tool is never "broken," the app features a robust **Manual Mode**.
* **Total Independence:** Users can manually type in the current stock price and option premiums from their broker terminal.
* **Full Feature Parity:** The manual mode supports all 8 standard strategies as well as the infinite Custom Strategy Builder, making this tool universally applicable to any market in the world.

---

## 🏗️ Under the Hood (Tech Stack)

* **Frontend Framework:** `Streamlit` (Provides a highly responsive, React-like state management system via `session_state` to dynamically hide/show UI elements based on user interaction).
* **Data Processing:** `Pandas` and `NumPy` (Used to generate continuous linear spaces for spot prices and compute maximums/minimums across massive data arrays).
* **Visualization:** `Plotly Graph Objects` (Renders the interactive SVG charts).
* **Data Provider:** `yfinance` (Engineered to utilize internal `curl_cffi` sessions to bypass cloud-server rate limiting and crumb/cookie blockers).

---

## 📐 Pre-Built Strategies Included
For beginners, the dashboard includes 8 highly optimized, pre-built structural templates:
1. **Covered Call** (Income Generation)
2. **Protective Put** (Crash Insurance)
3. **Long Straddle** (High Volatility, Direction Neutral)
4. **Short Straddle** (Low Volatility, Direction Neutral)
5. **Long Strangle** (High Volatility, Budget Friendly)
6. **Short Strangle** (Low Volatility, Wide Margin of Safety)
7. **Bull Spread** (Capped Upside, Subsidized Cost)
8. **Bear Spread** (Capped Downside, Subsidized Cost)

---
*Disclaimer: This tool is built for educational and academic purposes (ES 418 Project). It is not financial advice.*
