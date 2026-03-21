"""Condition templates and clause suggestions for Ontario real estate."""

from __future__ import annotations

CONDITION_TEMPLATES = {
    "financing": (
        "This Offer is conditional upon the Buyer arranging, at the Buyer's own "
        "expense, a new first Charge/Mortgage for not less than ${amount} bearing "
        "interest at a rate of no more than {rate}% per annum, calculated "
        "semi-annually not in advance, repayable in blended monthly payments of "
        "about ${payment}, and to run for a term of not less than {term} years "
        "from the date of completion of this transaction. Unless the Buyer gives "
        "notice in writing delivered to the Seller personally or in accordance "
        "with any other provisions for the delivery of notice in this Agreement "
        "of Purchase and Sale or any Schedule thereto not later than {expiry_time} "
        "p.m. on the {expiry_day} day of {expiry_month}, {expiry_year}, that this "
        "condition is fulfilled, this Offer shall be null and void and the deposit "
        "shall be returned to the Buyer in full without deduction. This condition "
        "is included for the benefit of the Buyer and may be waived at the "
        "Buyer's sole option by notice in writing to the Seller as aforesaid "
        "within the time period stated herein."
    ),
    "home_inspection": (
        "This Offer is conditional upon the inspection of the subject property "
        "by a home inspector at the Buyer's own expense, and the obtaining of a "
        "report satisfactory to the Buyer in the Buyer's sole and absolute "
        "discretion. Unless the Buyer gives notice in writing delivered to the "
        "Seller personally or in accordance with any other provisions for the "
        "delivery of notice in this Agreement of Purchase and Sale or any "
        "Schedule thereto not later than {expiry_time} p.m. on the {expiry_day} "
        "day of {expiry_month}, {expiry_year}, that this condition is fulfilled, "
        "this Offer shall be null and void and the deposit shall be returned to "
        "the Buyer in full without deduction. This condition is included for the "
        "benefit of the Buyer and may be waived at the Buyer's sole option by "
        "notice in writing to the Seller as aforesaid within the time period "
        "stated herein."
    ),
    "status_certificate": (
        "This Offer is conditional upon the Buyer's lawyer reviewing the Status "
        "Certificate and attachments and finding the Status Certificate and "
        "attachments satisfactory in the Buyer's Lawyer's sole and absolute "
        "discretion. The Seller agrees to request at the Seller's expense, the "
        "Status Certificate within {request_days} days after acceptance of this "
        "Offer. Unless the Buyer gives notice in writing delivered to the Seller "
        "personally or in accordance with any other provisions for the delivery "
        "of notice in this Agreement of Purchase and Sale or any Schedule thereto "
        "not later than {expiry_time} p.m. on the {expiry_day} day of "
        "{expiry_month}, {expiry_year}, that this condition is fulfilled, this "
        "Offer shall be null and void and the deposit shall be returned to the "
        "Buyer in full without deduction."
    ),
    "sale_of_buyers_property": (
        "This Offer is conditional upon the sale of the Buyer's property known "
        "as {buyer_property_address}. Unless the Buyer gives notice in writing "
        "delivered to the Seller personally or in accordance with any other "
        "provisions for the delivery of notice in this Agreement of Purchase and "
        "Sale or any Schedule thereto not later than {expiry_time} p.m. on the "
        "{expiry_day} day of {expiry_month}, {expiry_year}, that this condition "
        "is fulfilled, this Offer shall be null and void and the deposit shall "
        "be returned to the Buyer in full without deduction."
    ),
    "lawyer_approval": (
        "This Offer is conditional upon the approval of the terms hereof by the "
        "Buyer's Solicitor. Unless the Buyer gives notice in writing delivered "
        "to the Seller personally or in accordance with any other provisions for "
        "the delivery of notice in this Agreement of Purchase and Sale or any "
        "Schedule thereto not later than {expiry_time} p.m. on the {expiry_day} "
        "day of {expiry_month}, {expiry_year}, that this condition is fulfilled, "
        "this Offer shall be null and void and the deposit shall be returned to "
        "the Buyer in full without deduction."
    ),
}
