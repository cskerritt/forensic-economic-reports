from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Optional, Tuple, Dict, Any, List, Union
import pandas as pd
from dateutil.relativedelta import relativedelta
import os
import decimal
import logging
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Set up logger
logger = logging.getLogger(__name__)

# Define custom exceptions for better error handling
class CalculationError(Exception):
    """Base exception for calculation errors."""
    pass

class InputValidationError(CalculationError):
    """Exception for invalid input data."""
    pass

class NumericConversionError(CalculationError):
    """Exception for errors in numeric conversions."""
    pass

class DateValidationError(CalculationError):
    """Exception for date validation errors."""
    pass

# Configure decimal context
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP

# Default configuration values
DEFAULT_CONFIG = {
    "worklife_adjustment": Decimal("0.919"),
    "unemployment_adjustment": Decimal("0.965"),
    "income_tax_adjustment": Decimal("0.88"),
    "personal_consumption_pre_2016": Decimal("0.75"),
    "personal_consumption_post_2016": Decimal("0.80"),
    "growth_rate": Decimal("0.031"),
    "discount_rate": Decimal("0.0325")
}

def parse_mdy(date_str: str) -> Optional[datetime]:
    """Parses MM/DD/YYYY. Returns None if invalid/empty."""
    if not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except ValueError:
        return None

def add_decimal_years(base_date: datetime, decimal_years: Decimal) -> datetime:
    """Adds decimal years to a date (e.g. 25.5 => 25 years + ~6 months)."""
    whole_years = int(decimal_years)
    fraction = decimal_years - whole_years
    months = int(round(fraction * Decimal("12")))
    return base_date + relativedelta(years=whole_years, months=months)

def format_currency(value: Decimal) -> str:
    """Format decimal as currency string."""
    return f"${value:,.2f}"

def format_percentage(value: Decimal) -> str:
    """Format decimal as percentage string."""
    return f"{value:,.2f}%"

