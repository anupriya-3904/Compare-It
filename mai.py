import streamlit as st
import time
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
import sys
import logging
from textblob import TextBlob

# Import functions from your existing script
from flipkart_searcher import FlipkartProductSearch, FlipkartReviewScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Flipkart Product Finder & Review Analyzer",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2874F0;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3E4152;
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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🛍️ Flipkart Product Finder & Review Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Find the lowest priced products and analyze review sentiment</p>", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.image("https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Emblem.png", width=150)
    st.markdown("### Settings")
    
    # Search settings
    st.markdown("#### Search Configuration")
    max_products = st.slider("Maximum products to analyze", 3, 10, 5)
    
    # Review settings
    st.markdown("#### Review Analysis")
    max_review_pages = st.slider("Maximum review pages to scrape", 1, 10, 3)
    
    # Advanced options (collapsible)
    with st.expander("Advanced Options"):
        wait_time = st.slider("Page load wait time (seconds)", 2, 10, 5)
        debug_mode = st.checkbox("Enable debug mode", False)
    
    st.markdown("---")
    st.markdown("### How to use")
    st.markdown("""
    1. Enter product name in the search box
    2. Enter the path to chromedriver.exe
    3. Click 'Search Flipkart' button
    4. Review all extracted products
    5. Check out the lowest-priced product
    6. Click 'Analyze Reviews' to see sentiment analysis
    7. View verdict based on positive/negative reviews
    """)

# Function to display search results
def display_products(products):
    if not products:
        st.warning("No products found. Try a different search term.")
        return
    
    st.markdown("<h2 class='sub-header'>🔍 Search Results</h2>", unsafe_allow_html=True)
    
    # Create a DataFrame for better display
    data = []
    for product in products:
        data.append({
            "Title": product['title'],
            "Price": product['price'],
            "Price Text": product['price_text'],
            "Link": product['link']
        })
    
    df = pd.DataFrame(data)
    
    # First, show all extracted products
    st.markdown("<h3 style='color: #2874F0;'>📋 All Extracted Products</h3>", unsafe_allow_html=True)
    
    # Display all products as a table
    st.dataframe(df[["Title", "Price Text"]], use_container_width=True)
    
    # Create an expander for all products with links
    with st.expander("View All Product Links"):
        for idx, product in enumerate(products):
            st.markdown(f"{idx+1}. [{product['title']}]({product['link']}) - {product['price_text']}")
    
    # Then, show the lowest price product in a special card
    st.markdown("<h3 style='color: #2874F0;'>🏷️ Lowest Price Product</h3>", unsafe_allow_html=True)
    
    lowest_product = products[0]  # Assuming products are sorted by price
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"**{lowest_product['title']}**")
    st.markdown(f"**Price:** {lowest_product['price_text']}")
    
    # Create columns for the buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"[View on Flipkart]({lowest_product['link']})")
    
    with col2:
        if st.button("Analyze Reviews", key="analyze_lowest"):
            st.session_state.selected_product = lowest_product
            st.session_state.analyze_clicked = True
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return df

def analyze_sentiment_with_ui(product):
    st.markdown("<h2 class='sub-header'>📊 Review Analysis</h2>", unsafe_allow_html=True)
    
    with st.status("Analyzing reviews...") as status:
        st.write(f"Setting up for: {product['title']}")
        
        # Use chrome driver path from session state
        driver_path = st.session_state.driver_path
        st.write("Starting browser...")
        
        # Initialize review scraper and analyze reviews
        try:
            scraper = FlipkartReviewScraper(driver_path)
            
            st.write("Navigating to product page...")
            all_reviews, all_titles, decision, product_info = scraper.scrape_reviews(
                product['link'], 
                pages_to_scrape=st.session_state.max_review_pages
            )
            
            status.update(label="Analysis complete!", state="complete")
        except Exception as e:
            st.error(f"An error occurred during review analysis: {str(e)}")
            status.update(label="Analysis failed", state="error")
            return
    
    # Display product being analyzed
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Product</h3>", unsafe_allow_html=True)
    st.markdown(f"**{product['title']}**")
    st.markdown(f"**Price:** {product['price_text']}")
    st.markdown(f"[View on Flipkart]({product['link']})")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display reviews
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
        tab1, tab2, tab3 = st.tabs(["All Reviews", "Review Titles", "Full Reviews"])
        
        with tab1:
            st.write(f"Total content analyzed: {len(all_content)}")
            st.dataframe(reviews_df, use_container_width=True)
        
        with tab2:
            if all_titles:
                st.write(f"Total review titles: {len(all_titles)}")
                titles_df = pd.DataFrame([{"Title": title} for title in all_titles])
                st.dataframe(titles_df, use_container_width=True)
            else:
                st.info("No review titles were found.")
        
        with tab3:
            if all_reviews:
                st.write(f"Total full reviews: {len(all_reviews)}")
                reviews_only_df = pd.DataFrame([{"Review": review} for review in all_reviews])
                st.dataframe(reviews_only_df, use_container_width=True)
            else:
                st.info("No full reviews were found.")
        
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

if 'driver_path' not in st.session_state:
    st.session_state.driver_path = "chromedriver.exe"

# Set max review pages when slider changes
st.session_state.max_review_pages = max_review_pages

# Main search functionality
st.markdown("<h2 class='sub-header'>🔎 Search Products</h2>", unsafe_allow_html=True)

# Create two columns for inputs
col1, col2 = st.columns([2, 1])

with col1:
    search_term = st.text_input("Enter product to search on Flipkart")

with col2:
    driver_path = st.text_input("ChromeDriver path", value=st.session_state.driver_path)
    st.session_state.driver_path = driver_path

if st.button("Search Flipkart", key="search_button") and search_term:
    with st.status("Searching Flipkart products...") as status:
        st.write(f"Searching for: {search_term}")
        
        # Setup chrome driver path
        if not os.path.isfile(driver_path):
            st.warning(f"ChromeDriver not found at '{driver_path}'. The search may fail.")
        
        # Find products
        st.write("Scanning listings...")
        try:
            product_searcher = FlipkartProductSearch(driver_path)
            products = product_searcher.search_products(search_term)
            
            if products:
                lowest_price_product = product_searcher.get_lowest_price_product()
                st.session_state.products = products
                status.update(label="Search complete!", state="complete")
            else:
                status.update(label="No products found", state="error")
                st.session_state.products = None
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
st.markdown("<div class='footer'>Flipkart Product Finder & Review Analyzer - Developed with Streamlit</div>", unsafe_allow_html=True)