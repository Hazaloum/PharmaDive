import pandas as pd
import streamlit as st

def display_patent_summary(products_df, patents_df, ingredient_name):
    ingredient_name = ingredient_name.strip().upper()

    df_match = products_df[
        products_df["Ingredient_Formatted_Clean"] == ingredient_name
    ].copy()

    if df_match.empty:
        st.warning(f"❌ No data found for ingredient: `{ingredient_name}`")
        return

    df_match = df_match[df_match["Appl_Type"] == "N"]
    if df_match.empty:
        st.warning(f"📭 No NDA (originator) products found for: `{ingredient_name}`")
        return

    merged = pd.merge(df_match, patents_df, how="left", on=["Appl_No", "Product_No"])
    merged["Patent_Expire_Date_Text"] = pd.to_datetime(
        merged["Patent_Expire_Date_Text"], errors='coerce'
    )

    grouped = merged.groupby(["DF;Route", "Applicant"])

    st.markdown(f"## 🧪 Orange Book NDA Summary for `{ingredient_name}`")
    for (uptake, applicant), group in grouped:
        latest_expiry = group["Patent_Expire_Date_Text"].max()
        products = group["Trade_Name"].dropna().unique()
        products_list = ", ".join(sorted(products))
        
        st.markdown(f"---")
        st.markdown(f"### 💉 Dosage Form : `{uptake}`")
        st.markdown(f"- 🏢 **Applicant**: `{applicant}`")
        st.markdown(f"- 🧾 **Products**: {products_list}")
        st.markdown(f"- 📅 **Latest Patent Expiry**: `{latest_expiry.date() if pd.notnull(latest_expiry) else 'Unknown'}`")