import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Constants for each hotel's Green Champion
GREEN_CHAMPIONS = {
    'Camden': {
        'name': 'Chinmay', 
        'role': 'Front Office Manager',
        'image': 'images/champions/chinmay.jpg'
    },
    'Canopy': {
        'name': 'Lucyna', 
        'role': 'Front Office Manager',
        'image': 'images/champions/lucyna.jpg'
    },
    'Westin': {
        'name': 'Jekaterina & Gayatri', 
        'role': 'Front Office Manager',
        'image': 'images/champions/westin.jpg'
    },
    'St Albans': {
        'name': 'Suleman', 
        'role': 'Front Office Manager',
        'image': 'images/champions/suleman.jpg'
    },
    'CIV': {
        'name': 'Sufyan', 
        'role': 'Front Office Manager',
        'image': 'images/champions/sufyan.jpg'
    },
    'CIE': {
        'name': 'Asina', 
        'role': 'Front Office Manager',
        'image': 'images/champions/asina.jpg'
    },
    'EH': {
        'name': 'Roxana', 
        'role': 'Front Office Manager',
        'image': 'images/champions/roxana.jpg'
    }
}

from pathlib import Path
import os

def load_champion_image(image_path):
    """Load champion image with fallback to placeholder"""
    if os.path.exists(image_path):
        return image_path
    return "images/placeholder.jpg"

