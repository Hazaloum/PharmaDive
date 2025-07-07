import streamlit as st
import pandas as pd

from tool_functions.combinations      import create_combination_column
from tool_functions.summary           import generate_molecule_overview
from tool_functions.PacksAndProducts  import generate_combination_first_clean_summary
from tool_functions.MohapLandscape    import format_registered_products_by_company
from tool_functions.MoleculePlot      import plot_combination_market_breakdown_plotly
from tool_functions.MoleculeATC4      import plotly_combinations_within_atc4_go
#from tool_functions.OrangeBook import generate_uptake_patent_view
from tool_functions.SummaryGen import generate_exec_summary_data
from tool_functions.MarketShare import plot_manufacturer_market_share
from tool_functions.Erosion import plot_market_erosion
from tool_functions.OrangeBook import display_patent_summary
from tool_functions.Reg import get_regulatory_summary

# --- Load Master Data ---
@st.cache_data
def load_master_data():
    df = pd.read_csv("Master Data.csv")
    df = create_combination_column(df)
    df.columns = df.columns.str.replace("\n", " ", regex=False).str.strip()
    for c in df.columns:
        if "Value" in c or "Units" in c:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.strip(),
                errors="coerce"
            )
    return df

# --- Load MOHAP Data ---
@st.cache_data
def load_mohap_data():
    mohap_df = pd.read_csv("PriceListMOHAP.csv")
    mohap_df.columns = mohap_df.columns.str.replace("\n", " ", regex=False).str.strip()


    return mohap_df


# --- Load data ---
df = load_master_data()
mohap_df = load_mohap_data()

# --- UI ---
st.title("💊 UAE Molecule Intelligence Platform")

# Shared molecule selector
selected_combo = st.selectbox(
    "🔎 Search Molecule:",
    sorted(df["Molecule Combination"].dropna().unique())
)

