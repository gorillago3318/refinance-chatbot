# backend/calculation.py

def calculate_repayment(loan_amount, loan_tenure_years, annual_interest_rate):
    """
    Calculate the monthly repayment amount for a loan.

    Parameters:
        loan_amount (float): Total loan amount.
        loan_tenure_years (int): Tenure of the loan in years.
        annual_interest_rate (float): Annual interest rate in percentage.

    Returns:
        float: Monthly repayment amount.
    """
    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = loan_tenure_years * 12
    if monthly_interest_rate == 0:
        return round(loan_amount / number_of_payments, 2)

    monthly_repayment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** (-number_of_payments))
    return round(monthly_repayment, 2)
