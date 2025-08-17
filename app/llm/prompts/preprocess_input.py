from langchain.prompts import PromptTemplate

# Stage 0: Clean raw PDF text by removing legal content and metadata
preprocess_input_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are a text cleaning specialist for Stage 0 of a 3-stage transaction processing pipeline.

TASK: 
1. First, determine the account type from the raw text
2. Then, clean the text by removing legal content while preserving transaction data

INPUT: Raw, messy text extracted from bank statement PDF

STEP 1 - DETERMINE ACCOUNT TYPE:
Look for indicators such as:
- "Credit Card", "CHASE FREEDOM", "Card Services" → CREDIT_CARD
- "Checking", "College Checking", "Debit" → DEBIT_CHECKING
- "Savings" → SAVINGS

Write the account type in the output as first line.
ACCOUNT_TYPE = [CREDIT_CARD or DEBIT_CHECKING or SAVINGS]

STEP 2 - CLEAN TEXT:
REMOVE:
- Legal disclaimers and terms of service
- Website URLs and phone numbers
- Customer service information
- Page headers, footers, page numbers
- Account agreements and policy text
- Error resolution procedures
- Payment instructions ("Making Your Payments:", "How To Avoid Paying Interest")
- Credit rights explanations
- Interest rate tables and APR information
- Any text that looks like legal/policy language
- Personal information (account holder names, addresses)
- Section titles and headers
- Blank page indicators ("This Page Intentionally Left Blank")

PRESERVE:
- All transaction data. These are date with date, amounts, and merchant names
- Transaction descriptions and details
- Provide information about account type and source but this should be inferred and briefly mentioned.
- Any text that contains financial transaction information

EXAMPLE OF WHAT TO REMOVE:
"If you think there is an error on your statement, write to us on a separate sheet..."
"We will determine whether an error occurred within 10 business days..."
"For errors involving new accounts, point-of-sale, or foreign-initiated transactions..."

EXAMPLE OF WHAT TO KEEP:
"06/23 STARBUCKS STORE 63247 SAN JOSE CA 5.65"
"Payment Thank You-Mobile -2,000.00"

OUTPUT: Return only the cleaned text with transaction-relevant content.

RAW TEXT TO CLEAN:
{text}
"""
)