def calculate_worklife_factor(wle_years: float, yfs_years: float) -> Optional[Decimal]:
    """Calculate worklife factor based on work life expectancy and years to final separation."""
    try:
        if wle_years <= 0 or yfs_years <= 0:
            return None
        return Decimal(str(wle_years)) / Decimal(str(yfs_years))
    except (ValueError, ZeroDivisionError):
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(CalculationError),
    reraise=True
)
def calculate_aef(
    gross_earnings_base: float,
    worklife_adjustment: float,
    unemployment_factor: float,
    fringe_benefit: float,
    tax_liability: float,
    wrongful_death: bool = False,
    personal_type: str = "",
    personal_percentage: float = 0.0
) -> Tuple[pd.DataFrame, Decimal]:
    """
    Calculate Annual Earnings Factor with detailed steps.

    Args:
        gross_earnings_base: Base annual earnings
        worklife_adjustment: Worklife adjustment factor (decimal)
        unemployment_factor: Unemployment factor (decimal)
        fringe_benefit: Fringe benefit factor (decimal)
        tax_liability: Tax liability factor (decimal)
        wrongful_death: Whether this is a wrongful death case
        personal_type: Type of personal consumption (for wrongful death)
        personal_percentage: Personal consumption percentage (decimal)

    Returns:
        Tuple containing calculation steps DataFrame and final AEF value

    Raises:
        InputValidationError: If input values are invalid
        NumericConversionError: If numeric conversion fails
        CalculationError: For other calculation errors
    """
    try:
        # Input validation
        if gross_earnings_base < 0:
            raise InputValidationError("Gross earnings base cannot be negative")
        if worklife_adjustment < 0 or worklife_adjustment > 1:
            raise InputValidationError("Worklife adjustment must be between 0 and 1")
        if unemployment_factor < 0 or unemployment_factor > 1:
            raise InputValidationError("Unemployment factor must be between 0 and 1")
        if fringe_benefit < 0:
            raise InputValidationError("Fringe benefit cannot be negative")
        if tax_liability < 0 or tax_liability > 1:
            raise InputValidationError("Tax liability must be between 0 and 1")
        if personal_percentage < 0 or personal_percentage > 1:
            raise InputValidationError("Personal consumption percentage must be between 0 and 1")

        # Convert inputs to Decimal for precise calculations
        try:
            gross_base = Decimal(str(gross_earnings_base))
            worklife_adj = Decimal(str(worklife_adjustment))
            unemp_factor = Decimal(str(unemployment_factor))
            fringe = Decimal(str(fringe_benefit))
            tax = Decimal(str(tax_liability))
            personal_adj = Decimal(str(personal_percentage)) if personal_percentage > 0 else Decimal('0')
        except (ValueError, decimal.InvalidOperation) as e:
            logger.error(f"Numeric conversion error in AEF calculation: {e}")
            raise NumericConversionError(f"Failed to convert input values: {e}")

        # Step-by-step calculations with validation
        try:
            adjusted_base_earnings = gross_base * worklife_adj * (Decimal('1.0') - unemp_factor)
            tax_adjusted_earnings = adjusted_base_earnings * (Decimal('1.0') - tax)
            final_adjusted_earnings = tax_adjusted_earnings * (Decimal('1.0') + fringe)

            # Apply personal consumption adjustment if wrongful death case
            if wrongful_death and personal_adj > 0:
                final_adjusted_earnings = final_adjusted_earnings * (Decimal('1.0') - personal_adj)

            # Validate final result
            if final_adjusted_earnings < 0:
                logger.warning(f"Negative AEF calculated: {final_adjusted_earnings}")
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            logger.error(f"Calculation error in AEF: {e}")
            raise CalculationError(f"Error during AEF calculation: {e}")

        # Create calculation steps table
        steps = []
        steps.append(("Gross Earnings Base", gross_base * Decimal('100')))
        steps.append(("x Worklife Adjustment", worklife_adj * Decimal('100')))
        steps.append((f"x (1 - {unemp_factor * Decimal('100'):.2f}% Unemployment Factor)",
                     (Decimal('1.0') - unemp_factor) * Decimal('100')))
        steps.append(("= Adjusted Base Earnings", adjusted_base_earnings * Decimal('100')))
        steps.append((f"x (1 - {tax * Decimal('100'):.2f}% Tax Liabilities)",
                     (Decimal('1.0') - tax) * Decimal('100')))
        steps.append((f"x (1 + {fringe * Decimal('100'):.2f}% Fringe Benefits)",
                     (Decimal('1.0') + fringe) * Decimal('100')))
        steps.append(("= Fringe Benefits/Tax Adjusted Earnings Base",
                     final_adjusted_earnings * Decimal('100')))

        if wrongful_death and personal_adj > 0:
            steps.append((f"x (1 - {personal_adj * Decimal('100'):.2f}% Personal Consumption)",
                         (Decimal('1.0') - personal_adj) * Decimal('100')))

        steps.append(("AEF", final_adjusted_earnings * Decimal('100')))

        # Create DataFrame
        try:
            df = pd.DataFrame(steps, columns=['Step', 'Amount'])
            df['Amount'] = df['Amount'].apply(lambda x: f"{x:.2f}%")
        except Exception as e:
            logger.error(f"Error creating AEF DataFrame: {e}")
            raise CalculationError(f"Error creating calculation table: {e}")

        logger.info(f"AEF calculation successful: {final_adjusted_earnings}")
        return df, final_adjusted_earnings

    except InputValidationError as e:
        logger.error(f"AEF input validation error: {e}")
        raise
    except NumericConversionError as e:
        logger.error(f"AEF numeric conversion error: {e}")
        raise
    except CalculationError as e:
        logger.error(f"AEF calculation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in AEF calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in AEF calculation: {e}")

def compute_adjusted_income_factor(year: int, config: dict = DEFAULT_CONFIG) -> Decimal:
    """Compute the adjusted income factor based on the year."""
    worklife_adj = Decimal(str(config["worklife_adjustment"]))
    unemployment_adj = Decimal(str(config["unemployment_adjustment"]))
    tax_adj = Decimal(str(config["income_tax_adjustment"]))

    if year <= 2015:
        personal_consumption = Decimal(str(config["personal_consumption_pre_2016"]))
    else:
        personal_consumption = Decimal(str(config["personal_consumption_post_2016"]))

    return worklife_adj * unemployment_adj * tax_adj * personal_consumption

