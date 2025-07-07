import pandas as pd
import plotly.graph_objects as go

def plotly_combinations_within_atc4_go(df, atc4_name, UseValue=True, years=None):
    # --- Defaults ---
    if years is None:
        years = ["2021", "2022", "2023", "2024"]
    metric_label = "Value (AED)" if UseValue else "Units"

    # --- Clean columns ---
    df = df.copy()
    df.columns = df.columns.str.replace("\n", " ", regex=False).str.strip()

    # --- Raw columns ---
    unit_cols  = [f"{y} Units"    for y in years]
    value_cols = [f"{y} LC Value" for y in years]
    metric_cols = value_cols if UseValue else unit_cols

    # --- Filter to ATC4 ---
    df_f = df[df["ATC4"] == atc4_name].copy()
    if df_f.empty:
        return None, None

    # --- Numeric conversion ---
    for c in unit_cols + value_cols:
        df_f[c] = pd.to_numeric(df_f[c], errors="coerce").fillna(0)

    # --- Group & sum ---
    grp_units  = df_f.groupby("Molecule Combination")[unit_cols].sum()
    grp_values = df_f.groupby("Molecule Combination")[value_cols].sum()
    grp_metric = grp_values if UseValue else grp_units

    # --- Totals & share ---
    total_units  = grp_units.sum()
    total_values = grp_values.sum()
    total_metric = total_values if UseValue else total_units
    total_metric[total_metric == 0] = 1e-9
    pct_share = grp_metric.divide(total_metric, axis=1) * 100
    pct_share = pct_share.fillna(0).round(1)

    # --- Build bar chart ---
    fig = go.Figure()
    for combo in grp_metric.index:
        y_raw = [grp_metric.at[combo, col] for col in metric_cols]
        y_pct = [pct_share.at[combo, col] for col in metric_cols]

        # remove suffix for x-axis
        x_years = [c.split()[0] for c in metric_cols]

        fig.add_trace(go.Bar(
            name=combo,
            x=x_years,
            y=y_raw,
            customdata=y_pct,
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                f"{metric_label}: " + "%{y:,.0f}<br>"
                "Market Share: %{customdata:.1f}%<extra></extra>"
            )
        ))

    fig.update_layout(
        barmode="stack",
        title=f"Combination Breakdown — {atc4_name} ({years[0]}–{years[-1]})",
        xaxis_title="Year",
        yaxis_title=metric_label,
        legend_title="Combination",
        height=600,
        width=1000
    )

    # --- Build summary DataFrame ---
    def compute_cagr(start, end, n_years=4):
        if start <= 0 or pd.isna(start) or pd.isna(end):
            return 0.0
        return ((end / start) ** (1/n_years) - 1) * 100

    rows = []
    for combo in grp_metric.index:
        u_end = int(grp_units.at[combo, f"{years[-1]} Units"])
        v_end = int(grp_values.at[combo, f"{years[-1]} LC Value"])
        u_share = pct_share.at[combo, f"{years[-1]} LC Value"] if UseValue else pct_share.at[combo, f"{years[-1]} Units"]
        v_share = pct_share.at[combo, f"{years[-1]} LC Value"] if UseValue else pct_share.at[combo, f"{years[-1]} Units"]
        u_cagr = compute_cagr(grp_units.at[combo, f"{years[0]} Units"], u_end)
        v_cagr = compute_cagr(grp_values.at[combo, f"{years[0]} LC Value"], v_end)
        rows.append({
            "Combination": combo,
            f"{years[-1]} Units": u_end,
            f"{years[-1]} Value (AED)": v_end,
            "Share (%)": round(v_share if UseValue else u_share, 1),
            "Units CAGR (%)": round(u_cagr,1),
            "Value CAGR (%)": round(v_cagr,1)
        })

    summary_df = pd.DataFrame(rows)\
                   .sort_values(by=f"{years[-1]} {'Value (AED)' if UseValue else 'Units'}", ascending=False)\
                   .reset_index(drop=True)

    return fig, summary_df