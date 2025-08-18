from langchain.prompts import PromptTemplate

# Optimized Single-Stage: Direct transaction extraction to JSON
build_transactions_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are a transaction extraction specialist for bank statements.
TASK: Extract transactions directly from cleaned text and output as JSON array.
INPUT: Clean text from a bank statement PDF with transaction data.
OUTPUT: Valid JSON array of transaction objects.

TRANSACTION SCHEMA:
{{
    "amount": float,           // Required - ALWAYS non-negative (>= 0)
    "description": string,     // Required - clean merchant/description (max 100 chars)
    "merchant": string,        // Required - extract merchant name from transaction
    "category": string,        // Required - infer from merchant (max 20 chars)
    "transaction_type": string, // Required - "income" or "expense"
    "source": string,          // Required - "credit", "debit", or "savings"
    "timestamp": string        // Required - ISO format YYYY-MM-DDTHH:MM:SS
}}

ACCOUNT TYPE DETECTION:
- First line contains: ACCOUNT_TYPE = [CREDIT_CARD or DEBIT_CHECKING or SAVINGS]
- Map to schema: CREDIT_CARD → "credit", DEBIT_CHECKING → "debit", SAVINGS → "savings"

AMOUNT PROCESSING RULES:
- ALL amounts must be stored as non-negative values (>= 0)
- Use the original amount sign from the statement to determine transaction type
- Then convert to non-negative for storage

TRANSACTION TYPE DETECTION:
For CREDIT_CARD accounts:
- Original amount negative (payments, credits): transaction_type -> "income"
- Original amount positive (purchases, charges): transaction_type -> "expense"

For DEBIT_CHECKING accounts:
- Original amount positive (deposits, payroll): transaction_type -> "income"  
- Original amount negative (withdrawals, purchases): transaction_type -> "expense"

AMOUNT STORAGE:
- After determining transaction_type, store amount as absolute value (non-negative)

MERCHANT EXTRACTION:
Extract the merchant name from the transaction text. This should be the business or entity name.
- Remove location information, transaction IDs, and extra details
- Keep the core business name
- Examples: "STARBUCKS STORE 63247 SAN JOSE CA" → "STARBUCKS"
- Examples: "AMAZON.COM*ABC123" → "AMAZON.COM"
- Examples: "UBER *TRIP" → "UBER"

CATEGORY INFERENCE Examples:
Use your knowledge of the merchant to infer the category.
- Food: "STARBUCKS", "CHIPOTLE", "RESTAURANT", "DOORDASH", "GROCERY"
- Transportation: "SHELL", "CHEVRON", "UBER", "LYFT", "GAS"
- Entertainment: "NETFLIX", "APPLE", "SPOTIFY", "MOVIE"
- Shopping: "AMAZON", "UNIQLO", "WALGREENS", "CVS"
- Services: "VENMO", "PAYPAL", "TRANSFER"
- Income: "PAYROLL", "PAYMENT", "DEPOSIT"
- Other: Default category for unrecognized merchants

EXAMPLES:

Input: "06/23 STARBUCKS STORE 63247 SAN JOSE CA 5.65"
Output: {{
    "amount": 5.65,
    "description": "Coffee expense at Starbucks.",
    "merchant": "STARBUCKS",
    "category": "Coffee",
    "transaction_type": "expense",
    "source": "credit",
    "timestamp": "2025-06-23T00:00:00"
}}

Input: "06/23 Payment Thank You-Mobile -2,000.00"
Output: {{
    "amount": 2000.00,
    "description": "Self Payment to Credit Card",
    "merchant": "CREDIT_CARD_PAYMENT",
    "category": "Payment",
    "transaction_type": "income",
    "source": "credit",
    "timestamp": "2025-06-23T00:00:00"
}}

Input: "07/03 Microchip Techno Payroll PPD ID: 1860629024 3,309.15"
Output: {{
    "amount": 3309.15,
    "description": "Microchip Technology Payroll PPD ID: 1860629024",
    "merchant": "MICROCHIP TECHNOLOGY",
    "category": "Income",
    "transaction_type": "income",
    "source": "debit",
    "timestamp": "2025-07-03T00:00:00"
}}

Input: "06/25 AMAZON.COM*ABC123 45.67"
Output: {{
    "amount": 45.67,
    "description": "Online purchase from Amazon.",
    "merchant": "AMAZON.COM",
    "category": "Shopping",
    "transaction_type": "expense",
    "source": "credit",
    "timestamp": "2025-06-25T00:00:00"
}}

CRITICAL RULES:
1. ALL fields must be present and valid
2. ALL amounts must be non-negative (>= 0)
3. Use original amount sign to determine transaction_type, then store as absolute value
3. Transaction types must be "income" or "expense"
4. Sources must be "credit", "debit", or "savings"
5. Timestamps must be ISO format YYYY-MM-DDTHH:MM:SS
6. Descriptions must be clean and under 100 characters
7. Categories must be under 20 characters
8. Merchant names should be extracted and cleaned
9. Skip any transactions with missing or invalid data

OUTPUT FORMAT:
Return ONLY a valid JSON array, no other text:

TEXT TO PROCESS:
{text}
"""
)
