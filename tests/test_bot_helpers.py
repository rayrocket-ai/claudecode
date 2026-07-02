"""Unit tests for bot handler helpers."""

from bot.handlers.conversation import _format_deal_summary, _md_escape


class TestMdEscape:
    def test_underscores(self):
        assert _md_escape("John_Smith") == r"John\_Smith"

    def test_asterisks_backticks_brackets(self):
        assert _md_escape("a*b`c[d") == r"a\*b\`c\[d"

    def test_plain_text_unchanged(self):
        assert _md_escape("12 Main St, Toronto") == "12 Main St, Toronto"

    def test_non_string_input(self):
        assert _md_escape(800000) == "800000"


class TestFormatDealSummary:
    def test_full_summary(self):
        data = {
            "property_street_number": "12",
            "property_street_name": "Main St",
            "property_city": "Toronto",
            "buyer_1": "Jane Doe",
            "seller_1": "John Roe",
            "purchase_price": 800000,
            "deposit": 40000,
            "closing_date": "2026-09-30",
            "financing_condition": True,
        }
        summary = _format_deal_summary(data, "aps")
        assert "12 Main St" in summary
        assert "Jane Doe" in summary
        assert "$800,000" in summary
        assert "Financing" in summary

    def test_markdown_unsafe_names_escaped(self):
        data = {"buyer_1": "John_Smith", "seller_1": "A*Corp"}
        summary = _format_deal_summary(data, "aps")
        assert r"John\_Smith" in summary
        assert r"A\*Corp" in summary

    def test_empty_data(self):
        assert _format_deal_summary({}, "aps") == "_No data collected_"
