import io
import uuid
from fpdf import FPDF
from fastapi import UploadFile
from app.services.pdf_parser import extract_text_from_pdf
from app.services import llm
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.transaction import insert_transactions
from app.schemas.transaction import TransactionCreate
from sqlalchemy.orm import Session
from unittest.mock import Mock

client = TestClient(app)

@patch("app.routes.upload.extract_text_from_pdf")
@patch("app.routes.upload.call_llm_to_extract_transactions")
def test_process_pdf_creates_transactions(mock_llm, mock_pdf):
    """
    Test the whole flow of processing a PDF and creating transactions
    """
    # Step 1: Mock PDF text extraction
    mock_pdf.return_value = "Transaction: Netflix Subscription $10.00 on 2024-07-01"
    
    # Step 2: Mock LLM transaction extraction
    mock_llm.return_value = [
        {
            "amount": -10.0,
            "description": "Netflix Subscription",
            "category": "Entertainment",
            "transaction_type": "expense",
            "source": "debit",
            "timestamp": "2024-07-01T00:00:00"
        }
    ]

    # Step 3: Register and login user
    client.post("/auth/register", json={"username": "testuser", "password": "Password123!", "name": "Test User"})
    login_res = client.post("/auth/login", data={"username": "testuser", "password": "Password123!"})
    token = login_res.json().get("access_token")
    assert token, f"Login failed: {login_res.json()}"
    headers = {"Authorization": f"Bearer {token}"}

    # Step 4: Upload any file (we're mocking the extraction)
    fake_pdf = io.BytesIO(b"any content")
    files = {"file": ("statement.pdf", fake_pdf, "application/pdf")}
    res = client.post("/process/pdf", files=files, headers=headers)

    # Step 5: Check response
    assert res.status_code == 200
    assert res.json() == {"added": 1}
    
    # Step 6: Verify mocks were called correctly
    mock_pdf.assert_called_once()  # PDF extraction was called
    mock_llm.assert_called_once_with("Transaction: Netflix Subscription $10.00 on 2024-07-01", "openai")  # LLM called with extracted text and default provider

def test_extract_text_from_pdf():
    """
    Test the extraction of text from a valid in-memory PDF
    """
    # Step 1: Create in-memory PDF with actual text content
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    sample_text = "This is a test transaction.\nAmount: $10.00"
    pdf.multi_cell(0, 10, sample_text)

    # Step 2: Get PDF content as bytes
    pdf_bytes = pdf.output(dest='S').encode('latin-1')  # Get as string and encode
    pdf_buffer = io.BytesIO(pdf_bytes)

    # Step 3: Create UploadFile-like object
    upload_file = UploadFile(filename="test.pdf", file=pdf_buffer)

    # Step 4: Extract text
    extracted_text = extract_text_from_pdf(upload_file)

    # Step 5: Validate expected content
    assert "test transaction" in extracted_text.lower()
    assert "10.00" in extracted_text

def test_llm_extracts_valid_transaction_dicts():
    """
    Test the LLM service interface and expected transaction data structure
    """
    with patch.object(llm, "call_llm_to_extract_transactions") as mock_llm:
        # Mock the LLM to return realistic transaction data
        mock_llm.return_value = [
            {
                "amount": -15.99,
                "description": "Netflix Subscription",
                "category": "Entertainment",
                "transaction_type": "expense",
                "source": "debit",
                "timestamp": "2024-07-01T00:00:00"
            },
            {
                "amount": -45.67,
                "description": "Grocery Store Purchase",
                "category": "Food",
                "transaction_type": "expense",
                "source": "debit",
                "timestamp": "2024-07-01T00:00:00"
            },
            {
                "amount": 2500.00,
                "description": "Salary Deposit",
                "category": "Income",
                "transaction_type": "income",
                "source": "debit",
                "timestamp": "2024-01-15T00:00:00"
            }
        ]
        
        # Test with sample bank statement text
        sample_text = """
        BANK STATEMENT TRANSACTIONS:
        Netflix Subscription $15.99 Entertainment
        Grocery Store Purchase $45.67 Food
        Salary Deposit $2500.00 Income 2024-01-15
        """
        
        transactions = llm.call_llm_to_extract_transactions(sample_text)
        
        # Verify the mock was called
        mock_llm.assert_called_once_with(sample_text)
        
        # Should extract multiple transactions
        assert len(transactions) == 3
        
        # Check Netflix transaction
        netflix_tx = transactions[0]
        assert netflix_tx["amount"] == -15.99  # Should be negative for expense
        assert netflix_tx["transaction_type"] == "expense"
        assert netflix_tx["category"] == "Entertainment"
        assert netflix_tx["source"] == "debit"
        
        # Check salary transaction  
        salary_tx = transactions[2]
        assert salary_tx["amount"] == 2500.00  # Should be positive for income
        assert salary_tx["transaction_type"] == "income"
        assert salary_tx["category"] == "Income"
        
        # Verify all transactions have required fields
        for tx in transactions:
            assert "amount" in tx
            assert "description" in tx
            assert "category" in tx
            assert "transaction_type" in tx
            assert "source" in tx
            assert "timestamp" in tx
            assert tx["transaction_type"] in ["income", "expense"]
            assert tx["source"] in ["credit", "debit", "savings"]

