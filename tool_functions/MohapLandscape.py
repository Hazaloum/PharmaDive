import pandas as pd
import streamlit as st
import re

def clean_ingredient_string(text):
    text = re.sub(r"\(.*?\)", "", str(text))  # Remove content in parentheses
    text = text.replace(",", "").strip().upper()
    return text

def format_registered_products_by_company(molecule_name: str, mohap_df: pd.DataFrame):
    molecule_name_clean = clean_ingredient_string(molecule_name)

    # --- Clean and normalize relevant columns ---
    mohap_df["Ingredient"] = mohap_df["Ingredient"].astype(str)
    mohap_df["Ingredient_clean"] = mohap_df["Ingredient"].apply(clean_ingredient_string)
    mohap_df["Trade Name"] = mohap_df["Trade Name"].astype(str).str.strip()
    mohap_df["Form"] = mohap_df["Form"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    mohap_df["Strength"] = mohap_df["Strength"].astype(str).str.strip()
    mohap_df["Company"] = mohap_df["Company"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    mohap_df["Agent"] = mohap_df["Agent"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    # --- Match logic ---
    matched = mohap_df[mohap_df["Ingredient_clean"].str.contains(molecule_name_clean, na=False)]

    if matched.empty:
        st.warning(f"❌ No registered MOHAP products found for: **{molecule_name}**")
        return

    matched["Public Price (AED)"] = pd.to_numeric(matched["Public Price (AED)"], errors="coerce")

    # --- Originator logic ---
    try:
        company_prices = matched.groupby("Company")["Public Price (AED)"].sum().sort_values(ascending=False)
        likely_originator = company_prices.idxmax()
        originator_price_total = company_prices.max()
    except:
        likely_originator = "Unknown"
        originator_price_total = 0

    st.markdown(f"🎯 **Likely Originator:** `{likely_originator}` (Total Public Price: **AED {originator_price_total:,.0f}**)")

    # --- Clean subset ---
    subset = matched[[
        "Trade Name", "Strength", "Form", "Company",
        "Source", "Agent", "Public Price (AED)", "Ingredient"
    ]].fillna("Unknown").drop_duplicates()

    st.markdown(f"📦 **Registered MOHAP Products for:** `{molecule_name}`")
    for company, group in subset.groupby("Company"):
        st.markdown(f"\n#### 🏭 Company: `{company}`")
        for _, row in group.iterrows():
            st.markdown(
                f"- **{row['Trade Name']}** — {row['Strength']} {row['Form']} — 💰 AED {row['Public Price (AED)']} — 🧾 Agent: {row['Agent']} — 🧪 Ingredient: {row['Ingredient']}"
            )

    # --- CIF Price Prediction ---
    st.markdown("---")
    st.markdown("💰 **Predicted CIF Pricing Based on Originator Packs:**")
    originator_df = subset[subset["Company"] == likely_originator].copy()

    if originator_df.empty:
        st.markdown("❌ No valid originator packs to predict from.")
    else:
        for _, row in originator_df.iterrows():
            try:
                public_price = float(row["Public Price (AED)"])
                cif_price = round((public_price / 1.4) * 0.4, 2)
                st.markdown(
                    f"- 🧪 **{row['Trade Name']}** — {row['Strength']} {row['Form']} → Predicted CIF: **AED {cif_price}** (from AED {public_price})"
                )
            except:
                continue

    st.markdown("---")
    st.markdown(f"📊 **Summary:** {subset['Trade Name'].nunique()} unique products across {subset['Company'].nunique()} manufacturers.")