from httpx import AsyncClient


async def test_evaluate_flag_returns_200_and_expected_schema(
    client: AsyncClient,
) -> None:
    # Arrange
    create_response = await client.post(
        "/v1/flags",
        headers={"Idempotency-Key": "create-checkout-v2"},
        json={
            "key": "checkout.v2",
            "environment": "production",
            "enabled": True,
            "description": "New checkout flow",
        },
    )
    assert create_response.status_code == 201

    # Act
    response = await client.get("/v1/flags/production/checkout.v2/evaluate")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": "tenant-a",
        "environment": "production",
        "key": "checkout.v2",
        "enabled": True,
        "source": "cache",
    }
