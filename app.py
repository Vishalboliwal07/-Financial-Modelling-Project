import streamlit as st
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Professional Options Analyzer")

if 'custom_legs' not in st.session_state:
    st.session_state.custom_legs = []

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
    
    /* Removed hardcoded colors. Opacity creates the faded look in both Light and Dark themes */
    .metric-label { font-size: 14px; opacity: 0.7; margin-bottom: 0px; }
    .metric-value { font-size: 32px; font-weight: bold; margin-top: 0px; }
    
    /* Adjusted badge colors to use RGBA so they look good on both white and black backgrounds */
    .badge-debit { background-color: rgba(72, 187, 120, 0.2); color: #2f855a; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: bold; }
    .badge-credit { background-color: rgba(245, 101, 101, 0.2); color: #c53030; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


# ================= SIDEBAR =================
st.sidebar.header("⚙️ Dashboard Controls")
use_manual = st.sidebar.checkbox("🛠️ Manual Data Entry Mode", value=False)
currency_mode = st.sidebar.radio("💵 Currency Display", ["USD ($)", "INR (₹)"]) # NEW TOGGLE
zoom_pct = st.sidebar.slider("🔍 Chart Zoom Range (+/- %)", 10, 150, 50) / 100

STOCK_DATABASE = {
    # US Big Tech
    "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
    "Nvidia": "NVDA", "Tesla": "TSLA", "Meta": "META", "Netflix": "NFLX",
    
    # Semiconductor & IC Design
    "TSMC": "TSM", "AMD": "AMD", "Intel": "INTC", "ASML": "ASML",
    "Broadcom": "AVGO", "Qualcomm": "QCOM", "Texas Instruments": "TXN",

    # Indian Indices (F&O Favourites)
    "Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "India VIX": "^INDIAVIX",

    # Indian Heavyweights (NSE)
    "Reliance": "RELIANCE.NS", "HDFC Bank": "HDFCBANK.NS", "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS", "TCS": "TCS.NS", "Tata Motors": "TATAMOTORS.NS",
    "State Bank of India": "SBIN.NS", "ITC": "ITC.NS", "L&T": "LT.NS"
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
    strategies = ["Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle", "Covered Call", "Protective Put", "Bull Spread", "Bear Spread", "Custom Strategy"] #added long and short
    strategy = st.selectbox("Strategy", strategies)

st.markdown("---")

# --- STRATEGY COMPOSITION INDICATOR ---
# A dictionary explaining the physical makeup of every strategy
strategy_composition = {
    "Covered Call": "📈 1 Long Stock + 📉 1 Short Call",
    "Protective Put": "📈 1 Long Stock + 📈 1 Long Put",
    "Long Straddle": "📈 1 Long Call + 📈 1 Long Put (Same Strike)",
    "Short Straddle": "📉 1 Short Call + 📉 1 Short Put (Same Strike)",
    "Long Strangle": "📈 1 Long Call + 📈 1 Long Put (Different Strikes)",
    "Short Strangle": "📉 1 Short Call + 📉 1 Short Put (Different Strikes)",
    "Bull Spread": "📈 1 Long Call (Lower Strike) + 📉 1 Short Call (Higher Strike)",
    "Bear Spread": "📈 1 Long Put (Higher Strike) + 📉 1 Short Put (Lower Strike)"
}

# Fetch the text for the currently selected strategy
comp_text = strategy_composition.get(strategy, "Custom Configuration")

# Render a sleek UI box for it
st.markdown(f"""
    <div style="padding: 12px; border-radius: 5px; background-color: rgba(255,255,255,0.05); border-left: 4px solid #63b3ed; margin-bottom: 15px;">
        <span style="font-weight: bold; font-size: 16px; color: #e2e8f0;">{strategy}</span><br>
        <span style="color: #a0aec0; font-size: 14px;">Structure: {comp_text}</span>
    </div>
""", unsafe_allow_html=True)

# ================= DATA FETCHING =================
st.markdown("---")

# ================= REAL-TIME CURRENCY CONVERSION =================
@st.cache_data(ttl=3600) # Caches the exchange rate for 1 hour to prevent API bans
def get_exchange_rate():
    try:
        return yf.Ticker("USDINR=X").history(period="1d")["Close"].iloc[-1]
    except:
        return 83.50 # Fallback rate just in case Yahoo Finance is down

live_usd_inr = get_exchange_rate()

# Smart detection: Is the stock already in INR?
is_indian = ticker_symbol.endswith(".NS") or ticker_symbol.endswith(".BO") or ticker_symbol.startswith("^NSE")

if currency_mode == "USD ($)":
    currency_sym = "$"
    multiplier = 1.0 if not is_indian else (1.0 / live_usd_inr)
else:
    currency_sym = "₹"
    multiplier = live_usd_inr if not is_indian else 1.0

# ================= DATA FETCHING =================
if not use_manual:
    ticker_obj = yf.Ticker(ticker_symbol)
    with st.spinner("Fetching Market Data..."):
        hist = ticker_obj.history(period="1d")
        if hist.empty: st.stop()
        
        current_price = hist["Close"].iloc[-1] * multiplier 
        st.markdown(f'<div class="price-bar">Live Price for {ticker_symbol}: {currency_sym}{current_price:.2f}</div>', unsafe_allow_html=True)
        
        expiries = ticker_obj.options
        if not expiries:
            st.warning(f"⚠️ **Options Chain Unavailable**")
            st.info(f"Yahoo Finance does not provide free options data for {ticker_symbol}. To analyze strategies for this stock, please check the **'🛠️ Manual Data Entry Mode'** box in the sidebar and enter the premiums manually.")
            st.stop()
        expiry = st.selectbox("Select Expiry", expiries)
        chain = ticker_obj.option_chain(expiry)
        calls, puts = chain.calls, chain.puts

    def get_mid(df, k):
        row = df[df['strike'] == k]
        if row.empty: return 0.0
        return (row['bid'].values[0] + row['ask'].values[0]) / 2 or row['lastPrice'].values[0]

    strikes = sorted(calls['strike'].values)
    baseline_k = current_price / multiplier 

    if strategy == "Custom Strategy":
        # --- LIVE CUSTOM BUILDER ---
        st.markdown("### 🏗️ Live Custom Strategy Builder")
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1, 1.2, 1.2, 1.2, 2])
        c_action = c1.selectbox("Action", ["Buy", "Sell"], key="l_act")
        c_qty = c2.number_input("Qty", value=1, min_value=1, step=1, key="l_qty")
        c_type = c3.selectbox("Type", ["Call", "Put", "Stock"], key="l_type")
        
        if c_type == "Stock":
            c_strike = c4.number_input("Strike (N/A)", value=0.0, disabled=True, key="l_strk_s")
            default_price = current_price / multiplier
        else:
            default_strike_idx = list(strikes).index(min(strikes, key=lambda x: abs(x - baseline_k)))
            c_strike = c4.selectbox("Strike", strikes, index=default_strike_idx, key="l_strk_o")
            default_price = get_mid(calls, c_strike) if c_type == "Call" else get_mid(puts, c_strike)
            
        c_price = c5.number_input("Price", value=float(default_price), key="l_prc")
        
        def add_live_leg():
            st.session_state.custom_legs.append({
                "action": st.session_state.l_act, "qty": st.session_state.l_qty, "type": st.session_state.l_type,
                "strike": st.session_state.l_strk_o if st.session_state.l_type != "Stock" else 0,
                "price": st.session_state.l_prc, "active": True
            })
            
        c6.markdown("<br>", unsafe_allow_html=True)
        c6.button("➕ ADD POSITION", on_click=add_live_leg, use_container_width=True)
        
        # Dummy variables to prevent crash later
        k1, cp1, pp1, need_k2, k2, cp2, pp2 = baseline_k, 0, 0, False, None, 0, 0

    else:
        # --- EXISTING LIVE LOGIC ---
        k1_index = list(strikes).index(min(strikes, key=lambda x: abs(x - baseline_k)))
        k1 = st.selectbox("Strike K1", strikes, index=k1_index)
        need_k2 = strategy in ["Long Strangle", "Short Strangle", "Bull Spread", "Bear Spread"] 
        if need_k2:
            target_k2 = k1 - 5 if strategy == "Bear Spread" else k1 + 5
            best_k2 = min(strikes, key=lambda x: abs(x - target_k2))
            k2 = st.selectbox("Strike K2", strikes, index=list(strikes).index(best_k2), key=f"live_k2_{ticker_symbol}_{strategy}")
        else: k2 = None

        cp1, pp1 = get_mid(calls, k1), get_mid(puts, k1)
        cp2, pp2 = (get_mid(calls, k2), get_mid(puts, k2)) if need_k2 else (0.0, 0.0)

else:
    st.markdown('<div class="price-bar">🛠️ Manual Entry Mode Active</div>', unsafe_allow_html=True)
    
    if strategy == "Custom Strategy":
        # --- MANUAL CUSTOM BUILDER ---
        st.markdown("### 🏗️ Custom Strategy Builder")
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1, 1.2, 1.2, 1.2, 2])
        c_action = c1.selectbox("Action", ["Buy", "Sell"], key="m_act")
        c_qty = c2.number_input("Qty", value=1, min_value=1, step=1, key="m_qty")
        c_type = c3.selectbox("Type", ["Call", "Put", "Stock"], key="m_type")
        c_strike = c4.number_input("Strike", value=100.0, disabled=(c_type == "Stock"), key="m_strk")
        c_price = c5.number_input("Price", value=5.0, key="m_prc")
        
        def add_manual_leg():
            st.session_state.custom_legs.append({
                "action": st.session_state.m_act, "qty": st.session_state.m_qty, "type": st.session_state.m_type,
                "strike": st.session_state.m_strk if st.session_state.m_type != "Stock" else 0,
                "price": st.session_state.m_prc, "active": True
            })
            
        c6.markdown("<br>", unsafe_allow_html=True)
        c6.button("➕ ADD POSITION", on_click=add_manual_leg, use_container_width=True)
        
        current_price = 100.0 # Default manual spot
        k1, cp1, pp1, need_k2, k2, cp2, pp2 = 100, 0, 0, False, None, 0, 0

    else:
        # --- EXISTING MANUAL LOGIC ---
        m_col1, m_col2 = st.columns(2)
        current_price = m_col1.number_input("Spot Price", value=100.0, key="m_spot")
        k1 = m_col1.number_input("Strike K1", value=100.0, key="m_k1")
        cp1 = m_col2.number_input("Call Premium K1", value=5.0, key="m_cp1")
        pp1 = m_col1.number_input("Put Premium K1", value=5.0, key="m_pp1")
        
        need_k2 = strategy in ["Long Strangle", "Short Strangle", "Bull Spread", "Bear Spread"]
        if need_k2:
            default_k2 = k1 - 5.0 if strategy == "Bear Spread" else k1 + 5.0
            k2 = m_col2.number_input("Strike K2", value=float(default_k2), key=f"manual_k2_{strategy}")
            cp2 = m_col2.number_input("Call Premium K2", value=2.0, key="m_cp2")
            pp2 = m_col1.number_input("Put Premium K2", value=2.0, key="m_pp2")
        else: k2, cp2, pp2 = None, 0.0, 0.0


