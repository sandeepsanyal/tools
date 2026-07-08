from datetime import datetime
import os
import sys
from typing import Literal

import numpy as np

try:
    from .utils import format_indian_number
except ImportError:
    # Allows this file to also be run directly (script / interactive cell),
    # where there is no package context for a relative import to resolve.
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils import format_indian_number

def compounder_calculator(
    principal: float,
    maturity_amount: float,
    tenure: float,
    compounding_frequency: int
) -> float:
    """
    Calculate the compounded annual rate of return (XIRR) based on principal, maturity amount, tenure, and compounding frequency.

    Parameters:
    principal (float): The initial investment amount.
    maturity_amount (float): The amount of money accumulated after a certain period, including interest.
    tenure (float): The time period over which the investment is held, in years.
    compounding_frequency (int): The number of times interest compounds per year
        (e.g. 1 for yearly compounding like PPF, 4 for quarterly compounding like most bank FDs/RDs, 12 for monthly).

    Returns:
    float: The compounded annual rate of return (XIRR) as a percentage, expressed at the same
        compounding_frequency passed in (i.e. it is the nominal annual rate, not the effective annual rate).

    Example:
    >>> round(compounder_calculator(100, 113, 1, 1), 1)
    13.0
    """
    rate = (
        np.exp(
            np.log(maturity_amount/principal) / (compounding_frequency*tenure)
        ) - 1
    ) * (100 * compounding_frequency)

    return float(rate)

def maturity_compounded(
    principal: float,
    XIRR: float,
    tenure: float,
    compounding_frequency: int
) -> float:
    """
    Calculate the maturity amount of an investment with compound interest.

    Parameters:
    principal (float): The initial investment amount.
    XIRR (float): The nominal annual interest rate, as a percentage (e.g. pass 7 for 7%, not 0.07).
    tenure (float): The time period over which the investment is held, in years.
    compounding_frequency (int): The number of times interest compounds per year
        (e.g. 1 for yearly compounding like PPF, 4 for quarterly compounding like most bank FDs/RDs, 12 for monthly).

    Returns:
    float: The maturity amount after the specified tenure with compound interest.

    Example:
    >>> round(maturity_compounded(100000, 2.935, 1, 1), 2)
    102935.0
    >>> round(maturity_compounded(100000, 7, 12, 4), 2)  # bank-style quarterly compounding
    229959.87
    >>> round(maturity_compounded(100000, 7, 12, 1), 2)  # PPF-style yearly compounding
    225219.16
    """
    maturity_amount = principal * pow(
        base=1 + (XIRR / (100 * compounding_frequency)),
        exp=compounding_frequency * tenure
    )

    return maturity_amount

def sip_calculator(
    principal: float,
    XIRR: float,
    tenure: float,
    investment_frequency: Literal['monthly', 'quarterly', 'yearly'],
    initial_investment: float = 0
) -> float:
    """
    Calculate the future value of a SIP (Systematic Investment Plan) investment.

    Note: interest is assumed to compound at the same frequency as the contributions
    (e.g. a monthly SIP compounds monthly) — there is currently no independent
    compounding_frequency input, unlike compounder_calculator/maturity_compounded.

    Parameters:
    principal (float): The amount invested at each interval.
    XIRR (float): The nominal annual interest rate, as a percentage (e.g. pass 11.3 for 11.3%, not 0.113).
    tenure (float): The number of years the investment will be held.
    investment_frequency ('monthly' | 'quarterly' | 'yearly'): The frequency of investments,
        which also doubles as the compounding frequency (see note above).
    initial_investment (float, optional): The initial lump sum investment. Defaults to 0.

    Returns:
    float: The future value of the investment.

    Example:
    >>> round(sip_calculator(
    ...     principal=100,
    ...     XIRR=11.3,  # this is 11.3%
    ...     tenure=1,   # this is 1 year
    ...     investment_frequency="monthly"
    ... ), 2)
    1264.14
    """
    XIRR = XIRR/100
    
    # Convert yearly rate to the appropriate interval rate
    if investment_frequency == 'monthly':
        interval_rate = XIRR / 12
        num_intervals = tenure * 12
    elif investment_frequency == 'quarterly':
        interval_rate = XIRR / 4
        num_intervals = tenure * 4
    elif investment_frequency == 'yearly':
        interval_rate = XIRR
        num_intervals = tenure
    else:
        raise ValueError("Invalid investment frequency. Choose 'monthly', 'quarterly', or 'yearly'.")

    # Calculate the future value of the SIP
    future_value_sip = principal * ((1 + interval_rate) ** num_intervals - 1) / interval_rate

    # Calculate the future value of the initial investment
    future_value_initial = initial_investment * (1 + interval_rate) ** num_intervals

    # Total future value
    total_future_value = future_value_sip + future_value_initial

    return total_future_value







# uses
print("{}%".format(round(compounder_calculator(
    principal=100,
    maturity_amount=200,
    tenure=10,
    compounding_frequency=1
),2)))

print(format_indian_number(maturity_compounded(
    principal=1_00_000,
    XIRR=7.18,
    tenure=10,
    compounding_frequency=1
)))

print(format_indian_number(sip_calculator(
    initial_investment=4_25_200,
    principal=300_000,
    XIRR=7.1,
    tenure=abs(
        (
            datetime.strptime("2036-01-14", "%Y-%m-%d")\
            - datetime.now()
        ).days
    )/365,
    investment_frequency="yearly"
)))


