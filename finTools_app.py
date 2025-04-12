#!/usr/bin/env python3
"""
Empower Portfolio WebArchive Extractor
Copyright (C) 2025 Rodrigo Loureiro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
# Empower Portfolio WebArchive Extractor
=======================================

## Overview
This Streamlit app extracts portfolio holdings data from Empower retirement account
webarchive files (.webarchive format) and converts them to both human-readable text
and CSV format for further analysis.

## Inputs
- .webarchive files containing Empower retirement account portfolio information
- Files can be either uploaded by the user or selected from available files in the current directory

## Outputs
- Structured portfolio holdings data displayed as a table
- CSV file containing portfolio holdings information
- Raw extracted text (optional)

## Usage Instructions
1. Launch the app by running `streamlit run finTools_app.py`
2. Choose whether to upload a new .webarchive file or select an existing one
3. Configure extraction options:
   - Extract Portfolio Holdings: Parse and structure the portfolio data
   - Generate CSV File: Save the extracted data as a CSV file
   - Show Full Extracted Text: Display the raw text content of the webarchive
4. Click "Process WebArchive File" to start the extraction
5. View the results and download the CSV file if needed

## Dependencies
- streamlit: Web interface
- pandas: Data manipulation
- read_empower_webarchive: Custom module for webarchive processing

"""
import streamlit as st
import os
import glob
import pandas as pd
import sys
from io import StringIO
import tempfile
import uuid
import time
import datetime

