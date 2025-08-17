from langchain.prompts import PromptTemplate

# Stage 1: Clean and structure raw PDF text
build_transaction_blocks_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are a bank statement text preprocessor for Stage 2 of a 3-stage pipeline.
TASK: Formate cleaned data into transaction blocks.
INPUT: Clean text from a bank statement PDF with necessary information.
OUTPUT: Formatted transaction blocks.

1) Step 1: READ ACCOUNT TYPE:
The first line contains: ACCOUNT_TYPE = [CREDIT_CARD or DEBIT_CHECKING or SAVINGS]
Use this to determine the SOURCE field for all transactions.

2) Step 2: IDENTIFY AND FORMAT TRANSACTIONS
- Structure the transactions as blocks with the following format:

STRUCTURE:
TRANSACTION_START
DATE: xx/xx/xx
AMOUNT: xx.xx
SOURCE: CREDIT_CARD or DEBIT_CHECKING
TRANSACTION_TYPE: INCOME or EXPENSE
DESCRIPTION: xx
TRANSACTION_END

INSTRUCTIONS:
- Determine the source from the statement.
- All transactions in the same statement should have the same source.
- Extract Merchant Name or Transaction Description as DESCRIPTION. Do not infer or augment, only add the original data.
SOURCE: CREDIT_CARD
SOURCE: DEBIT_CHECKING

CRITICAL RULES:
- Use consistent field names (DATE, AMOUNT, SOURCE, TRANSACTION_TYPE, DESCRIPTION)
- PRESERVE ALL ORIGINAL DATA. DO NOT AUGMENT OR INFER, JUST FORMAT EXISTING DATA.
- Keep amounts with proper signs based on account type
- Do NOT create JSON - just clean, structured text.

EXAMPLES:
TRANSACTION_START
DATE: 07/15/25
AMOUNT: 5.65
SOURCE: CREDIT_CARD
TRANSACTION_TYPE: EXPENSE
DESCRIPTION: DD *DOORDASH FLOUR+WAT 855-431-0459 CA 
TRANSACTION_END

TRANSACTION_START
DATE: 07/15/25
AMOUNT: -100.00
SOURCE: CREDIT_CARD
TRANSACTION_TYPE: INCOME
DESCRIPTION: Payment Thank You-Mobile
TRANSACTION_END

TRANSACTION_START
DATE: 07/15/25
AMOUNT: -12.00
SOURCE: DEBIT_CHECKING
TRANSACTION_TYPE: EXPENSE
DESCRIPTION: Recurring Card Purchase 07/15 Coursera.Org Coursera.Org CA Card 4349 
TRANSACTION_END

TRANSACTION_START
DATE: 07/15/25
AMOUNT: 2000.00
SOURCE: DEBIT_CHECKING
TRANSACTION_TYPE: INCOME
DESCRIPTION: Microchip Techno Payroll PPD ID: 1860629024 
TRANSACTION_END

TRANSACTION TYPE RULES:
For CREDIT_CARD accounts:
- INCOME: Negative amounts
- EXPENSE: Positive amounts

For DEBIT_CHECKING accounts:
- INCOME: Positive amounts
- EXPENSE: Negative amounts

5) Step 5: Output Validation
- Make sure all transactions have non-zero amounts. Delete transaction block if amount is zero.
- Make sure all transactions have a date. Delete transaction block if date is missing.
- Make sure all transactions have a merchant/payee description. Delete transaction block if description is missing.
- Make sure all transactions have a source. Delete transaction block if source is missing.
- Make sure all transactions have a correct transaction type. If type is not matching the source, delete the transaction block.

TEXT TO PROCESS:
{text}
"""
)