# --- RENDER STRATEGY POSITIONS LIST (Applies to both Live and Manual Custom) ---
if strategy == "Custom Strategy":
    st.markdown("<hr style='margin:10px 0px; opacity:0.3'>", unsafe_allow_html=True)
    list_col1, list_col2 = st.columns([4, 1])
    list_col1.markdown("#### Strategy Positions")
    if list_col2.button("RESET LIST"):
        st.session_state.custom_legs = []
        st.rerun()

    if len(st.session_state.custom_legs) == 0:
        st.info("No positions added yet. Use the toolbar above to build your strategy.")
    else:
        for i, leg in enumerate(st.session_state.custom_legs):
            chk_col, text_col = st.columns([0.5, 4.5])
            leg['active'] = chk_col.checkbox("", value=leg['active'], key=f"chk_{i}")
            color = "#48bb78" if leg['action'] == "Buy" else "#f56565"
            qty_display = leg.get('qty', 1)
            if leg['type'] == "Stock": desc = f"<span style='color:{color}; font-weight:bold;'>{leg['action']}</span> {qty_display}x STOCK @ {currency_sym}{leg['price']}"
            else: desc = f"<span style='color:{color}; font-weight:bold;'>{leg['action']}</span> {qty_display}x {leg['strike']} {leg['type']} @ {currency_sym}{leg['price']}"
            text_col.markdown(desc, unsafe_allow_html=True)


