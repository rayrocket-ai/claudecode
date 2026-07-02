"""Unit tests for data extraction and validation."""

import json

from ai.agent import DEAL_DATA_TOOL, DataExtractor, RealEstateAgent


class TestValidateAps:
    def test_complete(self):
        data = {
            "buyer_1": "Jane Doe",
            "seller_1": "John Roe",
            "purchase_price": 800000,
            "property_street_number": "12",
            "property_street_name": "Main St",
            "property_city": "Toronto",
        }
        assert DataExtractor.validate_aps(data) == []

    def test_missing_fields(self):
        missing = DataExtractor.validate_aps({"buyer_1": "Jane Doe"})
        assert "seller_1" in missing
        assert "purchase_price" in missing
        assert "property_city" in missing

    def test_empty_values_count_as_missing(self):
        missing = DataExtractor.validate_aps({"buyer_1": "", "purchase_price": 0})
        assert "buyer_1" in missing
        assert "purchase_price" in missing


class TestNormalizePrice:
    def test_string_with_symbols(self):
        assert DataExtractor.normalize_price("$1,250,000") == 1250000.0

    def test_numeric_passthrough(self):
        assert DataExtractor.normalize_price(800000) == 800000.0


class TestJsonFallbackExtraction:
    def _extract(self, text):
        agent = RealEstateAgent.__new__(RealEstateAgent)
        return agent._try_extract_json(text)

    def test_json_block(self):
        text = 'Done!\n```json\n{"buyer_1": "Jane", "collection_complete": true}\n```'
        data = self._extract(text)
        assert data == {"buyer_1": "Jane", "collection_complete": True}

    def test_incomplete_flag_ignored(self):
        text = '```json\n{"buyer_1": "Jane", "collection_complete": false}\n```'
        assert self._extract(text) is None

    def test_plain_text_returns_none(self):
        assert self._extract("What is the property address?") is None


class TestDealDataTool:
    def test_schema_is_valid_json(self):
        # The tool definition must be serializable for the API call
        json.dumps(DEAL_DATA_TOOL)
        assert DEAL_DATA_TOOL["name"] == "submit_deal_data"
        props = DEAL_DATA_TOOL["input_schema"]["properties"]
        # Required APS fields must be describable by the tool
        for field in DataExtractor.REQUIRED_APS_FIELDS:
            assert field in props
