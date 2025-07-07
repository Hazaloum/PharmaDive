import pandas as pd

def generate_exec_summary_data(df, molecule_name):
    molecule_name = molecule_name.strip().upper()
    mol_df = df[df["Molecule Combination"].str.upper() == molecule_name].copy()

    if mol_df.empty:
        return None

    for col in ["2021 Units", "2024 Units", "2021 LC Value", "2024 LC Value"]:
        mol_df[col] = pd.to_numeric(mol_df[col], errors="coerce").fillna(0)

    mol_df["n_mols"] = mol_df["Molecule Combination"].str.count(" \+ ") + 1
    mol_df["2021 Units"] /= mol_df["n_mols"]
    mol_df["2024 Units"] /= mol_df["n_mols"]
    mol_df["2021 LC Value"] /= mol_df["n_mols"]
    mol_df["2024 LC Value"] /= mol_df["n_mols"]

    total_2024_units = mol_df["2024 Units"].sum()
    total_2024_value = mol_df["2024 LC Value"].sum()

    def compute_cagr(start, end, years=4):
        if start <= 0 or end <= 0:
            return 0.0
        return ((end / start) ** (1 / years) - 1) * 100

    unit_cagr = compute_cagr(mol_df["2021 Units"].sum(), mol_df["2024 Units"].sum())
    value_cagr = compute_cagr(mol_df["2021 LC Value"].sum(), mol_df["2024 LC Value"].sum())

    manu_2024 = mol_df.groupby("Manufacturer")["2024 LC Value"].sum()
    top_2024_manufacturer = manu_2024.idxmax()
    top_2024_share = manu_2024.max() / (total_2024_value or 1) * 100

    top3 = manu_2024.sort_values(ascending=False).head(3)
    top3_dict = {k: round(v / (total_2024_value or 1) * 100, 1) for k, v in top3.items()}

    above_3_pct = (manu_2024 / (total_2024_value or 1) * 100 >= 3).sum()

    manu_2021 = mol_df.groupby("Manufacturer")["2021 LC Value"].sum()
    top_2021_manufacturer = manu_2021.idxmax()
    top_2021_share = manu_2021.max() / (mol_df["2021 LC Value"].sum() or 1) * 100

    if top_2021_manufacturer == top_2024_manufacturer:
        change = top_2024_share - top_2021_share
        erosion_summary = f"{top_2021_share:.1f}% → {top_2024_share:.1f}% ({'📈 Gained' if change > 0 else '📉 Lost'} {abs(change):.1f} pts)"
    else:
        erosion_summary = f"{top_2021_manufacturer} ({top_2021_share:.1f}%) → {top_2024_manufacturer} ({top_2024_share:.1f}%)"

    # NEW: Get top product and its launch year
    top_manu_df = mol_df[mol_df["Manufacturer"] == top_2024_manufacturer]
    top_product_row = top_manu_df.sort_values("2024 LC Value", ascending=False).head(1)
    top_product_name = top_product_row["Product"].values[0] if not top_product_row.empty else "Unknown"
    top_product_launch_year = int(top_product_row["Launch Year"].values[0]) if not top_product_row.empty else None

    private_df = mol_df[mol_df["Market"] == "PRIVATE MARKET"]
    lpo_df = mol_df[mol_df["Market"] == "LPO"]

    private_2021_units = private_df["2021 Units"].sum()
    private_2024_units = private_df["2024 Units"].sum()
    private_cagr = compute_cagr(private_2021_units, private_2024_units)

    lpo_2021_units = lpo_df["2021 Units"].sum()
    lpo_2024_units = lpo_df["2024 Units"].sum()
    lpo_cagr = compute_cagr(lpo_2021_units, lpo_2024_units)

    private_pct = private_2024_units / (total_2024_units or 1) * 100
    lpo_pct = lpo_2024_units / (total_2024_units or 1) * 100

    forecast_units = {}
    forecast_value = {}
    for i, year in enumerate(range(2025, 2030), 1):
        forecast_units[year] = int(total_2024_units * ((1 + unit_cagr / 100) ** i))
        forecast_value[year] = int(total_2024_value * ((1 + value_cagr / 100) ** i))

    df_clean = df.copy()
    df_clean[["2021 Units", "2024 Units", "2021 LC Value", "2024 LC Value"]] = df_clean[
        ["2021 Units", "2024 Units", "2021 LC Value", "2024 LC Value"]
    ].apply(pd.to_numeric, errors="coerce").fillna(0)

    atc4_code = mol_df["ATC4"].dropna().unique()[0]
    atc3_code = mol_df["ATC3"].dropna().unique()[0]

    atc4_df = df_clean[df_clean["ATC4"] == atc4_code]
    atc3_df = df_clean[df_clean["ATC3"] == atc3_code]

    def get_class_metrics(subdf):
        return {
            "value_2024": subdf["2024 LC Value"].sum(),
            "unit_cagr": compute_cagr(subdf["2021 Units"].sum(), subdf["2024 Units"].sum()),
            "value_cagr": compute_cagr(subdf["2021 LC Value"].sum(), subdf["2024 LC Value"].sum())
        }

    def pretty_list(values):
        return ", ".join(sorted(set(values))) if len(values) > 0 else "N/A"

    return {
        "molecule": molecule_name,
        "total_sales": total_2024_value,
        "total_units": total_2024_units,
        "unit_cagr": unit_cagr,
        "value_cagr": value_cagr,
        "top_2024_manufacturer": top_2024_manufacturer,
        "top_2024_share": top_2024_share,
        "originator_share_change": erosion_summary,
        "unique_manufacturers": mol_df["Manufacturer"].nunique(),
        "private_pct": private_pct,
        "lpo_pct": lpo_pct,
        "private_cagr": private_cagr,
        "lpo_cagr": lpo_cagr,
        "top3_manufacturers": top3_dict,
        "manufacturers_above_3_pct": above_3_pct,
        "atc1": pretty_list(mol_df["ATC1"].dropna().unique()),
        "atc2": pretty_list(mol_df["ATC2"].dropna().unique()),
        "atc3": pretty_list(mol_df["ATC3"].dropna().unique()),
        "atc4": pretty_list(mol_df["ATC4"].dropna().unique()),
        "forecast_units": forecast_units,
        "forecast_value": forecast_value,
        "atc4_metrics": get_class_metrics(atc4_df),
        "atc3_metrics": get_class_metrics(atc3_df),
        "top_product": top_product_name,
        "top_product_launch_year": top_product_launch_year
    }