def compute_present_value(
    amount: Decimal,
    discount_rate: Decimal,
    years_from_ref: Decimal
) -> Decimal:
    """Compute present value given an amount, discount rate, and years from reference."""
    try:
        if discount_rate == Decimal("0"):
            return amount
        factor = (Decimal("1") + discount_rate) ** (-years_from_ref)
        return amount * factor
    except (ValueError, ZeroDivisionError):
        return Decimal("0")

def calculate_age(birth_date: datetime, current_date: datetime) -> Decimal:
    """Calculate decimal age at a given date."""
    days_in_year = 366 if current_date.year % 4 == 0 else 365
    age_days = (current_date - birth_date).days
    return Decimal(str(age_days)) / Decimal("365.25")

def export_to_excel(df: pd.DataFrame, filename: str, include_discounting: bool = True) -> str:
    """Export earnings table to Excel with formatting."""
    try:
        # Create a copy of the DataFrame to modify
        export_df = df.copy()

        # Drop Present Value column if discounting is not included
        if not include_discounting and 'Present Value' in export_df.columns:
            export_df = export_df.drop(columns=['Present Value'])

        # Create Excel writer with xlsxwriter engine
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Write to Excel
            export_df.to_excel(writer, index=False, sheet_name='Earnings Analysis')

            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Earnings Analysis']

            # Add totals row
            last_row = len(export_df) + 2  # +2 for header and 1-based indexing
            total_row = last_row + 1

            # Get column letters for formatting
            for idx, col in enumerate(export_df.columns):
                col_letter = chr(65 + idx)  # A, B, C, etc.

                # Set column width
                worksheet.column_dimensions[col_letter].width = 18

                # Format cells based on content type
                if col in ['Wage Base Years', 'Residual Earning Capacity', 'Gross Earnings', 'Loss', 'Present Value']:
                    # Currency format for data cells
                    for row in range(2, last_row):
                        cell = f"{col_letter}{row}"
                        worksheet[cell].number_format = '$#,##0.00'

                    # Add sum formula only for Loss and Present Value columns
                    if col in ['Loss', 'Present Value']:
                        sum_cell = f"{col_letter}{total_row}"
                        worksheet[sum_cell] = f'=SUM({col_letter}2:{col_letter}{last_row-1})'
                        worksheet[sum_cell].number_format = '$#,##0.00'

                elif col == 'Portion of Year':
                    # Percentage format
                    for row in range(2, last_row):
                        cell = f"{col_letter}{row}"
                        worksheet[cell].number_format = '0.00%'

                elif col == 'Age':
                    # Decimal format
                    for row in range(2, last_row):
                        cell = f"{col_letter}{row}"
                        worksheet[cell].number_format = '0.00'

            # Add "Totals" label
            worksheet[f'A{total_row}'] = 'Totals'

            # Add borders and bold font to totals row
            for col in range(len(export_df.columns)):
                col_letter = chr(65 + col)  # Fixed: use col instead of idx
                cell = worksheet[f'{col_letter}{total_row}']
                cell.font = cell.font.copy(bold=True)

            # Add column numbers in parentheses
            for idx, col in enumerate(export_df.columns, 1):
                cell = worksheet[f'{chr(64 + idx)}1']
                cell.value = f"{cell.value} ({idx})"
                cell.font = cell.font.copy(bold=True)

        return filename
    except Exception as e:
        print(f"Error exporting to Excel: {str(e)}")
        return ""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(CalculationError),
    reraise=True
)
def compute_earnings_table(
    start_date: datetime,
    end_date: datetime,
    wage_base: float,
    residual_base: float,
    growth_rate: float,
    discount_rate: Optional[float],
    adjustment_factor: float,
    date_of_birth: Optional[datetime] = None,
    reference_start: Optional[datetime] = None,
    config: dict = DEFAULT_CONFIG,
    include_discounting: bool = True,
    offset_wages: dict = None,
    career_progressions: dict = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Decimal, Decimal]:
    """
    Compute earnings table with growth and present value calculations.

    Args:
        start_date: Start date for the calculation period
        end_date: End date for the calculation period
        wage_base: Base annual wage
        residual_base: Residual earning capacity
        growth_rate: Annual growth rate (decimal)
        discount_rate: Discount rate for present value calculations (decimal)
        adjustment_factor: Adjustment factor for earnings (percentage)
        date_of_birth: Date of birth for age calculations
        reference_start: Reference date for present value calculations
        config: Configuration dictionary
        include_discounting: Whether to include present value calculations
        offset_wages: Dictionary of {year: amount} for specific wage offsets
        career_progressions: Dictionary of {year: increase} for career progression

    Returns:
        Tuple containing raw data DataFrame, display DataFrame, total present value, and total loss

    Raises:
        DateValidationError: If date inputs are invalid
        InputValidationError: If numeric inputs are invalid
        NumericConversionError: If numeric conversion fails
        CalculationError: For other calculation errors
    """
    try:
        # Input validation for dates
        if not isinstance(start_date, datetime):
            raise DateValidationError("Start date must be a datetime object")
        if not isinstance(end_date, datetime):
            raise DateValidationError("End date must be a datetime object")
        if start_date > end_date:
            raise DateValidationError("Start date cannot be after end date")
        if date_of_birth and not isinstance(date_of_birth, datetime):
            raise DateValidationError("Date of birth must be a datetime object")
        if date_of_birth and date_of_birth > start_date:
            raise DateValidationError("Date of birth cannot be after start date")
        if reference_start and not isinstance(reference_start, datetime):
            raise DateValidationError("Reference start date must be a datetime object")

        # Input validation for numeric values
        if wage_base < 0:
            raise InputValidationError("Wage base cannot be negative")
        if residual_base < 0:
            raise InputValidationError("Residual base cannot be negative")
        if adjustment_factor <= 0:
            raise InputValidationError("Adjustment factor must be positive")
        if growth_rate < -1:  # Allow negative growth but not less than -100%
            raise InputValidationError("Growth rate cannot be less than -100%")
        if include_discounting and discount_rate is not None and discount_rate < 0:
            raise InputValidationError("Discount rate cannot be negative")

        # Convert inputs to Decimal with validation
        try:
            annual_wage = Decimal(str(wage_base))
            residual = Decimal(str(residual_base))
            growth = Decimal(str(growth_rate))
            adj_factor = Decimal(str(adjustment_factor)) / Decimal("100")  # Convert percentage to decimal

            if include_discounting and discount_rate is not None:
                discount = Decimal(str(discount_rate))
            else:
                discount = None
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            logger.error(f"Numeric conversion error in earnings table: {e}")
            raise NumericConversionError(f"Failed to convert input values: {e}")

        # Initialize calculations
        raw_data = []  # For Excel export
        display_data = []  # For web display
        total_pv = Decimal("0")
        total_loss = Decimal("0")

        current_date = start_date
        ref_date = reference_start or start_date
        current_wage = annual_wage
        current_residual = residual

        # Process offset wages
        offset_wages_dict = {}
        if offset_wages:
            try:
                for year, amount in offset_wages.items():
                    year_int = int(year)
                    if year_int < start_date.year or year_int > end_date.year:
                        raise InputValidationError(f"Offset wage year {year} is outside scenario date range")
                    if amount < 0:
                        raise InputValidationError(f"Offset wage amount cannot be negative for year {year}")
                    offset_wages_dict[year_int] = Decimal(str(amount))
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.error(f"Error processing offset wages: {e}")
                raise NumericConversionError(f"Invalid offset wage data: {e}")

        # Process career progressions
        career_progressions_dict = {}
        if career_progressions:
            try:
                for year, increase in career_progressions.items():
                    year_int = int(year)
                    if year_int < start_date.year or year_int > end_date.year:
                        raise InputValidationError(f"Career progression year {year} is outside scenario date range")
                    if increase < 0:
                        raise InputValidationError(f"Career progression increase cannot be negative for year {year}")
                    career_progressions_dict[year_int] = Decimal(str(increase))
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.error(f"Error processing career progressions: {e}")
                raise NumericConversionError(f"Invalid career progression data: {e}")

        # Track previous year for validation
        prev_year = None

        # Main calculation loop
        try:
            while current_date <= end_date:
                year = current_date.year

                # Calculate portion of year
                if year == start_date.year:
                    year_start = start_date
                    year_end = datetime(year, 12, 31)
                elif year == end_date.year:
                    year_start = datetime(year, 1, 1)
                    year_end = end_date
                else:
                    year_start = datetime(year, 1, 1)
                    year_end = datetime(year, 12, 31)

                # Validate year progression
                if prev_year and year <= prev_year:
                    raise CalculationError(f"Invalid year progression: {prev_year} to {year}")
                prev_year = year

                # Calculate exact days for portion with validation
                days_in_year = 366 if year % 4 == 0 else 365
                days_in_period = (min(year_end, end_date) - year_start).days + 1
                if days_in_period <= 0:
                    raise CalculationError(f"Invalid period days calculation for year {year}")
                portion = Decimal(str(days_in_period)) / Decimal(str(days_in_year))

                # Validate portion
                if portion <= 0 or portion > 1:
                    raise CalculationError(f"Invalid portion of year calculated: {portion}")

                # Calculate age if birth date provided
                age = calculate_age(date_of_birth, year_start) if date_of_birth else None
                if age and age < 0:
                    raise CalculationError(f"Invalid age calculated: {age}")

                # Apply growth rate at the start of each year after the first year
                if year > start_date.year:
                    current_wage *= (Decimal("1") + growth)
                    current_residual *= (Decimal("1") + growth)

                # Apply career progression increases if available for this year
                if year in career_progressions_dict:
                    progression_increase = career_progressions_dict[year]
                    current_wage *= (Decimal("1") + progression_increase)
                    # Note: We don't apply progression to residual wages

                # Calculate period base wage with portion
                period_base = current_wage * portion

                # Calculate adjusted wage using adjustment factor
                period_adjusted = period_base * adj_factor

                # Apply offset wages if available for this year
                if year in offset_wages_dict:
                    period_residual = offset_wages_dict[year] * portion
                else:
                    period_residual = current_residual * portion

                # Calculate loss
                period_loss = period_adjusted - period_residual

                # Calculate present value if discounting is enabled
                if include_discounting and discount is not None:
                    years_from_ref = Decimal(str((year_start - ref_date).days)) / Decimal("365.25")
                    pv = compute_present_value(period_loss, discount, years_from_ref)
                else:
                    pv = period_loss

                # Store raw values for Excel export
                raw_row = {
                    "Year": year,
                    "Portion of Year": float(portion),
                    "Age": float(age) if age is not None else None,
                    "Wage Base Years": float(period_base),
                    "Residual Earning Capacity": float(period_residual),
                    "Gross Earnings": float(period_adjusted),
                    "Loss": float(period_loss)
                }

                if include_discounting:
                    raw_row["Present Value"] = float(pv)

                # Store formatted values for display
                display_row = {
                    "Year": year,
                    "Portion of Year": "{:.2%}".format(float(portion)),
                    "Age": f"{float(age):.2f}" if age is not None else "",
                    "Wage Base Years": format_currency(period_base),
                    "Residual Earning Capacity": format_currency(period_residual),
                    "Gross Earnings": format_currency(period_adjusted),
                    "Loss": format_currency(period_loss)
                }

                if include_discounting:
                    display_row["Present Value"] = format_currency(pv)

                raw_data.append(raw_row)
                display_data.append(display_row)

                # Update totals
                total_pv += pv
                total_loss += period_loss

                if year_end >= end_date:
                    break

                current_date = year_end + relativedelta(days=1)
        except (decimal.DivisionByZero, decimal.InvalidOperation) as e:
            logger.error(f"Calculation error in earnings table: {e}")
            raise CalculationError(f"Error during earnings calculation: {e}")

        # Final validation of totals
        if len(raw_data) == 0:
            raise CalculationError("No data points calculated")

        # Create DataFrames
        try:
            raw_df = pd.DataFrame(raw_data)
            display_df = pd.DataFrame(display_data)
        except Exception as e:
            logger.error(f"Error creating earnings DataFrames: {e}")
            raise CalculationError(f"Error creating calculation tables: {e}")

        logger.info(f"Earnings table calculation successful: {len(raw_data)} periods, total loss: {total_loss}")
        return raw_df, display_df, total_pv, total_loss

    except DateValidationError as e:
        logger.error(f"Date validation error in earnings table: {e}")
        raise
    except InputValidationError as e:
        logger.error(f"Input validation error in earnings table: {e}")
        raise
    except NumericConversionError as e:
        logger.error(f"Numeric conversion error in earnings table: {e}")
        raise
    except CalculationError as e:
        logger.error(f"Calculation error in earnings table: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in earnings table calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in earnings calculation: {e}")
        return pd.DataFrame(), pd.DataFrame(), Decimal("0"), Decimal("0")