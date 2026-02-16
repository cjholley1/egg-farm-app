import streamlit as st
import gspread
import pandas as pd
from datetime import date
from streamlit_extras.let_it_rain import rain
import plotly.express as px
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Egg Farm Dashboard", page_icon="🥚", layout="wide")

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def get_connection():
    # If we are on the cloud, use st.secrets
    if "gcp_service_account" in st.secrets:
        # Create a dictionary from the secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Use service_account_from_dict instead of filename
        gc = gspread.service_account_from_dict(creds_dict)
    
    # If we are on your laptop, use the file
    else:
        gc = gspread.service_account(filename='credentials.json')
        
    sh = gc.open("Egg Farm Database")
    return sh

# Try to connect to the specific worksheets
try:
    sh = get_connection()
    ws_daily = sh.worksheet("Daily_Log")
    ws_sales = sh.worksheet("Sales")
    ws_flock = sh.worksheet("Flock")
    st.sidebar.success("✅ Connected to Database")
except Exception as e:
    st.sidebar.error(f"❌ Connection Error: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("🐔 Coop Control")

# 1. The Navigation
page = st.sidebar.radio("Go to", ["Dashboard", "Log Daily Data", "Log Sales", "Flock Manager", "Settings"])

st.sidebar.divider()

# 2. The "Daily Cluck" (Humor)
jokes = [
    "Why did the chicken join the band? Because it had the drumsticks!",
    "What do you call a mischievous egg? A practical yolker.",
    "How do chickens bake a cake? From scratch!",
    "Fact: Chickens can remember over 100 different faces.",
    "Fact: A hen turns her egg about 50 times a day.",
    "Why did the robot cross the road? Because the chicken programmed it!",
    "How can you drop an egg six feet without breaking it? By dropping it 7 feet.",
    "How did the egg get up the mountain? It scrambled up!",
    "Gigi Luigi from the island of Fiji! Collects the eggs again!",
    "I love you Geeg! (You too James.)",
    "Under no circumstances will I start an egg fight...",
    "I'll take my eggs 'dipped-in-toast' style.",
    "Have a great day today!",
    "You should get more chickens.",
    "When Chuck Norris wants an egg, he cracks open a chicken.",
    "Did egg prices go up again?",
    "If you kick the chickens to make them fly, Mike will be pissed!",
    "Go Navy! Beat Army!",
    "'I'll take chicken for breakfast, lunch and dinner' -Krieger"
]
todays_joke = random.choice(jokes)
st.sidebar.info(f"**The Daily Cluck:**\n\n{todays_joke}")

st.sidebar.divider()

# 3. Google Calendar "Quick Actions"
st.sidebar.header("📅 Quick Tasks")

# Helper function to make the links
def make_google_cal_link(title, location="Coop", details=""):
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    # We replace spaces with '+' for the URL
    title = title.replace(" ", "+")
    location = location.replace(" ", "+")
    details = details.replace(" ", "+")
    return f"{base}&text={title}&location={location}&details={details}"

# Button 1: Buy Feed
url_feed = make_google_cal_link("Buy Chicken Feed", "Feed Store", "Grab layer pellets and scratch grains.")
st.sidebar.link_button("🛒 Remind: Buy Feed", url_feed)

# Button 2: Vet Visit
url_vet = make_google_cal_link("Vet Visit", "Barn", "Check on the flock health.")
st.sidebar.link_button("🩺 Schedule Vet", url_vet)

# Button 3: Customer Pickup
url_cust = make_google_cal_link("Customer Pickup", "Farm Gate", "Customer coming for eggs.")
st.sidebar.link_button("🤝 Customer Meeting", url_cust)

# --- MAIN PAGE CONTENT ---
st.title("Welcome to the Egg Farm! 🚜")

if page == "Dashboard":
    st.header("📊 Farm Overview")
    
    # --- LOAD DATA ---
    # We need to get all the data to calculate stats
    daily_data = ws_daily.get_all_records()
    sales_data = ws_sales.get_all_records()
    
    # Convert to Pandas DataFrame for easier math
    df_daily = pd.DataFrame(daily_data)
    df_sales = pd.DataFrame(sales_data)
    
    # --- DATA CLEANING (Crucial Step) ---
    # Ensure dates are actual Date objects, not strings
    if not df_daily.empty:
        df_daily["Date"] = pd.to_datetime(df_daily["Date"])
        df_daily = df_daily.sort_values("Date")
    
    if not df_sales.empty:
        df_sales["Date"] = pd.to_datetime(df_sales["Date"])
        df_sales = df_sales.sort_values("Date")

    # --- CALCULATE FLOCK SIZE ---
    flock_data = ws_flock.get_all_records()
    current_flock_size = 0
    
    if flock_data:
        df_flock = pd.DataFrame(flock_data)
        # Simple loop to calculate total
        for index, row in df_flock.iterrows():
            if "Add" in row["Action"]:
                current_flock_size += row["Quantity"]
            elif "Remove" in row["Action"]:
                current_flock_size -= row["Quantity"]

    # --- CALCULATE METRICS ---
    col1, col2, col3 = st.columns(3)
    
    # Metric 1: Total Eggs (Last 7 Days)
    if not df_daily.empty:
        # Filter for last 7 days logic could go here, but let's just do "Total" for now
        total_eggs = df_daily["Eggs_Collected"].sum()
        avg_eggs = df_daily["Eggs_Collected"].mean()
        
        col1.metric("Total Eggs Collected", f"{total_eggs:,.0f} 🥚")
        col2.metric("Avg Daily Production", f"{avg_eggs:.1f} 🥚/day")
    else:
        col1.metric("Total Eggs", "0")
    
    # Metric 2: Total Revenue
    if not df_sales.empty:
        total_rev = df_sales["Total_Price"].sum() # Ensure your sheet header matches this!
        col3.metric("Total Revenue", f"${total_rev:,.2f} 💸")
    else:
        col3.metric("Revenue", "$0.00")

    col3.metric("Current Flock Size", f"{current_flock_size} 🐔")

    # --- MARKET WATCH ---
    st.divider()
    st.subheader("🥚 Market Watch")
    
    c1, c2 = st.columns(2)
    
    # 1. Fetch the price from our settings (default to $4.50 if not set)
    market_price = st.session_state.get('market_price', 4.50)
    
    c1.metric("Supermarket Price", f"${market_price:.2f}")
    
    # 2. Your Sister's Price
    # Calculate this from actual sales data? Or manual? 
    # Let's make it manual for now to keep it simple.
    my_price = 5.00 
    
    # Calculate the difference
    delta = my_price - market_price
    c2.metric("Our Price", f"${my_price:.2f}", delta=f"{delta:+.2f} vs Market", delta_color="inverse")

    st.divider()

    # --- CHARTS ---
    st.subheader("Trends")
    
    if not df_daily.empty:
        # Line Chart: Eggs over Time
        st.write("### 🥚 Egg Production History")
        # Streamlit's native line chart is simple and fast
        st.line_chart(df_daily, x="Date", y="Eggs_Collected")
    
    if not df_sales.empty:
        # Bar Chart: Sales over Time
        st.write("### 💰 Sales History")
        # We group by date to sum up sales if there were multiple in one day
        daily_sales = df_sales.groupby("Date")["Total_Price"].sum()
        st.bar_chart(daily_sales)
    
    # Show raw data for now so we know it's working
    st.subheader("Recent Daily Logs")
    data = ws_daily.get_all_records()
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.write("No data found yet.")

elif page == "Log Daily Data":
    st.header("📝 Daily Log")
    
    # The Form
    with st.form("daily_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            d_date = st.date_input("Date", value=date.today())
            eggs = st.number_input("Eggs Collected", min_value=0, step=1)
        
        with col2:
            feed = st.number_input("Feed Bags Opened", min_value=0, step=1)
            notes = st.text_input("Notes (Optional)")
            
        submitted = st.form_submit_button("Save to Sheet")
        
        if submitted:
            # Prepare the row to send to Google Sheets
            # Note: We convert date to string because JSON requires it
            row = [str(d_date), eggs, feed, notes]
            
            try:
                ws_daily.append_row(row)
                st.success("✅ Data Saved Successfully!")
                # Clear the cache so the dashboard updates immediately
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Error saving data: {e}")

elif page == "Log Sales":
    st.header("💰 Log Sales")
    
    with st.form("sales_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            s_date = st.date_input("Date", value=date.today())
            customer = st.text_input("Customer Name (or 'Cash')")
            
        with col2:
            dozens = st.number_input("Dozens Sold", min_value=1, step=1)
            price = st.number_input("Total Price ($)", min_value=0.0, step=0.5, format="%.2f")
            status = st.selectbox("Payment Status", ["Paid", "Pending"])
            
        submitted = st.form_submit_button("Record Sale")
        
        if submitted:
            # Prepare the row
            row = [str(s_date), customer, dozens, price, status]
            
            try:
                # Add to the 'Sales' worksheet
                ws_sales.append_row(row)
                st.success(f"✅ Sale recorded for {customer}!")
                rain(
    emoji="💸",
    font_size=54,
    falling_speed=5,
    animation_length=1,
)  # Fun visual reward for making money
            except Exception as e:
                st.error(f"❌ Error saving sale: {e}")

elif page == "Flock Manager":
    st.header("🐔 Flock Management")
    
    st.info("Track birds entering or leaving the farm here.")
    
    with st.form("flock_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            f_date = st.date_input("Date", value=date.today())
            action = st.selectbox("Action", ["Add Birds (+)", "Remove Birds (-)"])
        
        with col2:
            quantity = st.number_input("Quantity", min_value=1, step=1)
            reason = st.text_input("Reason (e.g., Hatchery order, Predator, Sold)")
            
        submitted = st.form_submit_button("Update Flock")
        
        if submitted:
            # We save the raw action text for clarity
            row = [str(f_date), action, quantity, reason]
            
            try:
                ws_flock.append_row(row)
                st.success(f"✅ Flock updated: {action} {quantity} birds.")
                rain(
                    emoji="🐔",
                    font_size=60,
                    falling_speed=4,
                    animation_length=2,
                )
                st.cache_data.clear() # Refresh the cache so the dashboard updates
            except Exception as e:
                st.error(f"❌ Error updating flock: {e}")
     # Show History
    st.subheader("Flock History")
    data = ws_flock.get_all_records()
    if data:
        st.dataframe(pd.DataFrame(data))
elif page == "Settings":
    st.header("⚙️ App Settings")
    
    st.subheader("Market Watch")
    # We use st.session_state to "remember" this number across pages
    if 'market_price' not in st.session_state:
        st.session_state['market_price'] = 4.50
        
    new_price = st.number_input("Current Supermarket Price ($)", value=st.session_state['market_price'])
    
    if st.button("Update Price"):
        st.session_state['market_price'] = new_price
        st.success(f"Updated Market Price to ${new_price:.2f}")