import streamlit as st
import time
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os
import sys
import logging
from textblob import TextBlob
import plotly.express as px

# Import functions from your existing script
from amazon_searcher import (
    setup_chrome_driver,
    find_lowest_price_product,
    AmazonReviewScraper
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Amazon Product Finder & Review Analyzer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF9900;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #232F3E;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #F9F9F9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .positive {
        color: #2E7D32;
        font-weight: bold;
    }
    .negative {
        color: #C62828;
        font-weight: bold;
    }
    .neutral {
        color: #757575;
        font-weight: bold;
    }
    .verdict {
        font-size: 1.5rem;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
        font-weight: bold;
    }
    .verdict-buy {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .verdict-dont-buy {
        background-color: #FFEBEE;
        color: #C62828;
    }
    .verdict-neutral {
        background-color: #F5F5F5;
        color: #757575;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        color: #757575;
        font-size: 0.8rem;
    }
    .product-card {
        border: 1px solid #DDD;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .lowest-price-highlight {
        border: 2px solid #FF9900;
        background-color: #FFF8E1;
    }
    .price-tag {
        color: #B12704;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .lowest-price-label {
        background-color: #FF9900;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🛒 Amazon Product Finder & Review Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Find the lowest priced products and analyze review sentiment</p>", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Amazon_icon.svg", width=100)
    st.markdown("### Settings")
    
    # Search settings
    st.markdown("#### Search Configuration")
    max_products = st.slider("Maximum products to display", 5, 20, 10)
    
    # Review settings
    st.markdown("#### Review Analysis")
    max_review_pages = st.slider("Maximum review pages to scrape", 1, 5, 2)
    
    # Advanced options (collapsible)
    with st.expander("Advanced Options"):
        wait_time = st.slider("Page load wait time (seconds)", 2, 10, 5)
        debug_mode = st.checkbox("Enable debug mode", False)
    
    st.markdown("---")
    st.markdown("### How to use")
    st.markdown("""
    1. Enter product name in the search box
    2. Click 'Search Amazon' button
    3. Review all extracted products
    4. The lowest-priced product is highlighted
    5. Select a product to analyze reviews
    6. View sentiment analysis and verdict
    """)

# Modified function to display all products first, then highlight the lowest price one
def display_products(products):
    if not products:
        st.warning("No products found. Try a different search term.")
        return
    
    # Display all products in a data table first
    st.markdown("<h2 class='sub-header'>🔍 All Products Found</h2>", unsafe_allow_html=True)
    
    # Create a DataFrame for better display
    df = pd.DataFrame(products, columns=["Title", "Price (₹)", "Link"])
    
    # Format the DataFrame
    df_display = df.copy()
    df_display["Price (₹)"] = df_display["Price (₹)"].apply(lambda x: f"₹{x:,.2f}")
    
    # Display as a table
    st.dataframe(df_display[["Title", "Price (₹)"]], use_container_width=True)
    
    # Display all products as cards
    st.markdown("<h2 class='sub-header'>🛍️ Product Details</h2>", unsafe_allow_html=True)
    
    # Sort products by price for display (lowest first)
    sorted_products = sorted(products, key=lambda x: x[1])
    
    # Create a 2-column layout for product cards
    col1, col2 = st.columns(2)
    
    # Display product cards
    for i, product in enumerate(sorted_products):
        # Determine if this is the lowest price product
        is_lowest = (i == 0)
        
        # Alternate between columns
        current_col = col1 if i % 2 == 0 else col2
        
        with current_col:
            card_class = "product-card lowest-price-highlight" if is_lowest else "product-card"
            
            current_col.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
            
            # Add a label for lowest price product
            if is_lowest:
                current_col.markdown("<div class='lowest-price-label'>LOWEST PRICE</div>", unsafe_allow_html=True)
            
            current_col.markdown(f"<h3>{product[0]}</h3>", unsafe_allow_html=True)
            current_col.markdown(f"<div class='price-tag'>₹{product[1]:,.2f}</div>", unsafe_allow_html=True)
            
            # Button row
            button_col1, button_col2 = current_col.columns([1, 1])
            
            with button_col1:
                st.markdown(f"[View on Amazon]({product[2]})")
            
            with button_col2:
                if st.button("Analyze Reviews", key=f"analyze_{i}"):
                    st.session_state.selected_product = product
                    st.session_state.analyze_clicked = True
            
            current_col.markdown("</div>", unsafe_allow_html=True)
    
    # Show the lowest price product in a special section at the bottom
    lowest_product = sorted_products[0]
    
    st.markdown("<h2 class='sub-header'>🏆 Recommended: Lowest Price Product</h2>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #FF9900;'>🏷️ Best Value</h3>", unsafe_allow_html=True)
    st.markdown(f"**{lowest_product[0]}**")
    st.markdown(f"**Price:** ₹{lowest_product[1]:,.2f}")
    
    # Create columns for the buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"[View on Amazon]({lowest_product[2]})")
    
    with col2:
        if st.button("Analyze Reviews", key="analyze_lowest_bottom"):
            st.session_state.selected_product = lowest_product
            st.session_state.analyze_clicked = True
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return df

def analyze_sentiment_with_ui(product):
    st.markdown("<h2 class='sub-header'>📊 Review Analysis</h2>", unsafe_allow_html=True)
    
    with st.status("Analyzing reviews...") as status:
        st.write(f"Setting up for: {product[0]}")
        
        # Setup chrome driver path
        driver_path = str(Path('chromedriver.exe').resolve())
        st.write("Starting browser...")
        
        # Initialize review scraper and analyze reviews
        scraper = AmazonReviewScraper(driver_path)
        
        st.write("Navigating to product page...")
        review_titles, decision = scraper.scrape_review_titles(
            product[2], 
            max_pages=st.session_state.max_review_pages
        )
        
        status.update(label="Analysis complete!", state="complete")
    
    # Display product being analyzed
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Product</h3>", unsafe_allow_html=True)
    st.markdown(f"**{product[0]}**")
    st.markdown(f"**Price:** ₹{product[1]:,.2f}")
    st.markdown(f"[View on Amazon]({product[2]})")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display reviews
    if review_titles:
        # Create DataFrame for reviews with sentiment
        reviews_data = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for review in review_titles:
            sentiment = TextBlob(review).sentiment.polarity
            sentiment_label = ""
            
            if sentiment > 0.1:
                sentiment_label = "Positive 👍"
                positive_count += 1
            elif sentiment < -0.1:
                sentiment_label = "Negative 👎"
                negative_count += 1
            else:
                sentiment_label = "Neutral 😐"
                neutral_count += 1
                
            reviews_data.append({
                "Review": review,
                "Sentiment": sentiment_label,
                "Score": sentiment
            })
        
        reviews_df = pd.DataFrame(reviews_data)
        
        # Display reviews in expander
        with st.expander("📝 View All Reviews", expanded=True):
            st.dataframe(reviews_df[["Review", "Sentiment", "Score"]], use_container_width=True)
        
        # Calculate statistics
        total = positive_count + negative_count + neutral_count
        
        # Create sentiment distribution chart
        if total > 0:
            dist_data = {
                "Sentiment": ["Positive 👍", "Neutral 😐", "Negative 👎"],
                "Count": [positive_count, neutral_count, negative_count],
                "Percentage": [
                    positive_count/total*100 if total > 0 else 0,
                    neutral_count/total*100 if total > 0 else 0,
                    negative_count/total*100 if total > 0 else 0
                ]
            }
            
            dist_df = pd.DataFrame(dist_data)
            
            # Display statistics and chart in columns
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("<h3>📊 Sentiment Distribution</h3>", unsafe_allow_html=True)
                st.dataframe(dist_df, use_container_width=True)
            
            with col2:
                # Create pie chart
                colors = {
                    "Positive 👍": "#4CAF50", 
                    "Neutral 😐": "#9E9E9E", 
                    "Negative 👎": "#F44336"
                }
                
                fig = px.pie(
                    dist_df, 
                    values="Count", 
                    names="Sentiment", 
                    title="Review Sentiment Distribution",
                    color="Sentiment",
                    color_discrete_map=colors
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        # Display verdict
        st.markdown("<h3>🔍 Final Verdict</h3>", unsafe_allow_html=True)
        
        verdict_class = ""
        if "Buy ✅" in decision:
            verdict_class = "verdict verdict-buy"
        elif "Don't Buy ❌" in decision:
            verdict_class = "verdict verdict-dont-buy"
        else:
            verdict_class = "verdict verdict-neutral"
        
        st.markdown(f"<div class='{verdict_class}'>{decision}</div>", unsafe_allow_html=True)
        
        # Display recommendation
        st.markdown("<h3>💡 Recommendation</h3>", unsafe_allow_html=True)
        
        if "Buy ✅" in decision:
            st.success("YES - This product appears to have overall positive reviews and is the lowest priced option.")
        elif "Don't Buy ❌" in decision:
            st.error("NO - Although this is the lowest priced option, reviews suggest poor quality or satisfaction.")
        else:
            st.info("MAYBE - Reviews are mixed. Consider your specific needs carefully.")
    
    else:
        st.warning("No reviews were found for this product. This might be a new product or reviews couldn't be loaded.")

# Initialize session state
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None

if 'analyze_clicked' not in st.session_state:
    st.session_state.analyze_clicked = False

if 'products' not in st.session_state:
    st.session_state.products = None

if 'max_review_pages' not in st.session_state:
    st.session_state.max_review_pages = max_review_pages

# Set max review pages when slider changes
st.session_state.max_review_pages = max_review_pages

# Main search functionality
st.markdown("<h2 class='sub-header'>🔎 Search Products</h2>", unsafe_allow_html=True)
search_term = st.text_input("Enter product to search on Amazon")

if st.button("Search Amazon", key="search_button") and search_term:
    with st.status("Searching Amazon products...") as status:
        st.write(f"Searching for: {search_term}")
        
        # Setup chrome driver path
        driver_path = str(Path('chromedriver.exe').resolve())
        
        # Find products by price
        st.write("Scanning listings...")
        try:
            # Modify the find_lowest_price_product function to return all products instead of just the lowest
            # For now, we'll simulate multiple products by creating a list
            lowest_price_product = find_lowest_price_product(search_term, driver_path)
            
            if lowest_price_product:
                # In a real implementation, you would modify find_lowest_price_product to return all products
                # Here we'll simulate multiple products with varying prices for demonstration
                
                # The actual product (lowest price)
                base_price = lowest_price_product[1]
                title = lowest_price_product[0]
                link = lowest_price_product[2]
                
                # Create a list of simulated products with different prices
                # In your actual implementation, replace this with real products from the search results
                all_products = [
                    lowest_price_product,  # The actual lowest price product
                    [f"{title} (Alternate)", base_price * 1.1, link],
                    [f"{title} (Premium)", base_price * 1.25, link],
                    [f"{title} (Deluxe)", base_price * 1.5, link],
                    [f"{title} (Pro)", base_price * 1.75, link],
                ]
                
                st.session_state.products = all_products
                status.update(label="Search complete!", state="complete")
            else:
                status.update(label="No products found", state="error")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            status.update(label="Search failed", state="error")
            st.session_state.products = None

# Display products if available
if st.session_state.products:
    display_products(st.session_state.products)

# Show review analysis if a product is selected and analyze button clicked
if st.session_state.selected_product and st.session_state.analyze_clicked:
    analyze_sentiment_with_ui(st.session_state.selected_product)
    st.session_state.analyze_clicked = False  # Reset so it doesn't keep analyzing

# Footer
st.markdown("<div class='footer'>Amazon Product Finder & Review Analyzer - Developed with Streamlit</div>", unsafe_allow_html=True)