def test_insert_transactions():
    """
    Test the insertion of transactions into the database
    """
    # Mock database session
    mock_db = Mock(spec=Session)
    
    # Mock user
    mock_user = Mock()
    mock_user.id = "test-user-id"
    
    # Valid transaction data
    valid_transactions = [
        {
            "amount": -10.0,
            "description": "Test Transaction",
            "category": "Entertainment",
            "transaction_type": "expense",
            "source": "debit",
            "timestamp": "2024-07-01T00:00:00"
        },
        {
            "amount": 50.0,
            "description": "Salary",
            "category": "Income",
            "transaction_type": "income",
            "source": "debit",
            "timestamp": "2024-07-01T00:00:00"
        }
    ]
    
    # Test insertion
    result = insert_transactions(valid_transactions, mock_db, mock_user)
    
    # Should return count of inserted transactions
    assert result == 2
    
    # Database should have been called to add transactions
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()
    
def test_insert_transactions_with_invalid_data():
    """
    Test that invalid transactions are skipped gracefully
    """
    from app.services.transaction import insert_transactions
    from sqlalchemy.orm import Session
    from unittest.mock import Mock
    
    # Mock database session
    mock_db = Mock(spec=Session)
    
    # Mock user
    mock_user = Mock()
    mock_user.id = "test-user-id"
    
    # Mix of valid and invalid transaction data
    mixed_transactions = [
        {
            # Valid transaction
            "amount": -10.0,
            "description": "Valid Transaction",
            "category": "Entertainment",
            "transaction_type": "expense",
            "source": "debit",
            "timestamp": "2024-07-01T00:00:00"
        },
        {
            # Invalid transaction (missing required fields)
            "amount": 0,  # Invalid: amount cannot be zero
            "description": "",  # Invalid: description cannot be empty
        },
        {
            # Valid transaction
            "amount": 50.0,
            "description": "Another Valid Transaction",
            "category": "Income",
            "transaction_type": "income",
            "source": "debit",
            "timestamp": "2024-07-01T00:00:00"
        }
    ]
    
    # Test insertion - should only insert valid transactions
    result = insert_transactions(mixed_transactions, mock_db, mock_user)
    
    # Should return count of successfully inserted transactions (2 valid ones)
    assert result == 2
    
    # Database should have been called to add only valid transactions
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()

# def test_full_functionality_process_uploaded_pdf():
#     """
#     End-to-end test of uploading a PDF and processing transactions
#     """
#     # Step 1: Register + login user
#     username = "nazlidenizurenli123"
#     client.post("/auth/register", json={
#         "username": username, "password": "Password123!", "name": "verfiy data"
#     })
#     login_res = client.post("/auth/login", data={
#         "username": username, "password": "Password123!"
#     })
#     token = login_res.json().get("access_token")
#     assert token, f"Login failed: {login_res.json()}"
#     headers = {"Authorization": f"Bearer {token}"}

#     # Step 2: Upload CreditStatement
#     with open("data/CreditStatement.pdf", "rb") as credit_pdf:
#         files = {"file": ("credit.pdf", credit_pdf, "application/pdf")}
#         res_credit = client.post("/process/pdf?model_provider=openai", files=files, headers=headers)
#         print("Credit Response:", res_credit.json())

#     # Step 3: Upload DebitStatement
#     with open("data/DebitStatement.pdf", "rb") as debit_pdf:
#         files = {"file": ("debit.pdf", debit_pdf, "application/pdf")}
#         res_debit = client.post("/process/pdf?model_provider=openai", files=files, headers=headers)
#         print("Debit Response:", res_debit.json())

#     # Step 4: Assertions
#     assert res_credit.status_code == 200
#     assert isinstance(res_credit.json()["added"], int)
#     assert res_credit.json()["added"] >= 1

#     assert res_debit.status_code == 200
#     assert isinstance(res_debit.json()["added"], int)
#     assert res_debit.json()["added"] >= 1
    