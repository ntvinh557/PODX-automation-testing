import time
import re
from playwright.sync_api import Page, Locator

from tests.base.base_page import BasePage

class BillingPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        
        # --- Stripe Embedded Checkout Iframes ---
        self.stripe_frame = page.frame_locator("iframe[name='embedded-checkout']")
        self.stripe_modals_frame = page.frame_locator("iframe[name='embedded-checkout-modals']")
        
        # --- Contact Details ---
        self.email_input = self.stripe_frame.get_by_role("textbox", name="Email")
        
        # --- Card Information ---
        self.card_number_input = self.stripe_frame.get_by_role("textbox", name="Card number")
        self.card_expiry_input = self.stripe_frame.get_by_role("textbox", name="Expiration")
        self.card_cvc_input = self.stripe_frame.get_by_role("textbox", name="Credit or debit card CVC/CVV")
        
        # --- Billing Address ---
        self.cardholder_name_input = self.stripe_frame.get_by_role("textbox", name="Cardholder name")
        self.address_line_1_input = self.stripe_frame.get_by_role("textbox", name="Address line 1")
        self.city_input = self.stripe_frame.get_by_role("textbox", name="City")
        # Optional fields from locator map
        self.country_dropdown = self.stripe_frame.get_by_role("combobox", name="Country or region")
        self.address_line_2_input = self.stripe_frame.get_by_role("textbox", name="Address line 2")
        self.province_dropdown = self.stripe_frame.get_by_role("combobox", name="Province")
        self.postal_code_input = self.stripe_frame.get_by_role("textbox", name="Postal code")
        
        # --- Actions ---
        self.submit_button = self.stripe_frame.get_by_role("button", name="Save")
        
        # --- Validation Errors ---
        self.email_error = self.stripe_frame.locator("[data-qa='EmptyFieldError'], .FieldError").first
        self.invalid_card_number_error = self.stripe_frame.locator(".FieldError").filter(has_text=re.compile("card number|invalid", re.IGNORECASE))
        
        # --- Loading States ---
        self.submit_processing = self.stripe_frame.get_by_text("Processing")
        
        # --- Saved Card Actions (Outside Modal) ---
        self.set_primary_button = page.get_by_role("button", name="Set Primary")
        self.edit_card_button = page.get_by_role("button", name="Edit")

    def open(self):
        """Mở trang danh sách billing methods"""
        self.page.goto(f"{self.base_url}/billing/settings/")
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def open_add_billing_modal(self):
        """Click button Add new billing method và đợi modal load"""
        self.page.get_by_role("button", name="Add new billing method").click()
        self.submit_button.wait_for(state="visible")
        return self

    def clear_form(self):
        """Xoá dữ liệu các trường cơ bản để trigger validation lỗi."""
        self.email_input.fill("")
        self.email_input.press("Tab")
        self.card_number_input.fill("")
        self.card_number_input.press("Tab")
        
    def fill_billing_info(self, data: dict):
        """Điền toàn bộ thông tin thanh toán từ bộ test data."""
        if "email" in data:
            self.fill(self.email_input, data["email"])
            
        if "card_number" in data:
            self.fill(self.card_number_input, data["card_number"])
            
        if "card_expiry" in data:
            self.fill(self.card_expiry_input, data["card_expiry"])
            
        if "card_cvc" in data:
            self.fill(self.card_cvc_input, data["card_cvc"])
            
        if "cardholder_name" in data:
            self.fill(self.cardholder_name_input, data["cardholder_name"])
            
        if "country" in data:
            try:
                self.country_dropdown.select_option(value=data["country"], timeout=3000)
            except Exception:
                pass # Bỏ qua nếu không thể select (ví dụ element bị ẩn)

        if "address_line_1" in data:
            # Xử lý form Address động của Stripe (Autocomplete vs Manual)
            manual_btn = self.stripe_frame.get_by_role("button", name=re.compile("Enter address manually", re.IGNORECASE))
            
            # Chờ 1 trong 2 thẻ xuất hiện
            any_element = self.address_line_1_input.or_(manual_btn)
            try:
                any_element.first.wait_for(state="visible", timeout=10000)
                if manual_btn.is_visible():
                    manual_btn.click()
            except Exception:
                pass # Nếu timeout cứ để mặc định chạy tiếp, fill() sẽ tự văng lỗi nếu không thấy

            self.fill(self.address_line_1_input, data["address_line_1"])
            
        if "city" in data:
            self.fill(self.city_input, data["city"])

    def trigger_blur_on_card_number(self):
        """Trigger blur on card number to show inline validation."""
        self.card_number_input.press("Tab")


