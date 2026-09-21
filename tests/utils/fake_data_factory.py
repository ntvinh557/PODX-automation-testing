import os
from typing import Dict
from faker import Faker

# Khởi tạo Faker (có thể thêm nhiều locale nếu muốn)
fake = Faker(['en_US', 'vi_VN'])

class FakeDataFactory:
    """Factory class to generate random test data using Faker."""

    @staticmethod
    def get_random_user() -> Dict[str, str]:
        """Tạo thông tin user ngẫu nhiên."""
        return {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True),
            "phone_number": fake.phone_number(),
            "username": fake.user_name(),
        }

    @staticmethod
    def get_random_billing_address() -> Dict[str, str]:
        """Tạo địa chỉ thanh toán ngẫu nhiên."""
        return {
            "address_line_1": fake.street_address(),
            "address_line_2": fake.secondary_address(),
            "city": fake.city(),
            "state": fake.state(),
            "country": fake.country_code(),
            "postal_code": fake.postcode(),
        }

    @staticmethod
    def get_random_credit_card() -> Dict[str, str]:
        """Tạo thông tin thẻ tín dụng ngẫu nhiên (dùng cho negative test vì không phải thẻ thật của Stripe)."""
        return {
            "card_number": fake.credit_card_number(),
            "card_expiry": fake.credit_card_expire(date_format="%m/%y"),
            "card_cvc": fake.credit_card_security_code(),
            "cardholder_name": fake.name(),
        }
    
    @staticmethod
    def get_random_full_billing_profile() -> Dict[str, str]:
        """Tạo một profile thanh toán hoàn chỉnh."""
        profile = FakeDataFactory.get_random_credit_card()
        profile.update(FakeDataFactory.get_random_billing_address())
        return profile