# Add user_id management - put this after imports but before other functions
def ensure_user_dirs():
    """Create the user_files directory and user-specific subdirectory"""
    # Create main user_files directory if it doesn't exist
    user_files_dir = os.path.join(os.getcwd(), "user_files")
    if not os.path.exists(user_files_dir):
        os.makedirs(user_files_dir)

    # Create/get user ID and ensure user-specific directory exists
    if 'user_id' not in st.session_state:
        # Generate a unique user ID using date format YYYYMMDD and 8-char uuid4
        today = datetime.datetime.now().strftime("%Y%m%d")
        st.session_state.user_id = f"{today}_{uuid.uuid4().hex[:8]}"

    # Create user-specific directory
    user_dir = os.path.join(user_files_dir, st.session_state.user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    return user_dir

# Add this function after the ensure_user_dirs function

def cleanup_old_sessions():
    """Delete user session directories that are older than 24 hours"""
    user_files_dir = os.path.join(os.getcwd(), "user_files")

    # Skip if user_files directory doesn't exist
    if not os.path.exists(user_files_dir):
        return

    current_time = time.time()
    # 24 hours in seconds
    max_age = 24 * 60 * 60

    # Get list of all user directories
    user_dirs = [os.path.join(user_files_dir, d) for d in os.listdir(user_files_dir)
                if os.path.isdir(os.path.join(user_files_dir, d))]

    for user_dir in user_dirs:
        try:
            # Skip current user's directory
            if 'user_id' in st.session_state and user_dir.endswith(st.session_state.user_id):
                continue

            # Get directory creation/modification time
            dir_time = os.path.getmtime(user_dir)

            # If directory is older than max_age, delete it
            if current_time - dir_time > max_age:
                # Recursively delete the directory and all its contents
                for root, dirs, files in os.walk(user_dir, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(user_dir)
        except Exception as e:
            # Log errors but continue processing other directories
            print(f"Error cleaning up directory {user_dir}: {str(e)}")

# Replace the original ensure_user_files_dir with the new function
def ensure_user_files_dir():
    """Get the user-specific directory path"""
    return ensure_user_dirs()

# Import functions from the read_empower_webarchive script
from read_empower_webarchive import (
    extract_webarchive_text,
    extract_portfolio_holdings,
    save_holdings_to_csv,
    format_holdings_as_text
)

# Set page config - must be the first Streamlit command
st.set_page_config(page_title="Empower Portfolio Extractor", layout="wide")

# Add these lines right after the st.set_page_config line
if 'processed_result' not in st.session_state:
    st.session_state.processed_result = None
if 'processed_file_path' not in st.session_state:
    st.session_state.processed_file_path = None

def get_available_webarchive_files():
    """Find and list all .webarchive files in the current directory and user's directory"""
    # Check both current directory and user-specific directory
    current_dir_files = glob.glob("*.webarchive")
    user_dir = ensure_user_files_dir()
    user_dir_files = glob.glob(os.path.join(user_dir, "*.webarchive"))

    # Return full paths for both sets of files
    return current_dir_files + user_dir_files

def save_raw_data_to_file(text, file_path_base):
    """Save raw extracted text to a file with _rawdata suffix"""
    user_dir = ensure_user_files_dir()
    base_name = os.path.basename(file_path_base)
    raw_data_path = os.path.join(user_dir, f"{base_name}_rawdata.txt")
    with open(raw_data_path, "w", encoding="utf-8") as f:
        f.write(text)
    return raw_data_path

def render_sidebar():
    """Render all sidebar elements and return user inputs"""
    with st.sidebar:
        st.markdown("""
            <style>
            /* Sidebar styling */
            [data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 250px;
                max-width: 450px;
                background-color: lightblue;
            }
            </style>
        """, unsafe_allow_html=True)

        # Add Buy Me a Coffee button at the top of sidebar
        st.markdown("""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                    Like what you see?
            <a href="https://www.buymeacoffee.com/PNhYc1Mjil" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
                     alt="Buy Me A Coffee"
                     style="height: 50px; width: auto;">
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.title("Empower Portfolio Extractor")

        st.markdown("""
        ### Instructions:
        1. Upload your .webarchive file
        2. Click Process and view the results
        """)

        # File upload section - no more selection method choice
        st.header("Step 1: Upload File")

        file_path = None
        uploaded_file = st.file_uploader("Upload a .webarchive file", type=["webarchive"])
        if uploaded_file:
            # Save the uploaded file to user-specific directory
            user_dir = ensure_user_files_dir()
            temp_file_path = os.path.join(user_dir, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            file_path = temp_file_path

        # Process button
        st.header("Step 2: Process")
        process_button = st.button("Process WebArchive File")

    # Return all the user inputs from the sidebar
    # Always set extract_portfolio and save_csv to True
    return {
        "file_path": file_path,
        "file_selection_method": "Upload a file",  # Always upload now
        "extract_portfolio": True,  # Always extract portfolio
        "save_csv": True,           # Always save CSV
        "process_button": process_button
    }

def process_webarchive(file_path, extract_portfolio=True, save_csv=True):
    """Process a webarchive file and return the extracted data"""
    # Extract text content
    extracted_text = extract_webarchive_text(file_path)

    if not extracted_text or extracted_text.startswith("Error"):
        return {
            "success": False,
            "error": extracted_text or "Extraction failed: No content extracted",
            "text": None,
            "holdings": None,
            "csv_path": None,
            "raw_data_path": None,
            "text_path": None
        }

    # Save raw data to file
    output_file_base = os.path.splitext(os.path.basename(file_path))[0]
    raw_data_path = save_raw_data_to_file(extracted_text, output_file_base)

    # Process for portfolio holdings if requested
    holdings_data = None
    csv_path = None
    text_path = None
    morningstar_path = None
    report_path = None

    if extract_portfolio:
        holdings_data = extract_portfolio_holdings(extracted_text)
        if isinstance(holdings_data, str) and holdings_data.startswith("Could not"):
            return {
                "success": False,
                "error": holdings_data,
                "text": extracted_text,
                "holdings": None,
                "csv_path": None,
                "raw_data_path": raw_data_path,
                "text_path": None
            }

        # Save as CSV if requested
        if save_csv:
            user_dir = ensure_user_files_dir()
            csv_path = os.path.join(user_dir, f"{output_file_base}.csv")
            save_holdings_to_csv(holdings_data, csv_path)

            # Create MorningStar CSV if possible
            df = pd.read_csv(csv_path)
            morningstar_path = create_morningstar_csv(df, output_file_base)

            # Calculate stats and create text report
            stats = calculate_portfolio_statistics(df)
            if 'error' not in stats:
                report_path = create_text_report(stats, df, output_file_base)

        # Generate formatted text file
        user_dir = ensure_user_files_dir()
        text_path = os.path.join(user_dir, f"{output_file_base}.txt")
        formatted_text = format_holdings_as_text(holdings_data)
        with open(text_path, "w", encoding="utf-8") as file:
            file.write(formatted_text)

    return {
        "success": True,
        "error": None,
        "text": extracted_text,
        "holdings": holdings_data,
        "csv_path": csv_path,
        "raw_data_path": raw_data_path,
        "text_path": text_path,
        "morningstar_path": morningstar_path,
        "report_path": report_path
    }

def read_csv_to_dataframe(csv_path):
    """Read a CSV file and return a pandas DataFrame"""
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return None

def calculate_portfolio_statistics(df):
    """Calculate statistics for the portfolio"""
    stats = {}

    # Only calculate if we have the Value column
    if 'Value' in df.columns:
        try:
            # Handle value formatting (remove $ and commas if present)
            if df['Value'].dtype == 'object':
                df['Value_numeric'] = df['Value'].replace('[\$,]', '', regex=True).astype(float)
            else:
                df['Value_numeric'] = df['Value']

            # Calculate statistics
            stats['total_value'] = df['Value_numeric'].sum()
            stats['count'] = len(df)
            stats['avg_value'] = stats['total_value'] / stats['count'] if stats['count'] > 0 else 0
            stats['max_value'] = df['Value_numeric'].max()
            stats['min_value'] = df['Value_numeric'].min()

            # Map the expected column names to their actual counterparts
            column_mapping = {
                'Symbol': 'Ticker' if 'Ticker' in df.columns else None,
                'Name': 'Name'  # Name is already correctly named
            }

            # Check if any mapped columns are missing
            missing_columns = [exp for exp, act in column_mapping.items() if act is None]
            if missing_columns:
                stats['error'] = f"Missing required columns: {', '.join(missing_columns)}"
                return stats

            # Create a copy with standardized column names for easier processing
            df_mapped = df.copy()
            if 'Ticker' in df.columns:
                df_mapped['Symbol'] = df['Ticker']

            # Calculate top holdings (top 10 instead of top 5)
            top_holdings = df_mapped.sort_values(by='Value_numeric', ascending=False).head(10)
            stats['top_holdings'] = top_holdings

            # Calculate percentage of total for each holding
            df_mapped['pct_of_total'] = df_mapped['Value_numeric'] / stats['total_value'] * 100

            # Use the mapped column names for the final dataframe
            cols_to_select = ['Name', 'Symbol', 'Value_numeric', 'pct_of_total']  # Swapped Name and Symbol order
            stats['holdings_pct'] = df_mapped[cols_to_select].sort_values(by='pct_of_total', ascending=False)

        except Exception as e:
            stats['error'] = f"Error calculating statistics: {str(e)}"
            import traceback
            stats['traceback'] = traceback.format_exc()
    else:
        stats['error'] = "Value column not found in data"

    return stats

def create_morningstar_csv(df, output_file_base):
    """Create a MorningStar-compatible CSV with just Ticker and Shares columns"""
    # Check if we have the needed columns
    ticker_col = 'Ticker' if 'Ticker' in df.columns else ('Symbol' if 'Symbol' in df.columns else None)
    shares_col = 'Shares' if 'Shares' in df.columns else None

    if not ticker_col or not shares_col:
        return None

    # Create a new DataFrame with just Ticker and Shares
    ms_df = pd.DataFrame({
        'Ticker': df[ticker_col],
        'Shares': df[shares_col]
    })

    # Save to CSV in user-specific directory
    user_dir = ensure_user_files_dir()
    base_name = os.path.basename(output_file_base)
    ms_path = os.path.join(user_dir, f"{base_name}_morningstar.csv")
    ms_df.to_csv(ms_path, index=False)
    return ms_path

def create_text_report(stats, df, output_file_base):
    """Create a text report summarizing the portfolio analysis"""
    user_dir = ensure_user_files_dir()
    base_name = os.path.basename(output_file_base)
    report_path = os.path.join(user_dir, f"{base_name}_report.txt")

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("PORTFOLIO ANALYSIS REPORT\n")
        file.write("=======================\n\n")

        # Summary statistics
        file.write("SUMMARY STATISTICS\n")
        file.write("-----------------\n")
        file.write(f"Total Portfolio Value: ${stats['total_value']:,.2f}\n")
        file.write(f"Number of Holdings: {stats['count']}\n")
        file.write(f"Average Holding Value: ${stats['avg_value']:,.2f}\n")
        file.write(f"Largest Holding: ${stats['max_value']:,.2f}\n")
        file.write(f"Smallest Holding: ${stats['min_value']:,.2f}\n\n")

        # Top holdings
        file.write("TOP HOLDINGS\n")
        file.write("-----------\n")

        top_holdings = stats['holdings_pct'].head(10)
        for idx, row in top_holdings.iterrows():
            file.write(f"{row['Name']} ({row['Symbol']}): {row['pct_of_total']:.2f}% (${row['Value_numeric']:,.2f})\n")

        # If there are more than 10 holdings, add an "Other" category
        if len(stats['holdings_pct']) > 10:
            others_sum = stats['holdings_pct'].iloc[10:]['pct_of_total'].sum()
            others_value = others_sum / 100 * stats['total_value']
            file.write(f"Other Holdings: {others_sum:.2f}% (${others_value:,.2f})\n\n")

        # All holdings sorted by value
        file.write("\nALL HOLDINGS (by value)\n")
        file.write("---------------------\n")

        for idx, row in df.sort_values('Value_numeric', ascending=False).iterrows():
            ticker = row.get('Ticker', row.get('Symbol', 'N/A'))
            name = row.get('Name', 'N/A')
            value = row.get('Value_numeric', row.get('Value', 0))
            shares = row.get('Shares', 'N/A')

            file.write(f"{name} ({ticker}): ${value:,.2f}")
            if shares != 'N/A':
                file.write(f", {shares} shares")
            file.write("\n")

    return report_path

def main():
    # Initialize user directory
    user_dir = ensure_user_dirs()

    # Render sidebar and get user inputs
    sidebar_inputs = render_sidebar()

    file_path = sidebar_inputs["file_path"]
    extract_portfolio = sidebar_inputs["extract_portfolio"]
    save_csv = sidebar_inputs["save_csv"]
    process_button = sidebar_inputs["process_button"]

    # Process file only if button clicked and file path provided or if we already have results
    process_file = False

    if file_path and process_button:
        # Clean up old sessions before processing new file
        with st.spinner("Cleaning up old sessions..."):
            cleanup_old_sessions()

        # New file to process
        process_file = True
        st.session_state.processed_file_path = file_path

    # Display results if we have processed data
    if process_file:
        with st.spinner("Processing file..."):
            result = process_webarchive(
                file_path=file_path,
                extract_portfolio=extract_portfolio,
                save_csv=save_csv
            )
            # Store result in session state
            st.session_state.processed_result = result

    # Use stored result if available
    result = st.session_state.processed_result

    if result and result.get("success", False):
        st.success("File processed successfully!")

        # Display portfolio holdings
        if result["holdings"]:
            st.header("Portfolio Holdings")

            # Read data from CSV file for display
            df = None
            if result["csv_path"]:
                df = read_csv_to_dataframe(result["csv_path"])

                # If needed, reorder columns to make sure Name comes before Ticker
                if df is not None and 'Name' in df.columns and 'Ticker' in df.columns:
                    cols = df.columns.tolist()
                    name_index = cols.index('Name')
                    ticker_index = cols.index('Ticker')

                    if ticker_index < name_index:  # If Ticker appears before Name
                        # Reorder the columns to put Name before Ticker
                        cols.remove('Name')
                        cols.insert(ticker_index, 'Name')
                        df = df[cols]

            if df is None:
                # Fallback to the holdings data if CSV couldn't be read
                df = pd.DataFrame(result["holdings"])
                # Make sure Name column comes before Ticker if both exist
                if 'Name' in df.columns and 'Ticker' in df.columns:
                    # Get all column names
                    cols = df.columns.tolist()
                    # Remove both columns
                    cols.remove('Name')
                    cols.remove('Ticker')
                    # Add them back in the desired order
                    cols.insert(0, 'Ticker')
                    cols.insert(0, 'Name')
                    # Reorder the dataframe
                    df = df[cols]

            # Display the dataframe without any formatting - exactly as it appears in the CSV
            st.dataframe(df, hide_index=True)

            # Move download buttons here - right after displaying the holdings table
            st.subheader("Download Options")
            col1, col2, col3 = st.columns(3)

            # Provide CSV download
            if result["csv_path"]:
                with open(result["csv_path"], "r") as f:
                    csv_data = f.read()

                with col1:
                    download_csv = st.download_button(
                        label="Download CSV File",
                        data=csv_data,
                        file_name=os.path.basename(result["csv_path"]),
                        mime="text/csv",
                        key="download_csv"
                    )

            # MorningStar CSV download or text file as fallback
            if result["morningstar_path"]:
                with open(result["morningstar_path"], "r") as f:
                    ms_data = f.read()

                with col2:
                    download_ms = st.download_button(
                        label="Download MorningStar CSV",
                        data=ms_data,
                        file_name=os.path.basename(result["morningstar_path"]),
                        mime="text/csv",
                        key="download_ms"
                    )
            elif result["text_path"]:
                with open(result["text_path"], "r", encoding="utf-8") as f:
                    text_data = f.read()

                with col2:
                    download_text = st.download_button(
                        label="Download Formatted Text File",
                        data=text_data,
                        file_name=os.path.basename(result["text_path"]),
                        mime="text/plain",
                        key="download_text"
                    )

            # Text report download or raw data as fallback
            if result["report_path"]:
                with open(result["report_path"], "r", encoding="utf-8") as f:
                    report_data = f.read()

                with col3:
                    download_report = st.download_button(
                        label="Download Text Report",
                        data=report_data,
                        file_name=os.path.basename(result["report_path"]),
                        mime="text/plain",
                        key="download_report"
                    )
            elif result["raw_data_path"]:
                with open(result["raw_data_path"], "r", encoding="utf-8") as f:
                    raw_data = f.read()

                with col3:
                    download_raw = st.download_button(
                        label="Download Raw Data File",
                        data=raw_data,
                        file_name=os.path.basename(result["raw_data_path"]),
                        mime="text/plain",
                        key="download_raw"
                    )

            # Now continue with portfolio statistics section
            st.header("Portfolio Statistics")

            # Calculate portfolio statistics
            stats = calculate_portfolio_statistics(df)

            if 'error' in stats:
                st.error(stats['error'])
                # Display raw dataframe columns to help debugging
                st.write("Available columns in the dataframe:", df.columns.tolist())
                # Display traceback if available
                if 'traceback' in stats:
                    with st.expander("Error details"):
                        st.code(stats['traceback'])
            else:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Summary")
                    st.metric(label="Total Portfolio Value", value=f"${stats['total_value']:,.2f}")
                    st.metric(label="Number of Holdings", value=stats['count'])
                    st.metric(label="Average Holding Value", value=f"${stats['avg_value']:,.2f}")
                    st.metric(label="Largest Holding", value=f"${stats['max_value']:,.2f}")
                    st.metric(label="Smallest Holding", value=f"${stats['min_value']:,.2f}")

                with col2:
                    st.subheader("Top Holdings")
                    # Get top 10 holdings
                    top_data = stats['holdings_pct'].head(10)

                    # Calculate "Others" only if more than 10 holdings
                    others_sum = stats['holdings_pct'].iloc[10:]['pct_of_total'].sum() if len(stats['holdings_pct']) > 10 else 0

                    # Add "Other" category if there are more than 10 holdings
                    if others_sum > 0:
                        others_row = pd.DataFrame({
                            'Symbol': ['OTHER'],
                            'Name': ['Other Holdings'],
                            'Value_numeric': [others_sum / 100 * stats['total_value']],
                            'pct_of_total': [others_sum]
                        })
                        display_data = pd.concat([top_data, others_row])
                    else:
                        display_data = top_data

                    # Create a table showing top holdings with percentages
                    # Increase the height of the dataframe to avoid scrolling
                    st.dataframe(
                        display_data[['Name', 'Symbol', 'pct_of_total']].rename(  # Swapped Name and Symbol order
                            columns={'pct_of_total': '% of Portfolio'}
                        ).reset_index(drop=True),
                        hide_index=True,
                        height=420  # Set a fixed height that should accommodate 10-11 rows
                    )

    else:
        # Show detailed instructions when no file is processed yet
        st.title("Empower Portfolio Extractor")

        st.markdown("""
        ### How to Use This Tool:

        1. **Get your portfolio data from Empower**:
           - Log in to your Empower Personal Dashboard account at [home.personalcapital.com](https://home.personalcapital.com)
           - Navigate to **Investing** → **Holdings** in the main menu
           - Wait for your portfolio holdings to fully load on the page
           - Exact process depends on your browser, but generally:
           - **Right-click** anywhere on the holdings section of the page
           - Select **Save Page As** from the context menu
           - In the save dialog, change the format to **Web Archive (.webarchive)**
           - Always choose **Web Archive** format, not **HTML**
           - Save the file to your computer

        2. **Process your data**:
           - Upload the .webarchive file using the file uploader in the sidebar ←
           - Click **Process WebArchive File** button
           - View your holdings data and download various file formats

        3. **Download options**:
           - CSV file - Complete portfolio data for spreadsheets
           - MorningStar CSV - Compatible with MorningStar's portfolio analyzer
           - Text Report - Detailed portfolio analysis text report
        """)

        # Add some helpful tips
        st.info("💡 **Tip**: This tool works entirely in your browser - your financial data never leaves your computer.")

    # Clean up temporary files after processing - no need to check file_selection_method anymore
    if file_path and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except:
            pass

    # Add a small footer to show user ID (optional)
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Session ID: {st.session_state.user_id}")

if __name__ == "__main__":
    main()
