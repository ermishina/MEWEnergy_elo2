#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Generate visualizations from actual API response data
Processes geocode, PVWatts, and utility rate API results

Usage:
    python generate_visualizations.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import json
import numpy as np

# Set style for professional-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 100

def load_api_data():
    """Load and process API response files"""
    
    # Load geocode results
    with open('raw/geocode_results.json', 'r') as f:
        geocode_data = json.load(f)
    
    # Load PVWatts results
    with open('raw/pvwatts_results.json', 'r') as f:
        pvwatts_data = json.load(f)
    
    # Load utility rates
    with open('raw/utility_rates_results.json', 'r') as f:
        rates_data = json.load(f)
    
    # Combine into analysis-ready dataframe
    records = []
    
    for pv_record in pvwatts_data['data']:
        location_id = pv_record['id']
        
        # Get corresponding rate data
        rate_record = next((r for r in rates_data['data'] if r['id'] == location_id), None)
        
        # Extract PVWatts outputs
        if pv_record['pvwatts']['success']:
            pv_outputs = pv_record['pvwatts']['outputs']
            solar_outputs = pv_record['solar_resource']['outputs']
            
            record = {
                'id': location_id,
                'region': pv_record['region'],
                'address': pv_record['input_address'],
                'lat': pv_record['lat'],
                'lon': pv_record['lon'],
                
                # Solar resource data
                'avg_dni': solar_outputs['avg_dni']['annual'],
                'avg_ghi': solar_outputs['avg_ghi']['annual'],
                'avg_lat_tilt': solar_outputs['avg_lat_tilt']['annual'],
                
                # PVWatts outputs
                'ac_annual': pv_outputs['ac_annual'],
                'capacity_factor': pv_outputs['capacity_factor'],
                'system_capacity_kw': 5.0,  # From metadata
                
                # Monthly data
                'ac_monthly': pv_outputs['ac_monthly'],
                
                # Utility rate
                'electricity_rate': None,
                'utility_name': None,
                'state': None,
                'srec_price': 0.0
            }
            
            # Add rate data if available
            if rate_record and 'residential' in rate_record['rates']:
                res_rate = rate_record['rates']['residential']
                if res_rate['success']:
                    record['electricity_rate'] = res_rate['rate']
                    record['utility_name'] = res_rate['utility_name']
                    record['state'] = rate_record.get('state')
                    record['srec_price'] = rate_record.get('srec_price', 0.0)
            
            records.append(record)
    
    df = pd.DataFrame(records)
    
    print(f"✓ Loaded {len(df)} locations with complete data")
    print(f"  Regions: {', '.join(df['region'].unique())}")
    print(f"  States: {', '.join(df['state'].dropna().unique())}")
    
    return df


