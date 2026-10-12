#!/usr/bin/env python3
"""
Regenerate Map 1 (all legacy DSI records) with a blue-white-red diverging color scale.
White = midpoint, blue = below average, red = above average.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

OUTPUT_DIR = "/Users/jasminekindness/IIFB_COP17/ahteg_allocation"

# ── Load data ──────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(OUTPUT_DIR, "insdc_provenance_country_maps.csv"))
df = df[df['iso3'].notna() & (df['iso3'] != '') & (df['iso3'] != '---')].copy()

# Use log10 of record counts so the color scale isn't dominated by USA alone
df['log_all'] = df['ena_all'].apply(lambda x: np.log10(x) if x > 0 else 0)

# Set midpoint: median of countries that have data, so white = typical country
countries_with_data = df[df['ena_all'] > 0]
midpoint_log = countries_with_data['log_all'].median()
zmin = 0
zmax = countries_with_data['log_all'].max()

# Blue-white-red diverging colorscale
# Plotly colorscale takes normalized 0-1 positions; we need to map the midpoint
mid_norm = (midpoint_log - zmin) / (zmax - zmin)

COLOR_SCALE_BWR = [
    [0.0, '#2166ac'],        # dark blue (lowest)
    [mid_norm * 0.3, '#4393c3'],
    [mid_norm * 0.6, '#92c5de'],
    [mid_norm * 0.85, '#d1e5f0'],
    [mid_norm, '#f7f7f7'],   # white (median)
    [mid_norm + (1 - mid_norm) * 0.15, '#fddbc7'],
    [mid_norm + (1 - mid_norm) * 0.4, '#f4a582'],
    [mid_norm + (1 - mid_norm) * 0.7, '#d6604d'],
    [1.0, '#b2182b'],        # dark red (highest)
]

LAND_COLOR = '#f0f0f0'
OCEAN_COLOR = '#d9d9d9'

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
plot_data = df[df['ena_all'] > 0].copy()

fig.add_trace(go.Choropleth(
    locations=plot_data['iso3'],
    z=plot_data['log_all'],
    colorscale=COLOR_SCALE_BWR,
    zmin=zmin,
    zmax=zmax,
    marker_line_color='#ffffff',
    marker_line_width=0.3,
    colorbar=dict(
        title=dict(
            text="DSI Records<br>(log₁₀ scale)",
            font=dict(size=12),
        ),
        tickfont=dict(size=11),
        len=0.6,
        x=1.01,
        tickvals=[0, midpoint_log, zmax],
        ticktext=[
            f"0",
            f"~{int(10**midpoint_log):,}",
            f"~{int(10**zmax):,}",
        ],
    ),
    hovertemplate=(
        '<b>%{text}</b><br>'
        'Records: %{customdata:,.0f}<br>'
        '<extra></extra>'
    ),
    text=plot_data['country'],
    customdata=plot_data['ena_all'],
    hoverinfo='text+z',
))

fig.update_layout(
    title=dict(
        text=(
            '<b>All Non-Human DSI Records with Country Provenance</b><br>'
            '<sup style="font-size:13px;color:#666">'
            'INSDC / ENA sample database &bull; 26.7 million records &bull; '
            f'white = median country (~{int(10**midpoint_log):,} records) &bull; accessed 8 October 2026'
            '</sup>'
        ),
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
    margin=dict(l=0, r=0, t=90, b=0),
    paper_bgcolor='#ffffff',
    font=dict(family='Helvetica, Arial, sans-serif', size=12, color='#333'),
)

path = os.path.join(OUTPUT_DIR, "map1_all_legacy_records.html")
fig.write_html(path, include_plotlyjs='cdn')
print(f"Saved: {path}")
print(f"Median country (white midpoint): ~{int(10**midpoint_log):,} records (log10={midpoint_log:.2f})")
print(f"Range: 0 to ~{int(10**zmax):,} records (log10={zmax:.2f})")
