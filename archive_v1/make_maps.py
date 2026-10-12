#!/usr/bin/env python3
"""
Generate choropleth maps from INSDC provenance data for the Cali Fund assessment.
Produces three individual maps + one combined comparison figure, all as standalone HTML.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

OUTPUT_DIR = "/Users/jasminekindness/IIFB_COP17/ahteg_allocation"

# ── Load data ──────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(OUTPUT_DIR, "insdc_provenance_country_maps.csv"))

# Filter out non-country entries (oceans, territories, unmapped)
df = df[df['iso3'].notna() & (df['iso3'] != '') & (df['iso3'] != '---')].copy()

# Use log scale for color since the data spans orders of magnitude
df['ena_all_log'] = df['ena_all'].apply(lambda x: 0 if x <= 0 else x)
df['ena_post2023_log'] = df['ena_post2023'].apply(lambda x: 0 if x <= 0 else x)
df['ena_env_log'] = df['ena_env'].apply(lambda x: 0 if x <= 0 else x)

# Development status labels
df['status_label'] = df['dev_status'].fillna('Unmapped')

# ── Shared layout settings ─────────────────────────────────────────
COLOR_SCALE = [
    [0, '#f7fbff'],       # near-zero: very light
    [0.1, '#deebf7'],
    [0.2, '#c6dbef'],
    [0.3, '#9ecae1'],
    [0.4, '#6baed6'],
    [0.5, '#4292c6'],
    [0.6, '#2171b5'],
    [0.7, '#08519c'],
    [0.8, '#08306b'],
    [1.0, '#051030'],     # highest: very dark blue
]

OCEAN_COLOR = '#d9d9d9'
LAND_COLOR = '#f0f0f0'
BG_COLOR = '#ffffff'

def make_choropleth(data, values_col, title, subtitle, filename, colorbar_title):
    """Create a single choropleth map."""
    fig = go.Figure()

    # Base layer: all countries in light grey
    fig.add_trace(go.Choropleth(
        locations=df['iso3'],
        z=[0] * len(df),
        colorscale=[[0, LAND_COLOR], [1, LAND_COLOR]],
        showscale=False,
        marker_line_color='#ffffff',
        marker_line_width=0.3,
        hoverinfo='skip',
    ))

    # Data layer
    plot_data = data[data[values_col] > 0].copy()

    fig.add_trace(go.Choropleth(
        locations=plot_data['iso3'],
        z=plot_data[values_col],
        colorscale=COLOR_SCALE,
        reversescale=False,
        marker_line_color='#ffffff',
        marker_line_width=0.3,
        colorbar=dict(
            title=colorbar_title,
            tickfont=dict(size=11),
            title_font=dict(size=12),
            len=0.6,
            x=1.01,
        ),
        hovertemplate=(
            '<b>%{text}</b><br>'
            'Records: %{z:,.0f}<br>'
            '<extra></extra>'
        ),
        text=plot_data['country'],
        hoverinfo='text+z',
    ))

    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b><br><sup style="font-size:13px;color:#666">{subtitle}</sup>',
            x=0.5,
            y=0.95,
            font=dict(size=18, color='#222'),
        ),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor='#cccccc',
            coastlinewidth=0.5,
            projection_type='natural earth',
            landcolor=LAND_COLOR,
            oceancolor=OCEAN_COLOR,
            showocean=True,
            showlakes=False,
            lataxis_showgrid=False,
            lonaxis_showgrid=False,
        ),
        margin=dict(l=0, r=0, t=80, b=0),
        paper_bgcolor=BG_COLOR,
        font=dict(family='Helvetica, Arial, sans-serif', size=12, color='#333'),
    )

    path = os.path.join(OUTPUT_DIR, filename)
    fig.write_html(path, include_plotlyjs='cdn')
    print(f"Saved: {path}")
    return fig


# ── Map 1: All legacy records ──────────────────────────────────────
make_choropleth(
    df, 'ena_all_log',
    "All Non-Human DSI Records with Country Provenance",
    "INSDC / ENA sample database &bull; 26.7 million records &bull; accessed 8 October 2026",
    "map1_all_legacy_records.html",
    "Records (log scale)"
)

# ── Map 2: Post-2023 records ───────────────────────────────────────
make_choropleth(
    df, 'ena_post2023_log',
    "Post-2023 Non-Human DSI Records (first_public &ge; 2024-01-01)",
    "INSDC / ENA &bull; 6.8 million records &bull; developing-country share risen to 40.7%",
    "map2_post2023_records.html",
    "Records (log scale)"
)

# ── Map 3: Environmental samples ───────────────────────────────────
make_choropleth(
    df, 'ena_env_log',
    "Environmentally Sourced DSI Records with Country Provenance",
    "INSDC / ENA &bull; environmental_sample=true &bull; 125,405 records (0.5% of total)",
    "map3_environmental_records.html",
    "Records (log scale)"
)

# ── Combined 3-panel figure ────────────────────────────────────────
fig_combined = make_subplots(
    rows=3, cols=1,
    subplot_titles=[
        "<b>Map 1: All legacy DSI records with provenance (26.7M)</b>",
        "<b>Map 2: Post-2023 DSI records (6.8M) — developing share 40.7%</b>",
        "<b>Map 3: Environmentally sourced DSI records (125K)</b>",
    ],
    specs=[[{"type": "choropleth"}],
           [{"type": "choropleth"}],
           [{"type": "choropleth"}]],
    vertical_spacing=0.08,
)

# Add each map as a subplot
for i, (col, _) in enumerate([
    ('ena_all_log', 'All Records'),
    ('ena_post2023_log', 'Post-2023'),
    ('ena_env_log', 'Environmental'),
], start=1):
    plot_data = df[df[col] > 0].copy()

    # Base grey layer
    fig_combined.add_trace(
        go.Choropleth(
            locations=df['iso3'],
            z=[0] * len(df),
            colorscale=[[0, LAND_COLOR], [1, LAND_COLOR]],
            showscale=False,
            marker_line_color='#ffffff',
            marker_line_width=0.3,
            hoverinfo='skip',
        ),
        row=i, col=1,
    )

    # Data layer
    fig_combined.add_trace(
        go.Choropleth(
            locations=plot_data['iso3'],
            z=plot_data[col],
            colorscale=COLOR_SCALE,
            marker_line_color='#ffffff',
            marker_line_width=0.3,
            colorbar=dict(
                title="Records",
                tickfont=dict(size=9),
                title_font=dict(size=10),
                len=0.25,
                x=1.01,
                y=1 - (i - 1) / 3 - 0.12,
            ),
            hovertemplate='<b>%{text}</b><br>Records: %{z:,.0f}<extra></extra>',
            text=plot_data['country'],
            hoverinfo='text+z',
        ),
        row=i, col=1,
    )

fig_combined.update_layout(
    title=dict(
        text=('<b>INSDC Provenance Country Maps for the Cali Fund</b><br>'
              '<sup style="font-size:12px;color:#666">Non-human DSI sample records with country provenance &bull; '
              'ENA portal API &bull; accessed 8 October 2026</sup>'),
        x=0.5,
        font=dict(size=20, color='#222'),
    ),
    margin=dict(l=0, r=0, t=120, b=20),
    paper_bgcolor=BG_COLOR,
    font=dict(family='Helvetica, Arial, sans-serif', size=11, color='#333'),
    height=1200,
)

# Update geo for all subplots
for i in range(1, 4):
    fig_combined.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor='#cccccc',
        coastlinewidth=0.4,
        projection_type='natural earth',
        landcolor=LAND_COLOR,
        oceancolor=OCEAN_COLOR,
        showocean=True,
        lataxis_showgrid=False,
        lonaxis_showgrid=False,
        row=i, col=1,
    )

combined_path = os.path.join(OUTPUT_DIR, "insdc_provenance_combined_maps.html")
fig_combined.write_html(combined_path, include_plotlyjs='cdn')
print(f"Saved: {combined_path}")

# ── Map 4: Developing country share comparison ─────────────────────
# Show post-2023 as % of all records to highlight growth
df_growth = df[df['ena_all'] > 0].copy()
df_growth['growth_pct'] = 100 * df_growth['ena_post2023'] / df_growth['ena_all']

fig_growth = go.Figure()

fig_growth.add_trace(go.Choropleth(
    locations=df_growth['iso3'],
    z=df_growth['ena_all'].apply(lambda x: 0 if x <= 0 else 1),
    colorscale=[[0, LAND_COLOR], [1, LAND_COLOR]],
    showscale=False,
    marker_line_color='#ffffff',
    marker_line_width=0.3,
    hoverinfo='skip',
))

# Only show countries with >= 1000 total records
df_growth_filtered = df_growth[df_growth['ena_all'] >= 1000].copy()

GROWTH_COLORS = [
    [0, '#fff5f0'],
    [0.15, '#fee0d2'],
    [0.3, '#fcbba1'],
    [0.45, '#fc9272'],
    [0.6, '#ef3b2c'],
    [0.75, '#cb181d'],
    [0.9, '#a50f15'],
    [1.0, '#67000d'],
]

fig_growth.add_trace(go.Choropleth(
    locations=df_growth_filtered['iso3'],
    z=df_growth_filtered['growth_pct'],
    colorscale=GROWTH_COLORS,
    marker_line_color='#ffffff',
    marker_line_width=0.3,
    zmin=0, zmax=80,
    colorbar=dict(
        title="% Post-2023<br>(of all records)",
        tickfont=dict(size=11),
        title_font=dict(size=12),
        len=0.6,
        x=1.01,
    ),
    hovertemplate=(
        '<b>%{text}</b><br>'
        'Post-2023 share: %{z:.1f}%<br>'
        '<extra></extra>'
    ),
    text=df_growth_filtered['country'],
    hoverinfo='text+z',
))

fig_growth.update_layout(
    title=dict(
        text=('<b>Post-2023 Growth Rate: Share of DSI Records Published Since 2024</b><br>'
              '<sup style="font-size:13px;color:#666">Countries with &ge; 1,000 total records &bull; '
              'Higher = faster recent growth &bull; Developing countries shown in red</sup>'),
        x=0.5,
        y=0.95,
        font=dict(size=18, color='#222'),
    ),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor='#cccccc',
        coastlinewidth=0.5,
        projection_type='natural earth',
        landcolor=LAND_COLOR,
        oceancolor=OCEAN_COLOR,
        showocean=True,
        lataxis_showgrid=False,
        lonaxis_showgrid=False,
    ),
    margin=dict(l=0, r=0, t=90, b=0),
    paper_bgcolor=BG_COLOR,
    font=dict(family='Helvetica, Arial, sans-serif', size=12, color='#333'),
)

growth_path = os.path.join(OUTPUT_DIR, "map4_post2023_growth_rate.html")
fig_growth.write_html(growth_path, include_plotlyjs='cdn')
print(f"Saved: {growth_path}")

print("\nAll maps generated successfully.")
