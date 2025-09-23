import streamlit as st
import pandas as pd
import ast
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Minecraft Marketplace Analytics", layout="wide")

# --- Load and preprocess data ---
@st.cache_data
def load_data():
    df = pd.read_csv("chunkgg/products.csv")  # Update path if needed

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

    # Ensure key columns exist
    required_cols = ['downloads', 'prices', 'product_name', 'publisher', 'tags']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # Convert downloads to int
    df['downloads'] = pd.to_numeric(df['downloads'], errors='coerce').fillna(0).astype(int)

    # Convert prices column (stringified dict) to dictionary
    df['price_map'] = df['prices'].apply(lambda s: ast.literal_eval(s) if pd.notnull(s) else {})

    # Process tags into list
    df['tags_list'] = df['tags'].fillna('').apply(lambda s: [t.strip() for t in s.split(',') if t.strip()])

    return df

# Load data
df = load_data()

# --- Sidebar filters ---
publishers = st.sidebar.multiselect(
    "Publisher",
    options=df['publisher'].unique(),
    default=df['publisher'].unique()
)

all_tags = sorted({tag for tags in df['tags_list'] for tag in tags})
selected_tags = st.sidebar.multiselect("Tags", options=all_tags)

currency = st.sidebar.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "AUD"])

# --- Filter data based on selections ---
d = df[df['publisher'].isin(publishers)]
if selected_tags:
    d = d[d['tags_list'].apply(lambda tags: any(t in tags for t in selected_tags))]

# --- Currency conversion ---
rates = {'USD': 1.0, 'EUR': 1.09, 'GBP': 1.27, 'CAD': 0.74, 'AUD': 0.66}

def get_price(pmap, target):
    if not pmap:
        return None
    if target in pmap:
        return float(pmap[target])
    if 'USD' in pmap:
        usd = float(pmap['USD'])
    else:
        k, v = next(iter(pmap.items()))
        usd = float(v) * rates.get(k, 1)
    return usd / rates[target]

d[f'price_{currency}'] = d['price_map'].apply(lambda p: get_price(p, currency))
d[f'revenue_{currency}'] = d['downloads'] * d[f'price_{currency}']

# --- Handle NaN values for plotting ---
d[f'revenue_{currency}'] = d[f'revenue_{currency}'].fillna(0)
d[f'price_{currency}'] = d[f'price_{currency}'].fillna(0)

# --- KPIs ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Downloads", f"{d['downloads'].sum():,}")
c2.metric(f"Total Revenue ({currency})", f"{d[f'revenue_{currency}'].sum():,.2f}")
c3.metric("Number of Products", f"{len(d)}")

# --- Top Products by Revenue ---
st.subheader("Top Products by Revenue")
top = d.sort_values(f'revenue_{currency}', ascending=False).head(10)
fig = px.bar(
    top,
    x="product_name",
    y=f'revenue_{currency}',
    color="publisher",
    hover_data=["downloads", f'price_{currency}']
)
st.plotly_chart(fig, use_container_width=True)

# --- Price vs Downloads Scatter ---
st.subheader("Price vs Downloads")
fig2 = px.scatter(
    d,
    x=f'price_{currency}',
    y="downloads",
    size=f'revenue_{currency}',
    hover_name="product_name",
    color="publisher",
    size_max=60  # max bubble size
)
st.plotly_chart(fig2, use_container_width=True)

# --- Filtered Data Table ---
st.subheader("Filtered Products Table")
st.dataframe(d[["product_name", "publisher", "downloads", f'price_{currency}', f'revenue_{currency}']])

# --- Download filtered CSV ---
csv = d.to_csv(index=False)
st.download_button(
    label="Download Filtered CSV",
    data=csv,
    file_name="filtered_products.csv",
    mime="text/csv"
)
