

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from app.crud import leaderboards as lb_crud
from app.models.transaction import TransactionModel


class TestLeaderboardsCRUD:
    
    @pytest.fixture
    def test_user_id(self) -> UUID:
        return uuid4()
    
    @pytest.fixture
    def test_timeframe(self) -> tuple[datetime, datetime]:
        end = datetime.now(timezone.utc).replace(microsecond=0)
        start = end - timedelta(days=7)
        return start, end
    
    @pytest.fixture
    def sample_transactions(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime]) -> list[TransactionModel]:
        start, end = test_timeframe
        
        transactions = [
            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=10.00,
                description="Coffee at Starbucks",
                category="Food",
                merchant="STARBUCKS",
                transaction_type="expense",
                source="credit",
                timestamp=start + timedelta(days=1)
            ),
            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=20.00,
                description="Lunch at Starbucks", 
                category="Food",
                merchant="STARBUCKS",
                transaction_type="expense",
                source="debit",
                timestamp=start + timedelta(days=2)
            ),
            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=30.00,
                description="Dinner at McDonalds",
                category="Food", 
                merchant="MCDONALDS",
                transaction_type="expense",
                source="credit",
                timestamp=start + timedelta(days=3)
            ),
            

            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=15.00,
                description="Netflix subscription",
                category="Entertainment",
                merchant="NETFLIX", 
                transaction_type="expense",
                source="credit",
                timestamp=start + timedelta(days=2)
            ),
            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=25.00,
                description="Spotify premium",
                category="Entertainment",
                merchant="SPOTIFY",
                transaction_type="expense", 
                source="credit",
                timestamp=start + timedelta(days=4)
            ),
            

            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=50.00,
                description="Uber ride",
                category="Transportation",
                merchant="UBER",
                transaction_type="expense",
                source="debit", 
                timestamp=start + timedelta(days=5)
            ),
            

            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=1000.00,
                description="Salary deposit",
                category="Income",
                merchant="EMPLOYER",
                transaction_type="income",
                source="debit",
                timestamp=start + timedelta(days=1)
            ),
            

            TransactionModel(
                id=uuid4(),
                user_id=test_user_id,
                amount=100.00,
                description="Old transaction",
                category="Food",
                merchant="OLD_MERCHANT",
                transaction_type="expense",
                source="credit",
                timestamp=start - timedelta(days=1)
            ),
            

            TransactionModel(
                id=uuid4(),
                user_id=uuid4(),
                amount=999.00,
                description="Other user transaction",
                category="Food",
                merchant="OTHER_MERCHANT", 
                transaction_type="expense",
                source="credit",
                timestamp=start + timedelta(days=2)
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        return transactions


class TestCategoryLeaderboards(TestLeaderboardsCRUD):
    
    def test_top_categories_by_total_value(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        start, end = test_timeframe
        
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=3)
        assert len(results) == 3
        
        assert results[0]["category"] == "Food"
        assert results[0]["amount"] == 60.00
        
        assert results[1]["category"] == "Transportation" 
        assert results[1]["amount"] == 50.00
        
        assert results[2]["category"] == "Entertainment"
        assert results[2]["amount"] == 40.00
    
    def test_top_categories_by_tx_count(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test category ranking by transaction count."""
        start, end = test_timeframe
        
        results = lb_crud.top_categories_by_tx_count(db_session, test_user_id, start, end, limit=3)
        
        # Expected order: Food (3 transactions), Entertainment (2), Transportation (1)
        assert len(results) == 3
        
        assert results[0]["category"] == "Food"
        assert results[0]["amount"] == 3.0  # Count as float
        
        assert results[1]["category"] == "Entertainment"
        assert results[1]["amount"] == 2.0
        
        assert results[2]["category"] == "Transportation" 
        assert results[2]["amount"] == 1.0
    
    def test_top_categories_by_avg_cost(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test category ranking by average transaction cost."""
        start, end = test_timeframe
        
        results = lb_crud.top_categories_by_avg_cost(db_session, test_user_id, start, end, limit=3)
        
        # Expected order: Transportation (50.00), Food (20.00), Entertainment (20.00)
        # When tied, should be sorted by category name alphabetically
        assert len(results) == 3
        
        assert results[0]["category"] == "Transportation"
        assert results[0]["amount"] == 50.00
        
        # Food and Entertainment both have 20.00 average - alphabetical order
        assert results[1]["category"] == "Entertainment"  # E comes before F
        assert results[1]["amount"] == 20.00
        
        assert results[2]["category"] == "Food"
        assert results[2]["amount"] == 20.00
    
    def test_top_categories_by_largest_tx(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test category ranking by largest single transaction."""
        start, end = test_timeframe
        
        results = lb_crud.top_categories_by_largest_tx(db_session, test_user_id, start, end, limit=3)
        
        # Expected order: Transportation (50.00), Food (30.00), Entertainment (25.00)
        assert len(results) == 3
        
        assert results[0]["category"] == "Transportation"
        assert results[0]["amount"] == 50.00
        
        assert results[1]["category"] == "Food"
        assert results[1]["amount"] == 30.00
        
        assert results[2]["category"] == "Entertainment"
        assert results[2]["amount"] == 25.00


class TestMerchantLeaderboards(TestLeaderboardsCRUD):
    """Test merchant-based leaderboard functions."""
    
    def test_top_merchants_by_total_value(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test merchant ranking by total spending value.""" 
        start, end = test_timeframe
        
        results = lb_crud.top_merchants_by_total_value(db_session, test_user_id, start, end, limit=5)
        
        # Expected order: UBER (50.00), then MCDONALDS/STARBUCKS (both 30.00, sorted alphabetically)
        assert len(results) == 5
        
        assert results[0]["merchant"] == "UBER"
        assert results[0]["amount"] == 50.00
        assert results[0]["category"] == "Transportation"
        
        # MCDONALDS comes before STARBUCKS alphabetically when both have 30.00
        assert results[1]["merchant"] == "MCDONALDS"  
        assert results[1]["amount"] == 30.00
        assert results[1]["category"] == "Food"
        
        assert results[2]["merchant"] == "STARBUCKS"  
        assert results[2]["amount"] == 30.00
        assert results[2]["category"] == "Food"
    
    def test_top_merchants_by_tx_count(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test merchant ranking by transaction count."""
        start, end = test_timeframe
        
        results = lb_crud.top_merchants_by_tx_count(db_session, test_user_id, start, end, limit=5)
        
        # Expected: STARBUCKS (2 transactions), others (1 each)
        assert len(results) == 5
        
        assert results[0]["merchant"] == "STARBUCKS"
        assert results[0]["amount"] == 2.0
        assert results[0]["category"] == "Food"
        
        # Others should have 1 transaction each (order by merchant name alphabetically)
        merchant_names = [r["merchant"] for r in results[1:]]
        assert all(r["amount"] == 1.0 for r in results[1:])
    
    def test_top_merchants_by_avg_cost(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test merchant ranking by average transaction cost."""
        start, end = test_timeframe
        
        results = lb_crud.top_merchants_by_avg_cost(db_session, test_user_id, start, end, limit=5)
        
        # Expected order: UBER (50.00), MCDONALDS (30.00), SPOTIFY (25.00), then NETFLIX/STARBUCKS (both 15.00, sorted alphabetically)
        assert len(results) == 5
        
        assert results[0]["merchant"] == "UBER"
        assert results[0]["amount"] == 50.00
        
        assert results[1]["merchant"] == "MCDONALDS"
        assert results[1]["amount"] == 30.00
        
        assert results[2]["merchant"] == "SPOTIFY"
        assert results[2]["amount"] == 25.00
        
        # NETFLIX comes before STARBUCKS alphabetically when both have 15.00
        assert results[3]["merchant"] == "NETFLIX" 
        assert results[3]["amount"] == 15.00
        
        assert results[4]["merchant"] == "STARBUCKS" 
        assert results[4]["amount"] == 15.00  # (10 + 20) / 2 = 15
    
    def test_top_merchants_by_largest_tx(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test merchant ranking by largest single transaction."""
        start, end = test_timeframe
        
        results = lb_crud.top_merchants_by_largest_tx(db_session, test_user_id, start, end, limit=5)
        
        # Expected order: UBER (50.00), MCDONALDS (30.00), SPOTIFY (25.00), STARBUCKS (20.00), NETFLIX (15.00)
        assert len(results) == 5
        
        assert results[0]["merchant"] == "UBER"
        assert results[0]["amount"] == 50.00
        
        assert results[1]["merchant"] == "MCDONALDS" 
        assert results[1]["amount"] == 30.00
        
        assert results[2]["merchant"] == "SPOTIFY"
        assert results[2]["amount"] == 25.00
        
        assert results[3]["merchant"] == "STARBUCKS"
        assert results[3]["amount"] == 20.00  # Max of (10, 20) = 20
        
        assert results[4]["merchant"] == "NETFLIX"
        assert results[4]["amount"] == 15.00


class TestLeaderboardEdgeCases(TestLeaderboardsCRUD):
    """Test edge cases and boundary conditions."""
    
    def test_empty_results(self, db_session: Session, test_user_id: UUID):
        """Test leaderboard functions with no matching transactions."""
        # Use timeframe with no transactions
        start = datetime.now(timezone.utc) - timedelta(days=1)
        end = datetime.now(timezone.utc) - timedelta(hours=1)
        
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=5)
        assert len(results) == 0
    
    def test_limit_parameter(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test that limit parameter works correctly."""
        start, end = test_timeframe
        
        # Test limit=1
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=1)
        assert len(results) == 1
        assert results[0]["category"] == "Food"
        
        # Test limit=2
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=2)
        assert len(results) == 2
    
    def test_income_exclusion(self, db_session: Session, test_user_id: UUID, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test that income transactions are excluded from expense calculations."""
        start, end = test_timeframe
        
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=10)
        
        # Should not include Income category (1000.00 income transaction)
        categories = [r["category"] for r in results]
        assert "Income" not in categories
        
        # Only expense categories should be present
        assert set(categories) == {"Food", "Transportation", "Entertainment"}
    
    def test_user_isolation(self, db_session: Session, test_timeframe: tuple[datetime, datetime], sample_transactions):
        """Test that results are properly isolated by user."""
        start, end = test_timeframe
        different_user_id = uuid4()
        
        # Query with different user ID
        results = lb_crud.top_categories_by_total_value(db_session, different_user_id, start, end, limit=10)
        
        # Should get no results for different user
        assert len(results) == 0
    
    def test_timeframe_filtering(self, db_session: Session, test_user_id: UUID, sample_transactions):
        """Test that timeframe filtering works correctly."""
        # Use very narrow timeframe that excludes most transactions
        start = datetime.now(timezone.utc) - timedelta(days=7) + timedelta(days=1)
        end = start + timedelta(hours=1)  # Very narrow window
        
        results = lb_crud.top_categories_by_total_value(db_session, test_user_id, start, end, limit=10)
        
        # Should only include transactions within the narrow timeframe
        # Based on our test data, only the first Food transaction should be included
        assert len(results) <= 1


class TestOverallStats(TestLeaderboardsCRUD):
    
    @pytest.fixture
    def clean_user_id(self) -> UUID:
        return uuid4()

    @pytest.fixture  
    def financial_test_data(self, db_session: Session, clean_user_id: UUID) -> None:
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        
        # Create test transactions across different time periods
        transactions = [
            # This month transactions
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=1000.00,
                description="Monthly salary",
                category="Income",
                merchant="EMPLOYER",
                transaction_type="income",
                source="debit",
                timestamp=now - timedelta(days=5)  # 5 days ago
            ),
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=500.00,
                description="Rent payment",
                category="Housing",
                merchant="LANDLORD",
                transaction_type="expense",
                source="debit",
                timestamp=now - timedelta(days=3)  # 3 days ago
            ),
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=100.00,
                description="Groceries",
                category="Food",
                merchant="GROCERY_STORE",
                transaction_type="expense",
                source="credit",
                timestamp=now - timedelta(days=1)  # 1 day ago
            ),
            
            # Last month transactions (older than 30 days)
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=1200.00,
                description="Previous month salary",
                category="Income",
                merchant="EMPLOYER",
                transaction_type="income",
                source="debit",
                timestamp=now - timedelta(days=35)  # 35 days ago
            ),
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=200.00,
                description="Old groceries",
                category="Food",
                merchant="OLD_STORE",
                transaction_type="expense",
                source="credit",
                timestamp=now - timedelta(days=40)  # 40 days ago
            ),
            
            # This year but different month
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=2000.00,
                description="Bonus payment",
                category="Income",
                merchant="EMPLOYER",
                transaction_type="income",
                source="debit",
                timestamp=now.replace(month=1, day=15)  # January this year
            ),
            TransactionModel(
                id=uuid4(),
                user_id=clean_user_id,
                amount=300.00,
                description="January expense",
                category="Shopping",
                merchant="STORE",
                transaction_type="expense",
                source="credit",
                timestamp=now.replace(month=1, day=20)  # January this year
            ),
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
    
    def test_totals_last_30d(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start_30d = now - timedelta(days=30)
        
        income, expense = lb_crud.totals_last_30d(db_session, clean_user_id, start_30d, now)
        
        # Only transactions within last 30 days should be included
        # Expected: Income = 1000.00, Expense = 500.00 + 100.00 = 600.00
        assert income == 1000.00
        assert expense == 600.00
    
    def test_totals_this_month(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        income, expense = lb_crud.totals_this_month(db_session, clean_user_id, month_start, now)
        
        # Only transactions in current month should be included
        # Expected: Income = 1000.00, Expense = 500.00 + 100.00 = 600.00
        assert income == 1000.00
        assert expense == 600.00
    
    def test_totals_this_year(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        income, expense = lb_crud.totals_this_year(db_session, clean_user_id, year_start, now)
        
        # All transactions this year should be included
        # Expected: Income = 1000.00 + 1200.00 + 2000.00 = 4200.00, Expense = 500.00 + 100.00 + 200.00 + 300.00 = 1100.00
        # Note: The "previous month" transactions are still within this calendar year
        assert income == 4200.00
        assert expense == 1100.00
    
    def test_sum_income_expense_helper(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = now - timedelta(days=10)
        
        income, expense = lb_crud._sum_income_expense(db_session, clean_user_id, start, now)
        
        # Should include transactions within the specified range
        # Expected: Income = 1000.00, Expense = 500.00 + 100.00 = 600.00
        assert income == 1000.00
        assert expense == 600.00
    
    def test_overall_stats_service(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from app.services.leaderboards import overall_stats
        
        stats = overall_stats(db_session, clean_user_id, days=30)
        
        # Verify all expected fields are present
        expected_fields = {
            "income_30d", "income_month", "income_year",
            "expense_30d", "expense_month", "expense_year"
        }
        assert set(stats.keys()) == expected_fields
        
        # Verify all values are floats and non-negative
        for field, value in stats.items():
            assert isinstance(value, float)
            assert value >= 0
        
        # Basic sanity checks
        assert stats["income_30d"] >= 0
        assert stats["expense_30d"] >= 0
        assert stats["income_year"] >= stats["income_month"]  # Year should be >= month
        assert stats["expense_year"] >= stats["expense_month"]  # Year should be >= month
    
    def test_financial_overview_with_empty_data(self, db_session: Session):
        empty_user_id = uuid4()
        
        from app.services.leaderboards import overall_stats
        stats = overall_stats(db_session, empty_user_id, days=30)
        
        # All values should be 0.0 for user with no transactions
        for field, value in stats.items():
            assert value == 0.0
    
    def test_different_time_periods(self, db_session: Session, clean_user_id: UUID, financial_test_data):
        from app.services.leaderboards import overall_stats
        
        # Test with different day ranges
        stats_7d = overall_stats(db_session, clean_user_id, days=7)
        stats_30d = overall_stats(db_session, clean_user_id, days=30)
        stats_365d = overall_stats(db_session, clean_user_id, days=365)
        
        # 7 days should be subset of 30 days
        assert stats_7d["income_30d"] <= stats_30d["income_30d"]
        assert stats_7d["expense_30d"] <= stats_30d["expense_30d"]
        
        # 30 days should be subset of 365 days  
        assert stats_30d["income_30d"] <= stats_365d["income_30d"]
        assert stats_30d["expense_30d"] <= stats_365d["expense_30d"]


class TestNewCRUDFunctions(TestLeaderboardsCRUD):
    
    def test_range_filter_function(self, db_session: Session, test_user_id: UUID):
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = now - timedelta(days=7)
        
        # Test that _range_filter function works correctly
        filter_condition = lb_crud._range_filter(test_user_id, start, now)
        
        # Should return a SQL condition that can be used in queries
        assert filter_condition is not None
        
        # Test it doesn't cause SQL errors when used in a query
        result = db_session.query(TransactionModel).filter(filter_condition).all()
        assert isinstance(result, list)  # Should return a list (even if empty)
    
    def test_income_expense_case_statements(self, db_session: Session, test_user_id: UUID):
        # Create test transactions
        income_tx = TransactionModel(
            id=uuid4(),
            user_id=test_user_id,
            amount=100.00,
            description="Test income",
            category="Income",
            merchant="TEST",
            transaction_type="income",
            source="debit",
            timestamp=datetime.now(timezone.utc)
        )
        
        expense_tx = TransactionModel(
            id=uuid4(),
            user_id=test_user_id,
            amount=50.00,
            description="Test expense",
            category="Food",
            merchant="TEST",
            transaction_type="expense",
            source="credit",
            timestamp=datetime.now(timezone.utc)
        )
        
        db_session.add(income_tx)
        db_session.add(expense_tx)
        db_session.commit()
        
        # Test the _sum_income_expense function
        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        
        income, expense = lb_crud._sum_income_expense(db_session, test_user_id, start, end)
        
        assert income == 100.00
        assert expense == 50.00
