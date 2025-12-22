"""
Tests for delivery partner endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


@pytest.mark.asyncio
async def test_delivery_partner_signup(client: AsyncClient, test_session: AsyncSession):
    """Test delivery partner signup endpoint"""
    partner_data = {
        "name": "Test Partner",
        "email": "partner@example.com",
        "password": "testpassword123",
        "serviceable_zip_codes": [10001, 10002, 10003],
        "max_handling_capacity": 10
    }
    
    response = await client.post("/partner/signup", json=partner_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == partner_data["name"]
    assert data["email"] == partner_data["email"]
    assert data["serviceable_zip_codes"] == partner_data["serviceable_zip_codes"]
    assert data["max_handling_capacity"] == partner_data["max_handling_capacity"]
    assert "id" in data
    # Verify ID is a valid UUID
    try:
        UUID(data["id"])
    except (ValueError, TypeError):
        pytest.fail(f"ID is not a valid UUID: {data['id']}")
    assert "password" not in data  # Password should not be in response


@pytest.mark.asyncio
async def test_delivery_partner_login_success(client: AsyncClient, test_session: AsyncSession):
    """Test successful delivery partner login flow"""
    # First, create a partner
    partner_data = {
        "name": "Login Test Partner",
        "email": "loginpartner@example.com",
        "password": "loginpassword123",
        "serviceable_zip_codes": [20001],
        "max_handling_capacity": 5
    }
    
    signup_response = await client.post("/partner/signup", json=partner_data)
    assert signup_response.status_code == 200
    
    # Now test login
    login_data = {
        "username": partner_data["email"],
        "password": partner_data["password"]
    }
    
    response = await client.post(
        "/partner/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "type" in data
    assert data["type"] == "jwt"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_delivery_partner_login_invalid_credentials(client: AsyncClient, test_session: AsyncSession):
    """Test login with invalid credentials"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    response = await client.post(
        "/partner/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_delivery_partner_update(client: AsyncClient, test_session: AsyncSession):
    """Test updating delivery partner (requires authentication)"""
    # Create partner
    partner_data = {
        "name": "Update Test Partner",
        "email": "updatepartner@example.com",
        "password": "password123",
        "serviceable_zip_codes": [30001],
        "max_handling_capacity": 8
    }
    
    signup_response = await client.post("/partner/signup", json=partner_data)
    assert signup_response.status_code == 200
    
    # Login to get token
    login_response = await client.post(
        "/partner/token",
        data={"username": partner_data["email"], "password": partner_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Update partner
    update_data = {
        "serviceable_zip_codes": [30001, 30002],
        "max_handling_capacity": 12
    }
    
    response = await client.post(
        "/partner/",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["serviceable_zip_codes"] == update_data["serviceable_zip_codes"]
    assert data["max_handling_capacity"] == update_data["max_handling_capacity"]


@pytest.mark.asyncio
async def test_delivery_partner_logout(client: AsyncClient, test_session: AsyncSession):
    """Test delivery partner logout"""
    # Create and login partner
    partner_data = {
        "name": "Logout Test Partner",
        "email": "logoutpartner@example.com",
        "password": "password123",
        "serviceable_zip_codes": [40001],
        "max_handling_capacity": 5
    }
    
    signup_response = await client.post("/partner/signup", json=partner_data)
    assert signup_response.status_code == 200
    
    login_response = await client.post(
        "/partner/token",
        data={"username": partner_data["email"], "password": partner_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Logout
    response = await client.get(
        "/partner/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "detail" in data
    assert "logged out" in data["detail"].lower()

