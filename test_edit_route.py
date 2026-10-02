#!/usr/bin/env python
"""Test edit route with valid and invalid expense IDs."""

from app import app

def test_edit_route():
    """Test edit route."""
    with app.test_client() as client:
        with app.app_context():
            # Login as demo user
            login_resp = client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            })
            print(f"Login status: {login_resp.status_code}")

            # Test with valid expense (ID 8 belongs to demo user)
            print("\nTesting /expenses/8/edit (belongs to demo user):")
            valid_resp = client.get('/expenses/8/edit')
            print(f"  Status: {valid_resp.status_code}")
            print(f"  Contains 'Edit Expense' title: {b'Edit Expense' in valid_resp.data}")

            # Test with invalid expense (ID 12 belongs to different user)
            print("\nTesting /expenses/12/edit (belongs to different user):")
            invalid_resp = client.get('/expenses/12/edit')
            print(f"  Status: {invalid_resp.status_code} (404 is correct - user doesn't own this expense)")

            # Test with non-existent expense
            print("\nTesting /expenses/999/edit (doesn't exist):")
            notfound_resp = client.get('/expenses/999/edit')
            print(f"  Status: {notfound_resp.status_code} (404 is correct)")

if __name__ == '__main__':
    test_edit_route()
