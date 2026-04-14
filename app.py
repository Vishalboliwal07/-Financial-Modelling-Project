import streamlit as st
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Professional Options Analyzer")

# ================= CUSTOM CSS STYLING =================
st.markdown("""
    <style>
    .price-bar {
        background-color: #1a365d;
        color: #63b3ed;
        padding: 15px;
        border-radius: 5px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .metric-label { font-size: 14px; color: #cbd5e0; margin-bottom: 0px; }
    .metric-value { font-size: 32px; font-weight: bold; color: white; margin-top: 0px; }
    .badge-debit { background-color: #1c4532; color: #48bb78; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: bold; }
    .badge-credit { background-color: #4a1212; color: #f56565; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ================= SIDEBAR =================
st.sidebar.header("⚙️ Dashboard Controls")
use_manual = st.sidebar.checkbox("🛠️ Manual Data Entry Mode", value=False)
zoom_pct = st.sidebar.slider("🔍 Chart Zoom Range (+/- %)", 10, 150, 50) / 100

STOCK_DATABASE = {
    "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
    "Nvidia": "NVDA", "Tesla": "TSLA", "Reliance": "RELIANCE.NS", "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK", "HDFC Bank": "HDFCBANK.NS", "Infosys": "INFY.NS"
}

# ================= TOP SELECTION =================
col_left, col_right = st.columns(2)
with col_left:
    if not use_manual:
        search = st.text_input("Select Company", value="Apple")
        suggestions = [f"{n} ({t})" for n, t in STOCK_DATABASE.items() if search.lower() in n.lower() or search.lower() in t.lower()]
        selected_stock = st.selectbox("Select the correct match:", suggestions if suggestions else [search.upper()])
        ticker_symbol = selected_stock.split('(')[-1].strip(')')
    else: ticker_symbol = st.text_input("Enter Manual Ticker Symbol", value="CUSTOM")

with col_right:
    strategies = ["Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle", "Covered Call", "Protective Put", "Bull Spread", "Bear Spread"] #added long and short
    strategy = st.selectbox("Strategy", strategies)

st.markdown("---")

# ================= DATA FETCHING =================
if not use_manual:
    ticker_obj = yf.Ticker(ticker_symbol)
    with st.spinner("Fetching Market Data..."):
        hist = ticker_obj.history(period="1d")
        if hist.empty: st.stop()
        current_price = hist["Close"].iloc[-1]
        st.markdown(f'<div class="price-bar">Live Price for {ticker_symbol}: ${current_price:.2f}</div>', unsafe_allow_html=True)
        expiries = ticker_obj.options
        if not expiries: st.stop()
        expiry = st.selectbox("Select Expiry", expiries)
        chain = ticker_obj.option_chain(expiry)
        calls, puts = chain.calls, chain.puts

    def get_mid(df, k):
        row = df[df['strike'] == k]
        if row.empty: return 0.0
        return (row['bid'].values[0] + row['ask'].values[0]) / 2 or row['lastPrice'].values[0]

    strikes = sorted(calls['strike'].values)
    k1 = st.selectbox("Strike K1", strikes, index=list(strikes).index(min(strikes, key=lambda x: abs(x - current_price))))
    need_k2 = strategy in ["Long Strangle", "Short Strangle", "Bull Spread", "Bear Spread"] #long and short 
    k2 = st.selectbox("Strike K2", strikes, index=min(len(strikes)-1, list(strikes).index(k1)+1)) if need_k2 else None
    cp1, pp1 = get_mid(calls, k1), get_mid(puts, k1)
    cp2, pp2 = (get_mid(calls, k2), get_mid(puts, k2)) if need_k2 else (0.0, 0.0)
else:
    st.markdown(f'<div class="price-bar">🛠️ Manual Entry Mode Active</div>', unsafe_allow_html=True)
    m_col1, m_col2 = st.columns(2)
    current_price = m_col1.number_input("Spot Price", value=100.0)
    k1 = m_col1.number_input("Strike K1", value=100.0)
    cp1 = m_col2.number_input("Call Premium K1", value=5.0)
    pp1 = m_col1.number_input("Put Premium K1", value=5.0)
    need_k2 = strategy in ["Strangle", "Bull Spread", "Bear Spread"]
    if need_k2:
        k2 = m_col2.number_input("Strike K2", value=110.0)
        cp2 = m_col2.number_input("Call Premium K2", value=2.0)
        pp2 = m_col1.number_input("Put Premium K2", value=2.0)
    else: k2, cp2, pp2 = None, 0.0, 0.0

# ================= PREMIUM DETAILS SECTION =================
st.markdown("### Premium Details")
p_col1, p_col2, p_col3, p_col4 = st.columns(4)
p_col1.metric(f"Call Leg (K1: {k1})", f"${cp1:.2f}")
p_col2.metric(f"Put Leg (K1: {k1})", f"${pp1:.2f}")
if need_k2:
    p_col3.metric(f"Call Leg (K2: {k2})", f"${cp2:.2f}")
    p_col4.metric(f"Put Leg (K2: {k2})", f"${pp2:.2f}")

# ================= SPOT PRICE SIMULATOR =================
st.markdown("---")



sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    # Toggle button for Normal vs Percentage
    shift_mode = st.radio("Adjustment Mode", ["Normal ($)", "Percentage (%)"], horizontal=True)

with sim_col2:
    # Scroll bar (Slider) logic to adjust the Spot Price
    if shift_mode == "Normal ($)":
        shift_val = st.slider("Spot Price ($)", min_value=-100.0, max_value=100.0, value=0.0, step=1.0)
        current_price = current_price + shift_val
    else:
        shift_val = st.slider("Spot Price (%)", min_value=-20.0, max_value=20.0, value=0.0, step=0.5)
        current_price = current_price * (1 + (shift_val / 100))


# ================= MATH ENGINE (With Breakeven Injection) =================
def c_pay(S, K): return np.maximum(S - K, 0)
def p_pay(S, K): return np.maximum(K - S, 0)

S_temp = np.linspace(current_price * (1-zoom_pct), current_price * (1+zoom_pct), 1000)
#long and short
if strategy == "Long Straddle":   
    p_temp = (c_pay(S_temp, k1) + p_pay(S_temp, k1)) - (cp1 + pp1)
    net_premium, is_debit = (cp1 + pp1), True
elif strategy == "Short Straddle":
    p_temp = (cp1 + pp1) - (c_pay(S_temp, k1) + p_pay(S_temp, k1))
    net_premium, is_debit = (cp1 + pp1), False
elif strategy == "Long Strangle":
    p_temp = (p_pay(S_temp, k1) + c_pay(S_temp, k2)) - (pp1 + cp2)
    net_premium, is_debit = (pp1 + cp2), True
elif strategy == "Short Strangle":
    p_temp = (pp1 + cp2) - (p_pay(S_temp, k1) + c_pay(S_temp, k2))
    net_premium, is_debit = (pp1 + cp2), False
    #end
elif strategy == "Covered Call":
    p_temp = (S_temp - current_price) - c_pay(S_temp, k1) + cp1
    net_premium, is_debit = cp1, False
elif strategy == "Protective Put":
    p_temp = (S_temp - current_price) + p_pay(S_temp, k1) - pp1
    net_premium, is_debit = pp1, True
elif strategy == "Bull Spread":
    p_temp = (c_pay(S_temp, k1) - c_pay(S_temp, k2)) - cp1 + cp2
    net_premium, is_debit = (cp1 - cp2), (cp1 > cp2)
elif strategy == "Bear Spread":
    p_temp = (p_pay(S_temp, k2) - p_pay(S_temp, k1)) - pp2 + pp1
    net_premium, is_debit = (pp2 - pp1), (pp2 > pp1)

# Find Exact Breakevens
bes = []
for i in range(len(S_temp)-1):
    if p_temp[i] * p_temp[i+1] <= 0:
        be = S_temp[i] - p_temp[i]*(S_temp[i+1]-S_temp[i])/(p_temp[i+1]-p_temp[i])
        bes.append(round(be, 2))

# Final array for plotting
S = np.sort(np.unique(np.concatenate([S_temp, bes, [k1], [k2] if k2 else []])))
# long and short
if strategy == "Long Straddle":
    gross = c_pay(S, k1) + p_pay(S, k1)
    profit = gross - net_premium
elif strategy == "Short Straddle":
    gross = -(c_pay(S, k1) + p_pay(S, k1))
    profit = gross + net_premium
elif strategy == "Long Strangle":
    gross = p_pay(S, k1) + c_pay(S, k2)
    profit = gross - net_premium
elif strategy == "Short Strangle":
    gross = -(p_pay(S, k1) + c_pay(S, k2))
    profit = gross + net_premium
    #end
elif strategy == "Covered Call":
    gross = (S - current_price) - c_pay(S, k1)
    profit = gross + cp1
elif strategy == "Protective Put":
    gross = (S - current_price) + p_pay(S, k1)
    profit = gross - net_premium
elif strategy == "Bull Spread":
    gross = c_pay(S, k1) - c_pay(S, k2)
    profit = gross - net_premium
elif strategy == "Bear Spread":
    gross = p_pay(S, k2) - p_pay(S, k1)
    profit = gross - net_premium

# ================= UI METRICS =================
st.markdown("## Metrics")
met_col1, met_col2, met_col3, met_col4, met_col5 = st.columns(5) # Added a 5th column
#rr
# Numeric references for the math
max_p = np.max(profit)
max_l = np.min(profit)

# Define which strategies have capped risk/reward
profit_defined = strategy not in ["Long Straddle", "Long Strangle", "Protective Put"]
risk_defined = strategy not in ["Short Straddle", "Short Strangle", "Covered Call"]
#rr

with met_col1:
    st.markdown('<p class="metric-label">Max Profit</p>', unsafe_allow_html=True)
    val = "Undefined" if strategy in ["Long Straddle", "Long Strangle", "Protective Put"] else f"${np.max(profit):.2f}" #long and short
    st.markdown(f'<p class="metric-value">{val}</p>', unsafe_allow_html=True)

with met_col2:
    st.markdown('<p class="metric-label">Max Loss (Risk)</p>', unsafe_allow_html=True)
    val = "Undefined" if strategy in ["Short Straddle", "Short Strangle", "Covered Call"] else f"${np.min(profit):.2f}" #long and short
    st.markdown(f'<p class="metric-value">{val}</p>', unsafe_allow_html=True)

with met_col3:
    st.markdown('<p class="metric-label">Breakeven(s)</p>', unsafe_allow_html=True)
    be_val = ", ".join([f"${b}" for b in bes]) if bes else "None"
    st.markdown(f'<p class="metric-value" style="font-size:24px;">{be_val}</p>', unsafe_allow_html=True)

with met_col4:
    st.markdown('<p class="metric-label">Net Premium</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">${abs(net_premium):.2f}</p>', unsafe_allow_html=True)
    badge_text = "Debit" if is_debit else "Credit"
    badge_class = "badge-debit" if is_debit else "badge-credit"
    st.markdown(f'<span class="{badge_class}">↑ {badge_text}</span>', unsafe_allow_html=True)

#rr
with met_col5:
    st.markdown('<p class="metric-label">Risk : Reward</p>', unsafe_allow_html=True)
    if profit_defined and risk_defined:
        if max_l == 0:
            rr_val = "Risk-Free"
        else:
            # Calculates how much you make for every $1 risked
            ratio = max_p / abs(max_l)
            rr_val = f"1 : {ratio:.2f}"
    else:
        rr_val = "Undefined"
    st.markdown(f'<p class="metric-value">{rr_val}</p>', unsafe_allow_html=True)
#rr

# ================= PLOTLY GRAPHS (VERTICAL) =================
def create_fig(x, y, title, label_name):
    fig = go.Figure()
    
    # Fill Logic (Green for Profit, Red for Loss)
    fig.add_trace(go.Scatter(x=x, y=np.where(y>=0, y, 0), fill='tozeroy', fillcolor='rgba(72, 187, 120, 0.3)', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=np.where(y<0, y, 0), fill='tozeroy', fillcolor='rgba(245, 101, 101, 0.3)', line=dict(width=0), showlegend=False))
    
    # Main Line
    fig.add_trace(go.Scatter(x=x, y=y, name=label_name, line=dict(color='#63b3ed', width=3)))
    
    # Legend Dummies (Lines for legend only)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='orange', dash='dash'), name='Spot Price'))
    if "Profit" in title and bes:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#9f7aea', dash='dot'), name='Breakeven'))

    # Draw vertical reference lines
    fig.add_vline(x=current_price, line_dash="dash", line_color="orange")
    if "Profit" in title:
        for be in bes:
            fig.add_vline(x=be, line_dash="dot", line_color="#9f7aea")

    # Explicitly enhance the Zero Line separating Profit and Loss
    fig.add_hline(y=0, line_color="white", line_width=2, opacity=0.8)
    
    # --- SMART SCALING Y-AXIS ---
    # Find the actual highest and lowest points of the data
    actual_max = np.max(y)
    actual_min = np.min(y)
    
    # Calculate the total height of the graph for dynamic padding
    y_range = actual_max - actual_min
    if y_range == 0: y_range = 10 # Fallback
    
    # Add a 15% visual cushion above and below the data
    y_max = actual_max + (y_range * 0.15)
    y_min = actual_min - (y_range * 0.15)
    
    # Guarantee the zero line is always clearly visible, even if the trade is 100% profit or 100% loss
    if y_min >= 0: y_min = -y_max * 0.15
    if y_max <= 0: y_max = -y_min * 0.15

    fig.update_layout(
        title=f"<b>{title}</b>", 
        template="plotly_dark", 
        hovermode="x unified", 
        height=500,
        xaxis_title="Stock Price at Expiry ($)", 
        yaxis_title="Profit / Loss ($)" if "Profit" in title else "Value ($)",
        yaxis=dict(
            zeroline=True, 
            zerolinewidth=2, 
            zerolinecolor='rgba(255,255,255,0.5)', 
            range=[y_min, y_max] # Apply the smart dynamic range
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

st.plotly_chart(create_fig(S, gross, "1. Payoff Diagram (Gross Value)", "Payoff"), use_container_width=True)
st.plotly_chart(create_fig(S, profit, "2. Profit Diagram (Net Realized)", "Profit"), use_container_width=True)