# Tabs
tab1a, tab1b, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Exec Summary",
    "📈 Graph + Table",
    "🔍 ATC4 Breakdown",
    "📋 Summary + Packs",
    "🏛️ MOHAP Insights",
    "📅 Patent Expiry Finder",
    "📉 Erosion & Uptake"
])
# === Tab 1: Molecule-Level Market Breakdown ===
# === Tab 1A: Executive Summary ===
with tab1a:
    st.subheader("🧬 Executive Summary")

    summary = generate_exec_summary_data(df, selected_combo)

    # Block 1: Sales & Growth
    st.markdown("### 💰 Sales & Growth")
    col1, col2, col3 = st.columns(3)
    col1.metric("2024 Sales (AED)", f"{summary['total_sales']:,.0f}")
    col2.metric("2024 Units", f"{summary['total_units']:,.0f}")
    col3.metric("Unique Manufacturers", summary['unique_manufacturers'])
    
    col4, col5 = st.columns(2)
    col4.metric("CAGR (Units)", f"{summary['unit_cagr']:.1f}%")
    col5.metric("CAGR (Value)", f"{summary['value_cagr']:.1f}%")
    
    # 👉 New: Predicted Revenue
    st.markdown("#### 📈 Predict Your Entry Revenue")
    entry_pct = st.number_input("🔢 Expected Market Capture (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.5)
    adjusted_cif_price = (summary["total_sales"] / 1.4) * 0.4
    predicted_revenue = adjusted_cif_price * (entry_pct / 100)
    
    st.metric("💡 Predicted Revenue (AED)", f"{predicted_revenue:,.0f}")
    
    st.divider()

   # Block 2: Market Leaders
    st.markdown("### 🥇 Market Leaders")
    col6, col7 = st.columns(2)
    col6.metric("Top Manufacturer", summary['top_2024_manufacturer'])
    col7.metric("Market Share", f"{summary['top_2024_share']:.1f}%")
    
    st.markdown(f"**Originator Value Share Change:** {summary['originator_share_change']}")
    st.markdown(f"**Top 3 Manufacturers:**")
    for manu, share in summary["top3_manufacturers"].items():
        st.markdown(f"- `{manu}` → {share:.1f}%")
    
    st.markdown(f"**# Manufacturers >3% Share**: `{summary['manufacturers_above_3_pct']}`")
    
    # 👉 New: Top product and launch year
    st.markdown(f"**Top Product (from {summary['top_2024_manufacturer']}):** `{summary['top_product']}`")
    if summary['top_product_launch_year']:
        st.markdown(f"**Launch Year:** `{summary['top_product_launch_year']}`")
    
    st.divider()

    # Block 3: Market Split
    st.markdown("### 🏪 Market Split")
    col8, col9 = st.columns(2)
    col8.metric("Private Market", f"{summary['private_pct']:.1f}%")
    col9.metric("LPO Market", f"{summary['lpo_pct']:.1f}%")

    col10, col11 = st.columns(2)
    col10.metric("Private CAGR (Units)", f"{summary['private_cagr']:.1f}%")
    col11.metric("LPO CAGR (Units)", f"{summary['lpo_cagr']:.1f}%")

    st.divider()

    # Block 4: ATC Classification
    st.markdown("### 🧬 ATC Classification")
    st.markdown(f"""
    - **ATC1**: {summary['atc1']}  
    - **ATC2**: {summary['atc2']}  
    - **ATC3**: {summary['atc3']}  
    - **ATC4**: {summary['atc4']}
    """)

    st.divider()

    # Block 5: 📈 5-Year Forecast
    st.markdown("### 📈 Market Forecast (2025–2029)")

    forecast_table = pd.DataFrame({
        "Year": list(summary["forecast_units"].keys()),
        "Forecasted Units": list(summary["forecast_units"].values()),
        "Forecasted Value (AED)": list(summary["forecast_value"].values())
    })

    st.dataframe(forecast_table, use_container_width=True)

    st.caption("🔮 Based on historical CAGR from 2021–2024. These values are simple forecasts and assume trend continuation.")

    st.divider()

    # Block 6: 🧬 Class Overview
    st.markdown("### 🧬 Class Overview (2024)")

    class_table = pd.DataFrame([
        {
            "Level": "ATC4",
            "2024 Value (AED)": f"{summary['atc4_metrics']['value_2024']:,.0f}",
            "CAGR (Value)": f"{summary['atc4_metrics']['value_cagr']:.1f}%",
            "CAGR (Units)": f"{summary['atc4_metrics']['unit_cagr']:.1f}%"
        },
        {
            "Level": "ATC3",
            "2024 Value (AED)": f"{summary['atc3_metrics']['value_2024']:,.0f}",
            "CAGR (Value)": f"{summary['atc3_metrics']['value_cagr']:.1f}%",
            "CAGR (Units)": f"{summary['atc3_metrics']['unit_cagr']:.1f}%"
        }
    ])
    st.dataframe(class_table, use_container_width=True)
    
        # Block 4: Regulatory Snapshot
    st.markdown("### 📜 Regulatory Snapshot")

        # --- Load Data ---
    ob_products = pd.read_csv("OBproducts.csv")
    ob_patents  = pd.read_csv("OBpatents.csv")

        # --- Clean Orange Book product data ---
    ob_products.columns = ob_products.columns.str.strip()
    ob_products["Ingredient"] = ob_products["Ingredient"].astype(str).str.upper().str.strip()
    ob_products["Ingredient_List"] = ob_products["Ingredient"].str.split(";")
    ob_products["Ingredient_Formatted"] = ob_products["Ingredient_List"].apply(lambda x: " +".join(x))
    ob_products["Ingredient_Formatted_Clean"] = ob_products["Ingredient_Formatted"].str.strip().str.upper()

    reg_data = get_regulatory_summary(selected_combo, mohap_df, ob_products, ob_patents)

    colA, colB = st.columns(2)
    colA.metric("MOHAP Registered Manufacturers", reg_data["mohap_manufacturers"])
    colB.metric("Orange Book Latest Expiry", str(reg_data["orange_book_expiry"]))

    st.markdown(f"**Search logic**: includes any ingredient that contains the term `{selected_combo.upper()}`.")
    st.divider()
with tab1b:
    st.subheader("🧪 Molecule-Level Market Breakdown")

    plot_market = st.radio(
        "Market Type:",
        ["PRIVATE MARKET", "LPO", "TOTAL (PRIVATE + LPO)"],
        horizontal=True
    )
    plot_metric = st.radio(
        "Metric:",
        ["Units", "Value"],
        horizontal=True
    )
    group_by_column = st.radio(
        "Group By:",
        ["Manufacturer", "Product", "Strength"],
        horizontal=True
    )

    use_value         = (plot_metric == "Value")
    use_market_filter = (plot_market != "TOTAL (PRIVATE + LPO)")
    market_type_pass  = plot_market

    fig_mol, mol_summary = plot_combination_market_breakdown_plotly(
        df,
        selected_molecule=selected_combo,
        use_market_filter=use_market_filter,
        market_type=market_type_pass,
        use_value=use_value,
        group_by_column=group_by_column
    )
    if fig_mol:
        st.plotly_chart(fig_mol, use_container_width=True)
        st.subheader("🔢 2024 Manufacturer Summary")
        st.dataframe(mol_summary)
    else:
        st.warning("⚠️ No molecule-level data to show for that selection.")


    show_share_plot = st.toggle("📈 Show Market Share Line Chart")
    
    if show_share_plot:
        share_market_type = "TOTAL" if not use_market_filter else market_type_pass
        fig_share = plot_manufacturer_market_share(df, selected_molecule=selected_combo, market_type=share_market_type)
    
        if fig_share:
            st.plotly_chart(fig_share, use_container_width=True)
        else:
            st.warning("⚠️ Not enough data to show market share trends.")

# === Tab 2: ATC4 Breakdown ===
with tab2:
    st.subheader("🔍 ATC4 Market Breakdown")

    atc4_name = df.loc[
        df["Molecule Combination"] == selected_combo,
        "ATC4"
    ].dropna().unique()[0]

    fig_atc4, atc4_summary = plotly_combinations_within_atc4_go(
        df,
        atc4_name=atc4_name,
        UseValue=use_value
    )
    if fig_atc4:
        st.plotly_chart(fig_atc4, use_container_width=True)
        st.subheader("🔢 2024 ATC4 Summary")
        st.dataframe(atc4_summary)
    else:
        st.warning("⚠️ No ATC4 data to show for that molecule.")

# === Tab 3: Summary + Packs ===
with tab3:
    st.subheader("📋 Molecule Summary and Pack Overview")

    summary_df = generate_molecule_overview(df, selected_combo)
    if summary_df is not None:
        st.table(summary_df)
    else:
        st.warning(f"❌ No summary data for '{selected_combo}'")

    st.markdown("---")
    packs_md = generate_combination_first_clean_summary(df, selected_combo)
    st.markdown(packs_md)

# === Tab 4: MOHAP Insights ===
with tab4:
    st.subheader("🏛️ MOHAP Registered Product Landscape")

    mohap_ingredient = st.selectbox(
        "🔎 Search by Ingredient (MOHAP):",
        sorted(mohap_df["Ingredient"].dropna().unique())
    )

    mohap_markdown = format_registered_products_by_company(mohap_ingredient, mohap_df)
    st.markdown(mohap_markdown)
    # Sanitize Ingredient column
    mohap_df["Ingredient_clean"] = mohap_df["Ingredient"].astype(str).str.upper().str.strip()
    
    # Show unique values that include DAPAGLIFLOZIN
    matches = mohap_df[mohap_df["Ingredient_clean"].str.contains("DAPAGLIFLOZIN", na=False)]
    
    st.write("DAPAGLIFLOZIN Matches", matches[["Ingredient", "Ingredient_clean"]].drop_duplicates())

with tab5:
    st.subheader("📅 Orange Book Patent Expiry Lookup")

    # --- Load Data ---
    ob_products = pd.read_csv("OBproducts.csv")
    ob_patents  = pd.read_csv("OBpatents.csv")

    # --- Clean Orange Book product data ---
    ob_products.columns = ob_products.columns.str.strip()
    ob_products["Ingredient"] = ob_products["Ingredient"].astype(str).str.upper().str.strip()
    ob_products["Ingredient_List"] = ob_products["Ingredient"].str.split(";")
    ob_products["Ingredient_Formatted"] = ob_products["Ingredient_List"].apply(lambda x: " +".join(x))
    ob_products["Ingredient_Formatted_Clean"] = ob_products["Ingredient_Formatted"].str.strip().str.upper()

    # --- Dropdown selection ---
    selected_ingredient = st.selectbox(
        "🔎 Select Ingredient Combination:",
        sorted(ob_products["Ingredient_Formatted_Clean"].dropna().unique())
    )

    # --- Display patent summary in exec style ---
    display_patent_summary(ob_products, ob_patents, selected_ingredient)

with tab6:
    st.subheader("📉 Originator Erosion & Uptake Curve")

    with st.spinner("Analyzing erosion and plotting uptake..."):
        try:
            fig, erosion_summary = plot_market_erosion(df.copy(), selected_combo)

            if fig:
                st.plotly_chart(fig, use_container_width=True)

            if erosion_summary:
                st.markdown(f"""
### 📉 **Originator Erosion for `{selected_combo.upper()}`**
- **2021 Market Share:** {erosion_summary['originator_2021']:.2%}  
- **2024 Market Share:** {erosion_summary['originator_2024']:.2%}  
- **Drop:** {erosion_summary['drop']:.2f}%

---

### 📊 **ATC4 Erosion Benchmark – `{erosion_summary['atc4_code']}`**
- **Average Erosion Across ATC4:** {erosion_summary['average_atc4_erosion']:.2f}%  
- **Avg Originator Share in 2021:** {erosion_summary['avg_originator_2021']:.2%}  
- **Avg Originator Share in 2024:** {erosion_summary['avg_originator_2024']:.2%}
                """)
        except Exception as e:
            st.error(f"An error occurred: {e}")