# ================= PREMIUM DETAILS SECTION =================

if strategy != "Custom Strategy":
    st.markdown("### Premium Details")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    p_col1.metric(f"Call Leg (K1: {k1:.1f})", f"{currency_sym}{cp1:.2f}")
    p_col2.metric(f"Put Leg (K1: {k1:.1f})", f"{currency_sym}{pp1:.2f}")

    if need_k2:
        p_col3.metric(f"Call Leg (K2: {k2:.1f})", f"{currency_sym}{cp2:.2f}")
        p_col4.metric(f"Put Leg (K2: {k2:.1f})", f"{currency_sym}{pp2:.2f}")

main_layout = st.container()

# ================= REAL-TIME CURRENCY CONVERSION =================
@st.cache_data(ttl=3600) # Caches the exchange rate for 1 hour to prevent API bans
def get_exchange_rate():
    try:
        return yf.Ticker("USDINR=X").history(period="1d")["Close"].iloc[-1]
    except:
        return 83.50 # Fallback rate just in case Yahoo Finance is down

live_usd_inr = get_exchange_rate()

# Smart detection: Is the stock already in INR?
is_indian = ticker_symbol.endswith(".NS") or ticker_symbol.endswith(".BO") or ticker_symbol.startswith("^NSE")

if currency_mode == "USD ($)":
    currency_sym = "$"
    multiplier = 1.0 if not is_indian else (1.0 / live_usd_inr)