def create_irradiance_by_region(df, output_dir):
    """Solar irradiance comparison by region"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # DNI by region
    df.boxplot(column='avg_dni', by='region', ax=axes[0])
    axes[0].set_title('Direct Normal Irradiance by Region')
    axes[0].set_xlabel('Region')
    axes[0].set_ylabel('DNI (kWh/m²/day)')
    axes[0].get_figure().suptitle('')  # Remove default title
    
    # GHI by region
    df.boxplot(column='avg_ghi', by='region', ax=axes[1])
    axes[1].set_title('Global Horizontal Irradiance by Region')
    axes[1].set_xlabel('Region')
    axes[1].set_ylabel('GHI (kWh/m²/day)')
    axes[1].get_figure().suptitle('')
    
    # Capacity factor by region
    df.boxplot(column='capacity_factor', by='region', ax=axes[2])
    axes[2].set_title('System Capacity Factor by Region')
    axes[2].set_xlabel('Region')
    axes[2].set_ylabel('Capacity Factor (%)')
    axes[2].get_figure().suptitle('')
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'irradiance_by_region.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_production_map(df, output_dir):
    """Geographic scatter plot of annual production"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create scatter plot with production as color
    scatter = ax.scatter(df['lon'], df['lat'], 
                        c=df['ac_annual'], 
                        s=df['ac_annual']/20,  # Size by production
                        cmap='YlOrRd', 
                        alpha=0.7, 
                        edgecolors='black', 
                        linewidth=1.5)
    
    # Add location labels
    for idx, row in df.iterrows():
        ax.annotate(row['id'], 
                   (row['lon'], row['lat']),
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Annual AC Production (kWh)', rotation=270, labelpad=20)
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Annual Solar Production by Location\n(5 kW System)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'production_geographic_map.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_seasonal_comparison(df, output_dir):
    """Monthly production comparison across locations"""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Plot each location
    for idx, row in df.iterrows():
        ax.plot(range(12), row['ac_monthly'], 
               marker='o', linewidth=2, label=row['id'],
               alpha=0.8, markersize=6)
    
    ax.set_xticks(range(12))
    ax.set_xticklabels(months)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('AC Production (kWh)', fontsize=12)
    ax.set_title('Monthly Solar Production Comparison\nAcross US Regions (5 kW System)', 
                fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'seasonal_production_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_irradiance_vs_latitude(df, output_dir):
    """Relationship between latitude and solar irradiance"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # GHI vs Latitude
    axes[0].scatter(df['lat'], df['avg_ghi'], s=150, alpha=0.7, 
                   c='#FF6B35', edgecolors='black', linewidth=1.5)
    
    # Add trend line
    z = np.polyfit(df['lat'], df['avg_ghi'], 2)
    p = np.poly1d(z)
    x_trend = np.linspace(df['lat'].min(), df['lat'].max(), 100)
    axes[0].plot(x_trend, p(x_trend), 'r--', linewidth=2, alpha=0.8, label='Trend (quadratic)')
    
    # Add location labels
    for idx, row in df.iterrows():
        axes[0].annotate(row['id'], (row['lat'], row['avg_ghi']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    axes[0].set_xlabel('Latitude (degrees)', fontsize=11)
    axes[0].set_ylabel('Average GHI (kWh/m²/day)', fontsize=11)
    axes[0].set_title('Solar Irradiance vs. Latitude', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Annual Production vs Latitude
    axes[1].scatter(df['lat'], df['ac_annual'], s=150, alpha=0.7,
                   c='#4CAF50', edgecolors='black', linewidth=1.5)
    
    # Add trend line
    z2 = np.polyfit(df['lat'], df['ac_annual'], 2)
    p2 = np.poly1d(z2)
    axes[1].plot(x_trend, p2(x_trend), 'r--', linewidth=2, alpha=0.8, label='Trend (quadratic)')
    
    # Add location labels
    for idx, row in df.iterrows():
        axes[1].annotate(row['id'], (row['lat'], row['ac_annual']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    axes[1].set_xlabel('Latitude (degrees)', fontsize=11)
    axes[1].set_ylabel('Annual AC Production (kWh)', fontsize=11)
    axes[1].set_title('Energy Production vs. Latitude', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'latitude_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_electricity_rates_comparison(df, output_dir):
    """Compare electricity rates across locations"""
    # Filter to locations with rate data
    df_rates = df[df['electricity_rate'].notna()].copy()
    
    if len(df_rates) == 0:
        print("⚠ No electricity rate data available")
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort by rate for better visualization
    df_rates = df_rates.sort_values('electricity_rate')
    
    colors = ['#4CAF50' if r < 0.12 else '#FF9800' if r < 0.14 else '#F44336' 
              for r in df_rates['electricity_rate']]
    
    bars = ax.barh(range(len(df_rates)), df_rates['electricity_rate'], 
                   color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_yticks(range(len(df_rates)))
    ax.set_yticklabels([f"{row['id']} ({row['state']})" for _, row in df_rates.iterrows()])
    ax.set_xlabel('Electricity Rate ($/kWh)', fontsize=12)
    ax.set_title('Residential Electricity Rates by Location', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (idx, row) in enumerate(df_rates.iterrows()):
        ax.text(row['electricity_rate'] + 0.002, i, 
               f"${row['electricity_rate']:.4f}/kWh",
               va='center', fontsize=9)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', label='< $0.12/kWh'),
        Patch(facecolor='#FF9800', label='$0.12-$0.14/kWh'),
        Patch(facecolor='#F44336', label='> $0.14/kWh')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'electricity_rates_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_srec_analysis(df, output_dir):
    """Analyze SREC availability and pricing"""
    df_srec = df[df['srec_price'] > 0].copy()
    
    if len(df_srec) == 0:
        print("⚠ No SREC data available (expected - only 2 of 8 locations have active SREC programs)")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort by SREC price
    df_srec = df_srec.sort_values('srec_price', ascending=False)
    
    bars = ax.bar(range(len(df_srec)), df_srec['srec_price'],
                 color='#9C27B0', edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_xticks(range(len(df_srec)))
    ax.set_xticklabels([f"{row['id']}\n({row['state']})" for _, row in df_srec.iterrows()])
    ax.set_ylabel('SREC Price ($/MWh)', fontsize=12)
    ax.set_title('Solar Renewable Energy Certificate (SREC) Pricing by State', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, (idx, row) in enumerate(df_srec.iterrows()):
        ax.text(i, row['srec_price'] + 10, 
               f"${row['srec_price']:.0f}/MWh",
               ha='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'srec_pricing_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_summary_statistics(df, output_dir):
    """Generate summary statistics table"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare statistics for each location
    table_data = []
    headers = ['Location', 'Region', 'State', 'GHI\n(kWh/m²/day)', 
               'Annual\nProduction\n(kWh)', 'Capacity\nFactor\n(%)',
               'Electricity\nRate\n($/kWh)', 'SREC\n($/MWh)']
    
    for idx, row in df.iterrows():
        table_data.append([
            row['id'],
            row['region'][:12],  # Truncate long names
            row['state'] if row['state'] else 'N/A',
            f"{row['avg_ghi']:.2f}",
            f"{row['ac_annual']:,.0f}",
            f"{row['capacity_factor']:.1f}",
            f"{row['electricity_rate']:.4f}" if row['electricity_rate'] else 'N/A',
            f"${row['srec_price']:.0f}" if row['srec_price'] > 0 else 'None'
        ])
    
    table = ax.table(cellText=table_data,
                    colLabels=headers,
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2.5)
    
    # Style header row
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor('#A31F34')
        cell.set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#F5F5F5')
            else:
                cell.set_facecolor('#FFFFFF')
    
    plt.title('Solar System Analysis - Location Summary\n5 kW PV System (Standard Module, Fixed Roof Mount)', 
             fontsize=14, weight='bold', pad=20)
    
    output_path = Path(output_dir) / 'location_summary_table.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def create_performance_metrics_summary(df, output_dir):
    """Create summary of key performance metrics"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Annual production distribution
    axes[0, 0].hist(df['ac_annual'], bins=8, color='#4CAF50', 
                   edgecolor='black', alpha=0.7)
    axes[0, 0].axvline(df['ac_annual'].mean(), color='red', 
                      linestyle='--', linewidth=2,
                      label=f'Mean: {df["ac_annual"].mean():,.0f} kWh')
    axes[0, 0].set_xlabel('Annual AC Production (kWh)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Annual Production Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Capacity factor distribution
    axes[0, 1].hist(df['capacity_factor'], bins=8, color='#2196F3',
                   edgecolor='black', alpha=0.7)
    axes[0, 1].axvline(df['capacity_factor'].mean(), color='red',
                      linestyle='--', linewidth=2,
                      label=f'Mean: {df["capacity_factor"].mean():.1f}%')
    axes[0, 1].set_xlabel('Capacity Factor (%)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Capacity Factor Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # GHI distribution
    axes[1, 0].hist(df['avg_ghi'], bins=8, color='#FF9800',
                   edgecolor='black', alpha=0.7)
    axes[1, 0].axvline(df['avg_ghi'].mean(), color='red',
                      linestyle='--', linewidth=2,
                      label=f'Mean: {df["avg_ghi"].mean():.2f} kWh/m²/day')
    axes[1, 0].set_xlabel('Average GHI (kWh/m²/day)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Solar Irradiance Distribution')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Production vs GHI correlation
    axes[1, 1].scatter(df['avg_ghi'], df['ac_annual'], s=150,
                      c='#9C27B0', edgecolors='black', linewidth=1.5, alpha=0.7)
    
    # Add trend line
    z = np.polyfit(df['avg_ghi'], df['ac_annual'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(df['avg_ghi'].min(), df['avg_ghi'].max(), 100)
    axes[1, 1].plot(x_trend, p(x_trend), 'r--', linewidth=2, alpha=0.8,
                   label=f'R² = {np.corrcoef(df["avg_ghi"], df["ac_annual"])[0,1]**2:.3f}')
    
    axes[1, 1].set_xlabel('Average GHI (kWh/m²/day)')
    axes[1, 1].set_ylabel('Annual AC Production (kWh)')
    axes[1, 1].set_title('Production vs Solar Resource')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.suptitle('Solar System Performance Metrics Summary\n5 kW PV System Across US Regions',
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = Path(output_dir) / 'performance_metrics_summary.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("Solar Energy Data Visualization Generator")
    print("Processing Real API Data")
    print("="*60 + "\n")
    
    # Setup output directory
    output_dir = Path('visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}\n")
    
    # Load and process data
    print("Loading API data...")
    try:
        df = load_api_data()
    except FileNotFoundError as e:
        print(f"\n✗ Error: Required data file not found")
        print(f"  {e}")
        print("\nPlease ensure these files are in the current directory:")
        print("  - geocode_results.json")
        print("  - pvwatts_results.json")
        print("  - utility_rates_results.json")
        return 1
    
    print(f"\n{'='*60}")
    print("Generating visualizations...")
    print("="*60 + "\n")
    
    try:
        create_irradiance_by_region(df, output_dir)
        create_production_map(df, output_dir)
        create_seasonal_comparison(df, output_dir)
        create_irradiance_vs_latitude(df, output_dir)
        create_electricity_rates_comparison(df, output_dir)
        create_srec_analysis(df, output_dir)
        create_summary_statistics(df, output_dir)
        create_performance_metrics_summary(df, output_dir)
        
        print("\n" + "="*60)
        print("✓ All visualizations generated successfully!")
        print(f"Location: {output_dir.absolute()}")
        print("="*60 + "\n")
        
        # List generated files
        print("Generated files:")
        for viz_file in sorted(output_dir.glob('*.png')):
            print(f"  • {viz_file.name}")
        
        print(f"\nTotal: {len(list(output_dir.glob('*.png')))} visualizations\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())