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
    
    # Custom CSS for enhanced visual engagement
    st.markdown("""
        <style>
        /* Base styles with enhanced visuals */
        .green-header {
            color: #006B3E;
            text-align: center;
            padding: 1rem;
            font-size: calc(1.5rem + 1vw);
            margin-bottom: 0.5rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        .subtitle {
            font-size: calc(0.8rem + 0.5vw);
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f5f7f6);
            padding: 1.8rem;
            border-radius: 1.5rem;
            box-shadow: 5px 5px 15px rgba(0,107,62,0.1),
                       -5px -5px 15px rgba(255,255,255,0.8);
            text-align: center;
            height: 100%;
            transition: all 0.3s ease;
            border: 1px solid rgba(0,107,62,0.1);
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 8px 8px 20px rgba(0,107,62,0.15),
                       -8px -8px 20px rgba(255,255,255,0.9);
            border: 1px solid rgba(0,107,62,0.2);
        }
        .metric-card h3 {
            color: #006B3E;
            font-size: calc(1.3rem + 0.5vw);
            margin-bottom: 0.8rem;
            background: linear-gradient(45deg, #006B3E, #2E8B57);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .metric-card p {
            font-size: calc(0.9rem + 0.2vw);
            color: #555;
            margin: 0.7rem 0;
            line-height: 1.5;
        }
        .metric-card h4 {
            color: #444;
            font-size: calc(0.85rem + 0.2vw);
            margin-top: 1rem;
            padding: 0.5rem;
            background: rgba(0,107,62,0.05);
            border-radius: 1rem;
        }
        .hotel-select {
            max-width: min(300px, 90vw);
            margin: 1.5rem auto;
            background: white;
            padding: 0.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0,107,62,0.1);
        }
        
        /* Progress card with enhanced styling */
        .progress-card {
            background: linear-gradient(145deg, #ffffff, #f5f7f6);
            padding: 1.8rem;
            border-radius: 1.5rem;
            box-shadow: 5px 5px 15px rgba(0,107,62,0.1),
                       -5px -5px 15px rgba(255,255,255,0.8);
            margin: 0.8rem 0;
            border: 1px solid rgba(0,107,62,0.1);
            transition: all 0.3s ease;
        }
        .progress-card:hover {
            box-shadow: 8px 8px 20px rgba(0,107,62,0.15),
                       -8px -8px 20px rgba(255,255,255,0.9);
        }
        .progress-card h4 {
            font-size: calc(1.1rem + 0.3vw);
            margin-bottom: 1.2rem;
            color: #006B3E;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Champion card with enhanced styling */
        .champion-card {
            background: linear-gradient(145deg, #f8faf9, #ffffff);
            padding: 2rem;
            border-radius: 1.5rem;
            margin-top: 2rem;
            box-shadow: 5px 5px 15px rgba(0,107,62,0.1),
                       -5px -5px 15px rgba(255,255,255,0.8);
            border: 1px solid rgba(0,107,62,0.1);
            transition: all 0.3s ease;
        }
        .champion-card:hover {
            box-shadow: 8px 8px 20px rgba(0,107,62,0.15),
                       -8px -8px 20px rgba(255,255,255,0.9);
        }
        .champion-card img {
            border-radius: 50%;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border: 3px solid #006B3E;
            transition: transform 0.3s ease;
        }
        .champion-card img:hover {
            transform: scale(1.05);
        }
        
        /* Section headers with enhanced styling */
        .section-header {
            color: #006B3E;
            font-size: calc(1.2rem + 0.4vw);
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(0,107,62,0.1);
            text-align: center;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .metric-card {
                margin-bottom: 1.2rem;
            }
            .progress-card {
                margin: 0.8rem 0;
            }
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
        }
        
        /* Progress bar enhancement */
        div[role="progressbar"] {
            border-radius: 1rem;
            height: 0.8rem !important;
            background: rgba(0,107,62,0.1);
        }
        div[role="progressbar"] > div {
            background: linear-gradient(90deg, #006B3E, #2E8B57) !important;
            border-radius: 1rem;
            transition: width 1s ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    if not data:
        return

    # Get list of hotels
    hotels = sorted(data['waste']['Hotel'].unique())
    
    # Hotel selector in center without the box
    selected_hotel = st.selectbox('Select Hotel', hotels)
    
    # Calculate metrics for selected hotel
    metrics = calculate_guest_impact(data, selected_hotel)
    if not metrics:
        return
    
    # Header with hotel name
    st.markdown(f"""
        <h1 class="green-header">Your Green Stay at</h1>
        <h2 class="green-header" style="margin-top: -1rem;">{selected_hotel}</h2>
        <p class="subtitle">
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
    
    # Create responsive grid for progress cards
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Energy Progress
        energy_progress = 0.80  # Example: 80% progress
        st.markdown("""
        <div class="progress-card">
            <h4>⚡ Energy Reduction</h4>
        """, unsafe_allow_html=True)
        st.progress(energy_progress)
        st.markdown(f"**{energy_progress*100:.0f}%** progress to our 15% reduction goal")
    
    with col2:
        # Recycling Progress
        recycling_progress = metrics['recycling_rate'] / metrics['recycling_target']
        st.markdown("""
        <div class="progress-card">
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