else:
    currency_sym = "₹"
    multiplier = live_usd_inr if not is_indian else 1.0

# Apply the conversion to all base variables BEFORE the math engine!
current_price *= multiplier
k1 *= multiplier
cp1 *= multiplier
pp1 *= multiplier
if need_k2:
    k2 *= multiplier
    cp2 *= multiplier
    pp2 *= multiplier
    

# ================= SPOT PRICE SIMULATOR =================

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    shift_mode = st.radio("Adjustment Mode", ["Normal ($)", "Percentage (%)"], horizontal=True)

with sim_col2:
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

elif strategy == "Custom Strategy":
    p_temp = np.zeros_like(S_temp) 
    net_premium = 0.0
    
    for leg in st.session_state.custom_legs:
        if leg.get('active', False):
            qty = leg.get('qty', 1)
            # Differentiate buy/sell impact
            direction = qty if leg['action'] == "Buy" else -qty
            
            # Apply currency conversion to custom legs
            leg_strike = leg['strike'] * multiplier
            leg_price = leg['price'] * multiplier
            
            if leg['type'] == "Call":
                leg_pnl = np.maximum(S_temp - leg_strike, 0) - leg_price
            elif leg['type'] == "Put":
                leg_pnl = np.maximum(leg_strike - S_temp, 0) - leg_price
            elif leg['type'] == "Stock":
                leg_pnl = S_temp - leg_price
                
            net_premium += -direction * leg_price
            p_temp += direction * leg_pnl
            
    gross = p_temp - net_premium
    profit = p_temp  
    is_debit = net_premium < 0

# Find Exact Breakevens
bes = []
for i in range(len(S_temp)-1):
    if p_temp[i] * p_temp[i+1] <= 0:
        be = S_temp[i] - p_temp[i]*(S_temp[i+1]-S_temp[i])/(p_temp[i+1]-p_temp[i])
        bes.append(round(be, 2))

# Final array for plotting
S = np.sort(np.unique(np.concatenate([S_temp, bes, [k1], [k2] if k2 else []])))

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
elif strategy == "Custom Strategy":
    pass # Already calculated above