def load_data():
    """Load and prepare all data"""
    # Create image directories if they don't exist
    Path("images/champions").mkdir(parents=True, exist_ok=True)
    Path("images/logos").mkdir(parents=True, exist_ok=True)
    try:
        # Load all required data
        waste_df = pd.read_csv('data/waste.csv')
        electricity_df = pd.read_csv('data/elec.csv')
        water_df = pd.read_csv('data/water.csv')
        occupancy_df = pd.read_csv('data/occ_sleepers.csv')

        # Convert dates
        for df in [waste_df, electricity_df, water_df, occupancy_df]:
            df['Month'] = pd.to_datetime(df['Month'], format='%d/%m/%Y')

        # Convert occupancy percentage
        occupancy_df['Occupancy Rate'] = occupancy_df['Occupancy Rate'].str.rstrip('%').astype(float) / 100

        return {
            'waste': waste_df,
            'electricity': electricity_df,
            'water': water_df,
            'occupancy': occupancy_df
        }
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def calculate_guest_impact(data, selected_hotel):
    """Calculate per-guest impact metrics for selected hotel"""
    try:
        # Get latest month's data
        latest_month = data['waste']['Month'].max()
        
        # Filter for selected hotel
        hotel_waste = data['waste'][data['waste']['Hotel'] == selected_hotel]
        hotel_water = data['water'][['Month', selected_hotel]]
        hotel_electricity = data['electricity'][['Month', selected_hotel]]
        hotel_occupancy = data['occupancy'][data['occupancy']['Hotel'] == selected_hotel]
        
        # Calculate water savings per guest
        current_month_water = hotel_water[hotel_water['Month'] == latest_month][selected_hotel].sum()
        prev_year_water = hotel_water[hotel_water['Month'] == (latest_month - pd.DateOffset(years=1))][selected_hotel].sum()
        
        current_month_occ = hotel_occupancy[hotel_occupancy['Month'] == latest_month]['Sleepers'].sum()
        prev_year_occ = hotel_occupancy[hotel_occupancy['Month'] == (latest_month - pd.DateOffset(years=1))]['Sleepers'].sum()
        
        # Calculate water per guest
        current_water_per_guest = current_month_water / current_month_occ if current_month_occ > 0 else 0
        prev_water_per_guest = prev_year_water / prev_year_occ if prev_year_occ > 0 else 0
        
        water_saved_per_guest = max(0, (prev_water_per_guest - current_water_per_guest))
        
        # Calculate energy savings (CO2)
        current_energy = hotel_electricity[hotel_electricity['Month'] == latest_month][selected_hotel].sum()
        prev_year_energy = hotel_electricity[hotel_electricity['Month'] == (latest_month - pd.DateOffset(years=1))][selected_hotel].sum()
        
        current_energy_per_guest = current_energy / current_month_occ if current_month_occ > 0 else 0
        prev_energy_per_guest = prev_year_energy / prev_year_occ if prev_year_occ > 0 else 0
        
        # Convert kWh to CO2 (using 0.233 kg CO2/kWh)
        co2_saved_per_guest = max(0, (prev_energy_per_guest - current_energy_per_guest) * 0.233)
        
        # Get latest recycling rate for hotel
        latest_recycling = hotel_waste[hotel_waste['Month'] == latest_month]['Recycling Rates'].mean()
        recycling_target = 0.50  # 50% target
        
        # Calculate food waste reduction
        current_food_waste = hotel_waste[hotel_waste['Month'] == latest_month]['Food Waste'].mean()
        prev_food_waste = hotel_waste[hotel_waste['Month'] == (latest_month - pd.DateOffset(months=1))]['Food Waste'].mean()
        food_waste_reduction = max(0, (prev_food_waste - current_food_waste))
        
        return {
            'water_saved': water_saved_per_guest,
            'co2_saved': co2_saved_per_guest,
            'recycling_rate': latest_recycling,
            'recycling_target': recycling_target,
            'food_saved': food_waste_reduction,
            'month': latest_month.strftime('%B %Y')
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return None

def show_guest_display():
    """Main function to show guest sustainability display"""
    # Page config
    st.set_page_config(page_title="Hotel Sustainability Display", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .green-header {
            color: #006B3E;  /* Holiday Inn green */
            text-align: center;
            padding: 1rem;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }
        .hotel-select {
            max-width: 300px;
            margin: 0 auto;
        }
        div[data-testid="stSelectbox"] {
            margin: 0 auto;
            max-width: 300px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    if not data:
        return

    # Get list of hotels
    hotels = sorted(data['waste']['Hotel'].unique())
    
    # Hotel selector in center
    st.markdown('<div class="hotel-select">', unsafe_allow_html=True)
    selected_hotel = st.selectbox('Select Hotel', hotels)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate metrics for selected hotel
    metrics = calculate_guest_impact(data, selected_hotel)
    if not metrics:
        return
    
    # Header with hotel name
    st.markdown(f"""
        <h1 class="green-header">Your Green Stay at {selected_hotel}</h1>
        <p style='text-align: center; font-size: 1.2rem; color: #666;'>
            Together we're making a difference - {metrics['month']}
        </p>
    """, unsafe_allow_html=True)
    
    # Guest Impact Section
    st.markdown("### Your Stay Makes a Difference")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #006B3E;'>{metrics['water_saved']:.0f}L Water Saved</h3>
            <p>By reusing your towels</p>
            <h4>= {(metrics['water_saved']/75):.1f} days of drinking water</h4>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #006B3E;'>{metrics['co2_saved']:.1f}kg CO₂ Prevented</h3>
            <p>Using your key card for power</p>
            <h4>= {(metrics['co2_saved']*4):.1f} miles not driven</h4>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='color: #006B3E;'>{metrics['food_saved']*1000:.0f}g Food Saved</h3>
            <p>Through portion control</p>
            <h4>= {(metrics['food_saved']*1000/400):.1f} meals saved</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Hotel Journey
    st.markdown("### Our Green Journey")
    
    # Create 2x2 grid for progress cards
    col1, col2 = st.columns(2)
    
    with col1:
        # Energy Progress
        energy_progress = 0.80  # Example: 80% progress
        st.markdown("""
        <div style='padding: 1rem; background: white; border-radius: 0.5rem; margin: 0.5rem;'>
            <h4>⚡ Energy Reduction</h4>
        """, unsafe_allow_html=True)
        st.progress(energy_progress)
        st.markdown(f"**{energy_progress*100:.0f}%** progress to our 15% reduction goal")
    
    with col2:
        # Recycling Progress
        recycling_progress = metrics['recycling_rate'] / metrics['recycling_target']
        st.markdown("""
        <div style='padding: 1rem; background: white; border-radius: 0.5rem; margin: 0.5rem;'>
            <h4>♻️ Recycling Rate</h4>
        """, unsafe_allow_html=True)
        st.progress(min(recycling_progress, 1.0))
        st.markdown(f"**{metrics['recycling_rate']*100:.0f}%** recycled (Target: {metrics['recycling_target']*100:.0f}%)")
    
    # Meet Your Green Champion
    if selected_hotel in GREEN_CHAMPIONS:
        champion = GREEN_CHAMPIONS[selected_hotel]
        st.markdown("### Meet Your Green Champion")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            champion_image = load_champion_image(champion['image'])
            st.image(champion_image, width=150)
            
        with col2:
            st.markdown(f"""
            **Hi, I'm {champion['name']}!**
            
            As your Green Champion and {champion['role']} at {selected_hotel}, I'm here to help make your stay both 
            comfortable and environmentally friendly. Together, we can make a difference!
            
            Feel free to ask me about our sustainability initiatives or share your eco-friendly ideas!
            """)

if __name__ == "__main__":
    show_guest_display()