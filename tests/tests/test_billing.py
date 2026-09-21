import allure
import pytest
from playwright.sync_api import expect

from tests.pages.billing_page import BillingPage
from tests.utils.test_data_factory import TestDataFactory

@allure.suite("BILLING_UI_SUITE")
@allure.title("MPODX UI Billing Method Integration Test Case Suite")
@pytest.mark.auth(username="valid_user_billing")
@pytest.mark.usefixtures("authenticated_session")
class TestBillingMethod:
    
    @pytest.fixture(autouse=True)
    def setup_billing_modal(self, page):
        """Fixture chạy trước mỗi test case: Vào trang cài đặt thanh toán và mở Modal thêm thẻ."""
        billing_page = BillingPage(page)
        
        with allure.step("Vào màn hình billing settings"):
            billing_page.open()
            
        with allure.step("Click button Add new billing method và đợi modal load"):
            billing_page.open_add_billing_modal()

    @allure.title("TC-BILLING-001: Thêm thẻ thanh toán thành công và xác thực 3DS (Happy Path)")
    @allure.description("Điền thông tin thẻ -> Submit -> Kiểm tra nút Processing.")
    @pytest.mark.smoke
    @pytest.mark.regression
    @pytest.mark.e2e
    def test_add_billing_method_happy_path_tc001(self, page):
        billing_page = BillingPage(page)
        user_data = TestDataFactory.get_valid_3ds_user()

        with allure.step("Điền thông tin thẻ"):
            billing_page.fill_billing_info(user_data)
        
        with allure.step("Submit"):
            billing_page.submit_button.click()
            
        with allure.step("Xác nhận nút chuyển sang trạng thái Processing ngay sau khi submit"):
            expect(billing_page.submit_processing).to_be_visible()

    @allure.title("TC-BILLING-002: Bỏ trống các trường bắt buộc")
    @allure.description("Xóa sạch Email, Card Info, Address và bấm Save -> Nút Save không gửi API, hiển thị báo lỗi bắt buộc cho Email.")
    @pytest.mark.smoke
    @pytest.mark.regression
    @pytest.mark.e2e
    def test_empty_required_fields_validation_tc002(self, page):
        billing_page = BillingPage(page)

        with allure.step("Xoá sạch các trường bắt buộc"):
            billing_page.clear_form()

        with allure.step("Bấm Save"):
            billing_page.submit_button.click()
            
        with allure.step("Hiển thị lỗi bắt buộc cho Email"):
            expect(billing_page.email_error).to_be_visible()

    @allure.title("TC-BILLING-003: Validate thuật toán Luhn (Số thẻ invalid)")
    @allure.description("Nhập số thẻ sai độ dài hoặc không thỏa mãn công thức Luhn -> Báo lỗi 'Your card number is invalid.'")
    @pytest.mark.smoke
    @pytest.mark.regression
    @pytest.mark.e2e
    def test_invalid_luhn_validation_tc003(self, page):
        billing_page = BillingPage(page)
        invalid_user = TestDataFactory.get_invalid_luhn_user()

        with allure.step("Nhập số thẻ sai độ dài hoặc sai Luhn"):
            billing_page.fill(billing_page.card_number_input, invalid_user.get("card_number", ""))
            
        with allure.step("Trigger out-focus (blur) để hiển thị lỗi inline"):
            billing_page.trigger_blur_on_card_number()

        with allure.step("Thông báo lỗi số thẻ sai hiển thị"):
            expect(billing_page.invalid_card_number_error).to_be_visible()
