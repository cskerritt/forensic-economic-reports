"""
Life Expectancy Client

This module provides a client for life expectancy calculations.
The external Life Expectancy API has been removed, and this now uses local calculations.
"""

import logging
from ..utils.csv_lookups import lookup_worklife_values

logger = logging.getLogger(__name__)

class LifeExpectancyClient:
    """Client for life expectancy calculations."""

    def __init__(self, base_url=None):
        """
        Initialize the client.

        Args:
            base_url: Kept for backward compatibility but not used
        """
        # base_url parameter is kept for backward compatibility but not used
        logger.info("Initialized Life Expectancy client (using local calculations)")

    def get_life_expectancy(self, gender, race, age):
        """
        Get life expectancy using local calculations.

        Args:
            gender (str): Gender ('Men', 'Women', etc.)
            race (str): Race (not used in local calculations)
            age (float): Age in years

        Returns:
            dict: Life expectancy data or None if an error occurred
        """
        try:
            # Use local worklife expectancy tables
            education_level = None  # Default to None since we don't have this info
            wle_value, _ = lookup_worklife_values(gender, education_level, float(age))

            if wle_value is not None:
                total_years = float(age) + wle_value

                # Create a response similar to what the API would have returned
                result = {
                    'success': True,
                    'input': {
                        'gender': gender,
                        'race': race,
                        'age': float(age)
                    },
                    'results': {
                        'additionalYears': wle_value,
                        'totalYears': total_years
                    }
                }

                logger.info(f"Calculated life expectancy data locally: {result}")
                return result
            else:
                logger.error("Could not calculate life expectancy with local tables")
                return None

        except Exception as e:
            logger.error(f"Unexpected error when calculating life expectancy: {str(e)}")
            return None

# Create a singleton instance
life_expectancy_client = LifeExpectancyClient()
