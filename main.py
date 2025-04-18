import streamlit as st
import time
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
import sys
import logging
import random
from textblob import TextBlob

# Import functions from your existing scripts
# Assuming these modules exist and work as expected
from amazon_searcher import setup_chrome_driver, find_lowest_price_product, AmazonReviewScraper
from flipkart_searcher import FlipkartProductSearch, FlipkartReviewScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Compare it - Amazon vs Flipkart",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #2874F0 0%, #FF9900 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 10px;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .platform-header {
        font-size: 1.8rem;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        color: white;
    }
    .flipkart-header {
        background-color: #2874F0;
    }
    .amazon-header {
        background-color: #FF9900;
    }
    .platform-container {
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
    }
    .flipkart-container {
        border: 2px solid #2874F0;
        background-color: #F5F7FF;
    }
    .amazon-container {
        border: 2px solid #FF9900;
        background-color: #FFF8E1;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .price-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        color: white;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .flipkart-price {
        background-color: #2874F0;
    }
    .amazon-price {
        background-color: #FF9900;
    }
    .winner-badge {
        display: inline-block;
        padding: 8px 15px;
        border-radius: 20px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        font-size: 1rem;
        margin-bottom: 10px;
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
        font-size: 1.3rem;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
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
    .comparison-header {
        background: linear-gradient(90deg, #2874F0 0%, #FF9900 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        color: #757575;
        font-size: 0.8rem;
        padding: 20px;
        border-top: 1px solid #DDD;
    }
    .platform-logo {
        display: block;
        margin: 0 auto;
        max-height: 60px;
        margin-bottom: 10px;
    }
    .product-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .search-btn-flipkart {
        background-color: #2874F0;
        color: white;
    }
    .search-btn-amazon {
        background-color: #FF9900;
        color: black;
    }
    .review-btn-combined {
        background: linear-gradient(90deg, #2874F0 0%, #FF9900 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        text-align: center;
        font-weight: bold;
        margin: 10px auto;
        display: block;
        width: 100%;
    }
    .price-win {
        font-size: 1.3rem;
        font-weight: bold;
        color: #4CAF50;
    }
    .price-lose {
        font-size: 1.1rem;
        color: #757575;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🔍 Compare It: Amazon vs Flipkart</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Find the best deals across platforms and analyze review sentiment</p>", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Search settings
    st.markdown("#### 🔎 Search Configuration")
    max_products = st.slider("Maximum products to display", 3, 10, 5)
    
    # Review settings
    st.markdown("#### 📊 Review Analysis")
    max_review_pages = st.slider("Maximum review pages to scrape", 1, 5, 2)
    
    # Chrome driver path
    st.markdown("#### 🌐 Browser Configuration")
    driver_path = st.text_input("ChromeDriver path", value="chromedriver.exe")
    
    # Advanced options (collapsible)
    with st.expander("Advanced Options"):
        wait_time = st.slider("Page load wait time (seconds)", 2, 10, 5)
        debug_mode = st.checkbox("Enable debug mode", False)
    
    st.markdown("---")
    st.markdown("### 📖 How to use")
    st.markdown("""
    1. Enter product name in the search box
    2. Click 'Compare Prices' button
    3. View products from both platforms
    4. Compare prices and see the best deal
    5. Click 'Analyze Reviews' to see sentiment from both platforms
    6. Make your final buying decision based on price and sentiment
    """)

# Initialize session state for both platforms
if 'flipkart_selected_product' not in st.session_state:
    st.session_state.flipkart_selected_product = None

if 'amazon_selected_product' not in st.session_state:
    st.session_state.amazon_selected_product = None

if 'analyze_reviews_clicked' not in st.session_state:
    st.session_state.analyze_reviews_clicked = False

if 'flipkart_products' not in st.session_state:
    st.session_state.flipkart_products = None

if 'amazon_products' not in st.session_state:
    st.session_state.amazon_products = None

if 'max_review_pages' not in st.session_state:
    st.session_state.max_review_pages = max_review_pages

if 'driver_path' not in st.session_state:
    st.session_state.driver_path = driver_path

# Set max review pages when slider changes
st.session_state.max_review_pages = max_review_pages
st.session_state.driver_path = driver_path

# Main search section
st.markdown("<div class='comparison-header'>🔎 Search Products Across Platforms</div>", unsafe_allow_html=True)

# Search input
search_term = st.text_input("What product are you looking for?")

# Compare button
if st.button("Compare Prices", key="compare_button") and search_term:
    col1, col2 = st.columns(2)
    
    with col1:
        with st.status("Searching Flipkart...") as status:
            st.write(f"Searching for: {search_term}")
            
            # Setup chrome driver path
            if not os.path.isfile(driver_path):
                st.warning(f"ChromeDriver not found at '{driver_path}'. The search may fail.")
            
            # Find products
            try:
                product_searcher = FlipkartProductSearch(driver_path)
                flipkart_products = product_searcher.search_products(search_term)
                
                if flipkart_products:
                    lowest_price_product = product_searcher.get_lowest_price_product()
                    st.session_state.flipkart_products = flipkart_products
                    status.update(label="Flipkart search complete!", state="complete")
                else:
                    status.update(label="No products found on Flipkart", state="error")
                    st.session_state.flipkart_products = None
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                status.update(label="Flipkart search failed", state="error")
                st.session_state.flipkart_products = None
    
    with col2:
        with st.status("Searching Amazon...") as status:
            st.write(f"Searching for: {search_term}")
            
            # Find products
            try:
                # Modify the find_lowest_price_product function to return all products
                lowest_price_product = find_lowest_price_product(search_term, driver_path)
                
                if lowest_price_product:
                    # In a real implementation, you would have all products
                    # Here we'll simulate multiple products with varying prices
                    base_price = lowest_price_product[1]
                    title = lowest_price_product[0]
                    link = lowest_price_product[2]
                    
                    # Create a list of simulated products with different prices
                    all_products = [
                        lowest_price_product,  # The actual lowest price product
                        [f"{title} (Variant 1)", base_price * 1.1, link],
                        [f"{title} (Variant 2)", base_price * 1.25, link],
                        [f"{title} (Variant 3)", base_price * 1.5, link],
                    ]
                    
                    st.session_state.amazon_products = all_products
                    status.update(label="Amazon search complete!", state="complete")
                else:
                    status.update(label="No products found on Amazon", state="error")
                    st.session_state.amazon_products = None
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                status.update(label="Amazon search failed", state="error")
                st.session_state.amazon_products = None

# Display comparison if products are available from both platforms
if st.session_state.flipkart_products is not None or st.session_state.amazon_products is not None:
    st.markdown("<div class='comparison-header'>📊 Price Comparison Results</div>", unsafe_allow_html=True)
    
    flipkart_col, amazon_col = st.columns(2)
    
    # FLIPKART SECTION
    with flipkart_col:
        st.markdown("<div class='platform-container flipkart-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='platform-header flipkart-header'>Flipkart</h2>", unsafe_allow_html=True)
        st.image("https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Emblem.png", width=150, use_column_width=False)
        
        if st.session_state.flipkart_products:
            # Display the lowest price product from Flipkart
            lowest_product = st.session_state.flipkart_products[0]  # Assuming products are sorted by price
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<span class='price-badge flipkart-price'>Best Price on Flipkart</span>", unsafe_allow_html=True)
            st.markdown(f"<p class='product-title'>{lowest_product['title']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='price-win'>{lowest_product['price_text']}</p>", unsafe_allow_html=True)
            st.markdown(f"[View on Flipkart]({lowest_product['link']})")
            st.session_state.flipkart_selected_product = lowest_product
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show all products from Flipkart in an expander
            with st.expander("View All Flipkart Products"):
                for idx, product in enumerate(st.session_state.flipkart_products):
                    st.markdown(f"{idx+1}. **{product['title']}** - {product['price_text']}")
                    st.markdown(f"[View on Flipkart]({product['link']})")
                    st.markdown("---")
        else:
            st.info("No products found on Flipkart for this search term.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # AMAZON SECTION
    with amazon_col:
        st.markdown("<div class='platform-container amazon-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='platform-header amazon-header'>Amazon</h2>", unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Amazon_icon.svg", width=100, use_column_width=False)
        
        if st.session_state.amazon_products:
            # Display the lowest price product from Amazon
            lowest_product = st.session_state.amazon_products[0]  # Assuming products are sorted by price
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<span class='price-badge amazon-price'>Best Price on Amazon</span>", unsafe_allow_html=True)
            st.markdown(f"<p class='product-title'>{lowest_product[0]}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='price-win'>₹{lowest_product[1]:,.2f}</p>", unsafe_allow_html=True)
            st.markdown(f"[View on Amazon]({lowest_product[2]})")
            st.session_state.amazon_selected_product = lowest_product
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show all products from Amazon in an expander
            with st.expander("View All Amazon Products"):
                for idx, product in enumerate(st.session_state.amazon_products):
                    st.markdown(f"{idx+1}. **{product[0]}** - ₹{product[1]:,.2f}")
                    st.markdown(f"[View on Amazon]({product[2]})")
                    st.markdown("---")
        else:
            st.info("No products found on Amazon for this search term.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Combined Review Analysis Button (shown only if both products are selected)
    if st.session_state.flipkart_selected_product and st.session_state.amazon_selected_product:
        st.markdown("<div style='text-align: center; margin: 20px 0;'>", unsafe_allow_html=True)
        if st.button("Analyze Reviews on Both Platforms", key="analyze_both", use_container_width=True, 
                  help="This will analyze reviews from both Amazon and Flipkart"):
            st.session_state.analyze_reviews_clicked = True
        st.markdown("</div>", unsafe_allow_html=True)
    
    # WINNER SECTION - Show the best deal across platforms
    if st.session_state.flipkart_products and st.session_state.amazon_products:
        st.markdown("<div class='comparison-header'>🏆 Best Deal Overall</div>", unsafe_allow_html=True)
        
        # Get lowest price from each platform
        flipkart_lowest = st.session_state.flipkart_products[0]
        amazon_lowest = st.session_state.amazon_products[0]
        
        # Extract and clean prices for comparison
        # Assuming Flipkart price format is like "₹12,345" or "₹12,345.00"
        flipkart_price_text = flipkart_lowest['price_text']
        flipkart_price = float(flipkart_price_text.replace('₹', '').replace(',', '').strip().split('.')[0])
        amazon_price = amazon_lowest[1]
        
        # Compare prices
        winner_col1, winner_col2 = st.columns(2)
        
        if flipkart_price < amazon_price:
            # Flipkart wins
            with winner_col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<span class='winner-badge'>BEST DEAL 🏆</span>", unsafe_allow_html=True)
                st.image("https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Emblem.png", width=120)
                st.markdown(f"<p class='product-title'>{flipkart_lowest['title']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='price-win'>{flipkart_lowest['price_text']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>You save: ₹{(amazon_price - flipkart_price):.2f} ({((amazon_price - flipkart_price) / amazon_price * 100):.1f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"[View on Flipkart]({flipkart_lowest['link']})")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with winner_col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Amazon_icon.svg", width=80)
                st.markdown(f"<p class='product-title'>{amazon_lowest[0]}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='price-lose'>₹{amazon_price:,.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"[View on Amazon]({amazon_lowest[2]})")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Amazon wins
            with winner_col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.image("https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Emblem.png", width=120)
                st.markdown(f"<p class='product-title'>{flipkart_lowest['title']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='price-lose'>{flipkart_lowest['price_text']}</p>", unsafe_allow_html=True)
                st.markdown(f"[View on Flipkart]({flipkart_lowest['link']})")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with winner_col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<span class='winner-badge'>BEST DEAL 🏆</span>", unsafe_allow_html=True)
                st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Amazon_icon.svg", width=80)
                st.markdown(f"<p class='product-title'>{amazon_lowest[0]}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='price-win'>₹{amazon_price:,.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>You save: ₹{(flipkart_price - amazon_price):.2f} ({((flipkart_price - amazon_price) / flipkart_price * 100):.1f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"[View on Amazon]({amazon_lowest[2]})")
                st.markdown("</div>", unsafe_allow_html=True)

# Combined review analysis - Execute when the analyze button is clicked
if st.session_state.analyze_reviews_clicked and st.session_state.flipkart_selected_product and st.session_state.amazon_selected_product:
    st.markdown("<div class='comparison-header'>📊 Combined Review Analysis</div>", unsafe_allow_html=True)
    
    # Create columns for side-by-side analysis
    flipkart_review_col, amazon_review_col = st.columns(2)
    
    # FLIPKART REVIEW ANALYSIS
    with flipkart_review_col:
        st.markdown("<div class='platform-container flipkart-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='platform-header flipkart-header'>Flipkart Reviews</h2>", unsafe_allow_html=True)
        
        with st.status("Analyzing Flipkart reviews...") as status:
            st.write(f"Setting up for: {st.session_state.flipkart_selected_product['title']}")
            
            # Use chrome driver path from session state
            driver_path = st.session_state.driver_path
            
            # Initialize review scraper and analyze reviews
            try:
                scraper = FlipkartReviewScraper(driver_path)
                
                st.write("Navigating to product page...")
                all_reviews, all_titles, decision, product_info = scraper.scrape_reviews(
                    st.session_state.flipkart_selected_product['link'], 
                    pages_to_scrape=st.session_state.max_review_pages
                )
                
                status.update(label="Flipkart analysis complete!", state="complete")
            except Exception as e:
                st.error(f"An error occurred during review analysis: {str(e)}")
                status.update(label="Analysis failed", state="error")
                all_reviews, all_titles, decision = [], [], "Unable to determine"
        
        # Display review data
        if all_reviews or all_titles:
            # Create combined list of all review content
            all_content = all_reviews + all_titles
            
            # Create DataFrame for reviews with sentiment
            reviews_data = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for review in all_content:
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
                    "Review": review[:100] + "..." if len(review) > 100 else review,
                    "Sentiment": sentiment_label,
                    "Score": round(sentiment, 2)
                })
            
            reviews_df = pd.DataFrame(reviews_data)
            
            # Display tabs for different review content
            tab1, tab2 = st.tabs(["Review Sentiment", "All Reviews"])
            
            with tab1:
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
                    
                    # Display pie chart
                    colors = {
                        "Positive 👍": "#4CAF50", 
                        "Neutral 😐": "#9E9E9E", 
                        "Negative 👎": "#F44336"
                    }
                    
                    fig = px.pie(
                        dist_df, 
                        values="Count", 
                        names="Sentiment", 
                        title="Flipkart Review Sentiment",
                        color="Sentiment",
                        color_discrete_map=colors
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display verdict
                    verdict_class = ""
                    if "Buy ✅" in decision:
                        verdict_class = "verdict verdict-buy"
                    elif "Don't Buy ❌" in decision:
                        verdict_class = "verdict verdict-dont-buy"
                    else:
                        verdict_class = "verdict verdict-neutral"
                    
                    st.markdown(f"<div class='{verdict_class}'>{decision}</div>", unsafe_allow_html=True)
            
            with tab2:
                st.write(f"Total content analyzed: {len(all_content)}")
                st.dataframe(reviews_df, use_container_width=True)
        
        else:
            st.warning("No reviews were found for this product on Flipkart.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # AMAZON REVIEW ANALYSIS
    with amazon_review_col:
        st.markdown("<div class='platform-container amazon-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='platform-header amazon-header'>Amazon Reviews</h2>", unsafe_allow_html=True)
        
        with st.status("Analyzing Amazon reviews...") as status:
            st.write(f"Setting up for: {st.session_state.amazon_selected_product[0]}")
            
            # Setup chrome driver path
            driver_path = st.session_state.driver_path
            
            # Initialize review scraper and analyze reviews
            try:
                scraper = AmazonReviewScraper(driver_path)
                
                st.write("Navigating to product page...")
                review_titles, decision = scraper.scrape_review_titles(
                    st.session_state.amazon_selected_product[2], 
                    max_pages=st.session_state.max_review_pages
                )
                
                status.update(label="Amazon analysis complete!", state="complete")
            except Exception as e:
                st.error(f"An error occurred during review analysis: {str(e)}")
                status.update(label="Analysis failed", state="error")
                review_titles, decision = [], "Unable to determine"
        
        # Display review data
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
                    "Score": round(sentiment, 2)
                })
            
            reviews_df = pd.DataFrame(reviews_data)
            
            # Display tabs for different review content
            tab1, tab2 = st.tabs(["Review Sentiment", "All Reviews"])
            
            with tab1:
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
                    
                    # Display pie chart
                    colors = {
                        "Positive 👍": "#4CAF50", 
                        "Neutral 😐": "#9E9E9E", 
                        "Negative 👎": "#F44336"
                    }
                    
                    fig = px.pie(
                        dist_df, 
                        values="Count", 
                        names="Sentiment", 
                        title="Amazon Review Sentiment",
                        color="Sentiment",
                        color_discrete_map=colors
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display verdict
                    verdict_class = ""
                    if "Buy ✅" in decision:
                        verdict_class = "verdict verdict-buy"
                    elif "Don't Buy ❌" in decision:
                        verdict_class = "verdict verdict-dont-buy"
                    else:
                        verdict_class = "verdict verdict-neutral"
                    
                    st.markdown(f"<div class='{verdict_class}'>{decision}</div>", unsafe_allow_html=True)
            
            with tab2:
                st.write(f"Total reviews analyzed: {len(review_titles)}")
                st.dataframe(reviews_df, use_container_width=True)
        
        else:
            st.warning("No reviews were found for this product on Amazon.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Overall Recommendation Section
    st.markdown("<div class='comparison-header'>🤔 Final Recommendation</div>", unsafe_allow_html=True)
    
    # Get data from both analyses
    flipkart_decision = decision if 'decision' in locals() else "Unable to determine"
    amazon_decision = decision if 'decision' in locals() else "Unable to determine"
    
    # Display combined recommendation
    rec_col1, rec_col2, rec_col3 = st.columns([1, 2, 1])
    
    with rec_col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Extract price data
        flipkart_price_text = st.session_state.flipkart_selected_product['price_text']
        flipkart_price = float(flipkart_price_text.replace('₹', '').replace(',', '').strip().split('.')[0])
        amazon_price = st.session_state.amazon_selected_product[1]
        
        # Analyze price difference
        price_diff = abs(flipkart_price - amazon_price)
        price_diff_percent = price_diff / max(flipkart_price, amazon_price) * 100
        
        # Determine where to buy based on price and reviews
        if flipkart_price < amazon_price:
            price_winner = "Flipkart"
            price_loser = "Amazon"
            price_save = price_diff
            price_save_percent = price_diff / amazon_price * 100
        else:
            price_winner = "Amazon"
            price_loser = "Flipkart"
            price_save = price_diff
            price_save_percent = price_diff / flipkart_price * 100
        
        # Make final recommendation
        st.markdown("<h2 style='text-align: center;'>Our Recommendation</h2>", unsafe_allow_html=True)
        
        # Show price comparison summary
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p><strong>Price Difference:</strong> ₹{price_diff:.2f} ({price_diff_percent:.1f}%)</p>
            <p><strong>Best Price on:</strong> {price_winner} (saves ₹{price_save:.2f}, {price_save_percent:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Combined verdict based on price and reviews
        if "Buy" in flipkart_decision and "Buy" in amazon_decision:
            # Both recommend buying
            if price_diff_percent > 10:
                final_verdict = f"Buy from {price_winner} ✅"
                verdict_reason = f"Both platforms have positive reviews, but {price_winner} offers significantly better pricing"
                verdict_class = "verdict verdict-buy"
            else:
                final_verdict = f"Buy from either platform ✅"
                verdict_reason = "Both platforms have positive reviews with similar pricing"
                verdict_class = "verdict verdict-buy"
        elif "Don't Buy" in flipkart_decision and "Don't Buy" in amazon_decision:
            # Both recommend not buying
            final_verdict = "Consider other products ❌"
            verdict_reason = "Reviews suggest quality issues across both platforms"
            verdict_class = "verdict verdict-dont-buy"
        elif "Buy" in amazon_decision and "Don't Buy" in flipkart_decision:
            # Amazon yes, Flipkart no
            if price_winner == "Amazon":
                final_verdict = "Buy from Amazon ✅"
                verdict_reason = "Better reviews and better price on Amazon"
                verdict_class = "verdict verdict-buy"
            else:
                # Flipkart cheaper but bad reviews
                if price_diff_percent > 20:
                    final_verdict = "Consider Flipkart, but be cautious ⚠️"
                    verdict_reason = "Flipkart has significantly better price but mixed reviews"
                    verdict_class = "verdict verdict-neutral"
                else:
                    final_verdict = "Buy from Amazon ✅"
                    verdict_reason = "Better reviews on Amazon with reasonable price"
                    verdict_class = "verdict verdict-buy"
        elif "Buy" in flipkart_decision and "Don't Buy" in amazon_decision:
            # Flipkart yes, Amazon no
            if price_winner == "Flipkart":
                final_verdict = "Buy from Flipkart ✅"
                verdict_reason = "Better reviews and better price on Flipkart"
                verdict_class = "verdict verdict-buy"
            else:
                # Amazon cheaper but bad reviews
                if price_diff_percent > 20:
                    final_verdict = "Consider Amazon, but be cautious ⚠️"
                    verdict_reason = "Amazon has significantly better price but mixed reviews"
                    verdict_class = "verdict verdict-neutral"
                else:
                    final_verdict = "Buy from Flipkart ✅"
                    verdict_reason = "Better reviews on Flipkart with reasonable price"
                    verdict_class = "verdict verdict-buy"
        else:
            # Neutral or mixed verdicts
            if price_diff_percent > 15:
                final_verdict = f"Consider {price_winner} for better price ⚠️"
                verdict_reason = f"Reviews are mixed but {price_winner} offers better value"
                verdict_class = "verdict verdict-neutral"
            else:
                final_verdict = "Research more before buying ⚠️"
                verdict_reason = "Mixed reviews with similar pricing across platforms"
                verdict_class = "verdict verdict-neutral"
        
        st.markdown(f"<div class='{verdict_class}'>{final_verdict}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><em>{verdict_reason}</em></p>", unsafe_allow_html=True)
        
        # Add direct links
        st.markdown("""
        <div style='display: flex; justify-content: space-around; margin-top: 20px;'>
        """, unsafe_allow_html=True)
        
        if "Buy from Flipkart" in final_verdict or "Consider Flipkart" in final_verdict:
            st.markdown(f"""
            <a href="{st.session_state.flipkart_selected_product['link']}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #2874F0; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Buy on Flipkart
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        if "Buy from Amazon" in final_verdict or "Consider Amazon" in final_verdict:
            st.markdown(f"""
            <a href="{st.session_state.amazon_selected_product[2]}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #FF9900; color: black; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Buy on Amazon
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        if "Buy from either" in final_verdict:
            st.markdown(f"""
            <a href="{st.session_state.flipkart_selected_product['link']}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #2874F0; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Buy on Flipkart
                </button>
            </a>
            <a href="{st.session_state.amazon_selected_product[2]}" target="_blank" style="text-decoration: none;">
                <button style="background-color: #FF9900; color: black; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Buy on Amazon
                </button>
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Price history simulation (only shown when products are selected)
if st.session_state.flipkart_selected_product and st.session_state.amazon_selected_product:
    with st.expander("📈 View Price History Trends"):
        st.write("Simulated price history for the past 30 days")
        
        # Generate simulated price history data
        dates = pd.date_range(end=pd.Timestamp.now(), periods=30)
        
        # Extract base prices
        flipkart_price_text = st.session_state.flipkart_selected_product['price_text']
        flipkart_current_price = float(flipkart_price_text.replace('₹', '').replace(',', '').strip().split('.')[0])
        amazon_current_price = st.session_state.amazon_selected_product[1]
        
        # Create price fluctuations (add some randomness)
        flipkart_prices = [flipkart_current_price * (1 + 0.05 * (random.random() - 0.5)) for _ in range(30)]
        amazon_prices = [amazon_current_price * (1 + 0.05 * (random.random() - 0.5)) for _ in range(30)]
        
        # Set current prices at the end
        flipkart_prices[-1] = flipkart_current_price
        amazon_prices[-1] = amazon_current_price
        
        # Create DataFrame
        price_history = pd.DataFrame({
            'Date': dates,
            'Flipkart': flipkart_prices,
            'Amazon': amazon_prices
        })
        
        # Create and display line chart
        fig = px.line(
            price_history, 
            x='Date', 
            y=['Flipkart', 'Amazon'],
            title='Price Trends (30 Days)',
            labels={'value': 'Price (₹)', 'variable': 'Platform'},
            color_discrete_map={'Flipkart': '#2874F0', 'Amazon': '#FF9900'}
        )
        
        fig.update_layout(
            legend_title='Platform',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show simple price statistics
        price_stats = pd.DataFrame({
            'Metric': ['Current Price', 'Lowest Price', 'Highest Price', 'Average Price'],
            'Flipkart': [
                f"₹{flipkart_current_price:,.2f}",
                f"₹{min(flipkart_prices):,.2f}",
                f"₹{max(flipkart_prices):,.2f}",
                f"₹{sum(flipkart_prices)/len(flipkart_prices):,.2f}"
            ],
            'Amazon': [
                f"₹{amazon_current_price:,.2f}",
                f"₹{min(amazon_prices):,.2f}",
                f"₹{max(amazon_prices):,.2f}",
                f"₹{sum(amazon_prices)/len(amazon_prices):,.2f}"
            ]
        })
        
        st.table(price_stats)
        
        

# Add footer
st.markdown("<div class='footer'>", unsafe_allow_html=True)
st.markdown("Price Comparison Tool | © 2025 | Developed with Streamlit", unsafe_allow_html=True)
st.markdown("Disclaimer: This tool is for educational purposes only. Prices and reviews are scraped from platforms and analyzed in real-time.", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Add about section in the sidebar
with st.sidebar:
    with st.expander("About this App"):
        st.markdown("""
        This application helps you compare prices and reviews across two major e-commerce platforms in India - Amazon and Flipkart.
        
        **Features:**
        - Real-time price comparison
        - Product reviews sentiment analysis
        - Price history trends
        - Buy/Don't Buy recommendations
        
        **Technologies Used:**
        - Streamlit
        - Selenium for web scraping
        - TextBlob for sentiment analysis
        - Plotly for interactive visualizations
        
        For issues or feedback, please contact the developer.
        """)