# ================= PLOTLY GRAPHS LOGIC =================
def create_fig(x, y, title, label_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=np.where(y>=0, y, 0), fill='tozeroy', fillcolor='rgba(72, 187, 120, 0.3)', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=np.where(y<0, y, 0), fill='tozeroy', fillcolor='rgba(245, 101, 101, 0.3)', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=y, name=label_name, line=dict(color='#63b3ed', width=3)))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='orange', dash='dash'), name='Spot Price'))
    
    if "Profit" in title and bes:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#9f7aea', dash='dot'), name='Breakeven'))

    fig.add_vline(x=current_price, line_dash="dash", line_color="orange")
    if "Profit" in title:
        for be in bes:
            fig.add_vline(x=be, line_dash="dot", line_color="#9f7aea")

    fig.add_hline(y=0, line_color="white", line_width=2, opacity=0.8)
    
    actual_max = np.max(y)
    actual_min = np.min(y)
    y_range = actual_max - actual_min
    if y_range == 0: y_range = 10 
    y_max = actual_max + (y_range * 0.15)
    y_min = actual_min - (y_range * 0.15)
    
    if y_min >= 0: y_min = -y_max * 0.3
    if y_max <= 0: y_max = -y_min * 0.3

    fig.update_layout(
        title=f"<b>{title}</b>", template="plotly_dark", hovermode="x unified", height=550,
        xaxis_title="Stock Price at Expiry ($)", yaxis_title=f"Profit / Loss ({currency_sym})" if "Profit" in title else f"Value ({currency_sym})",
        yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='rgba(255,255,255,0.5)', range=[y_min, y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig

fig_gross = create_fig(S, gross, "Payoff Diagram (Gross Value)", "Payoff")
fig_profit = create_fig(S, profit, "Profit Diagram (Net Realized)", "Profit")

# ================= INJECTING UI INTO THE MAIN CONTAINER =================
# Now that the math is done and figures are generated, we render them in the container at the TOP.
with main_layout:
    st.markdown("---")
    # Split the layout: 1 part for metrics, 3 parts for the graph
    left_col, right_col = st.columns([1, 2.5]) 
    
    # --- VERTICAL METRICS (LEFT SIDE) ---
    # --- VERTICAL METRICS (LEFT SIDE) ---
    with left_col:
        st.markdown("### Strategy Metrics")
        st.markdown("<br>", unsafe_allow_html=True)
        
        max_p = np.max(profit)
        max_l = np.min(profit)
        profit_defined = strategy not in ["Long Straddle", "Long Strangle", "Protective Put"]
        risk_defined = strategy not in ["Short Straddle", "Short Strangle", "Covered Call"]

        st.markdown('<p class="metric-label">Max Profit</p>', unsafe_allow_html=True)
        # --- PASTE HAPPENED HERE ---
        val = f"{currency_sym}{max_p:.2f}" if profit_defined else "Undefined"
        st.markdown(f'<p class="metric-value">{val}</p><br>', unsafe_allow_html=True)

        st.markdown('<p class="metric-label">Max Loss (Risk)</p>', unsafe_allow_html=True)
        val = f"{currency_sym}{max_l:.2f}" if risk_defined else "Undefined"
        st.markdown(f'<p class="metric-value">{val}</p><br>', unsafe_allow_html=True)

        st.markdown('<p class="metric-label">Breakeven(s)</p>', unsafe_allow_html=True)
        be_val = ", ".join([f"{currency_sym}{b}" for b in bes]) if bes else "None"
        st.markdown(f'<p class="metric-value" style="font-size:24px;">{be_val}</p><br>', unsafe_allow_html=True)

        st.markdown('<p class="metric-label">Net Premium</p>', unsafe_allow_html=True)
        badge_text = "Debit" if is_debit else "Credit"
        badge_class = "badge-debit" if is_debit else "badge-credit"
        st.markdown(f'<p class="metric-value">{currency_sym}{abs(net_premium):.2f} <span class="{badge_class}" style="vertical-align: middle;">↑ {badge_text}</span></p><br>', unsafe_allow_html=True)
        # --- END OF PASTE ---

        st.markdown('<p class="metric-label">Risk : Reward</p>', unsafe_allow_html=True)
        if profit_defined and risk_defined:
            if max_l == 0:
                rr_val = "Risk-Free"
            else:
                ratio = max_p / abs(max_l)
                rr_val = f"1 : {ratio:.2f}"
        else:
            rr_val = "Undefined"
        st.markdown(f'<p class="metric-value">{rr_val}</p>', unsafe_allow_html=True)

    # --- TABBED GRAPHS (RIGHT SIDE) ---
    with right_col:
        # Create the Opstra-style tabs
        tab1, tab2 = st.tabs(["📉 PAYOFF CHART", "📊 P&L"])
        
        with tab1:
            st.plotly_chart(fig_gross, use_container_width=True)
        with tab2:
            st.plotly_chart(fig_profit, use_container_width=True)
