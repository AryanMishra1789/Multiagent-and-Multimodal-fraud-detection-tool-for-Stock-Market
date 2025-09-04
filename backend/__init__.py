# This file makes the directory a Python package
# It enables imports between modules in this directory

# Initialize DEFAULT_STOCK_DATA on import to ensure it's ready
try:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Ensure default stock data is initialized
    from announcement_utils import _initialize_default_data
    from announcement_utils_optimized import ultra_fast_stock_check
    
    # Log successful initialization
    logging.info("Backend package initialized successfully with optimized utilities")
except Exception as e:
    import logging
    logging.error(f"Error during initialization: {e}")
