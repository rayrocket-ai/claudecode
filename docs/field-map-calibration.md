# Calibrating TransactionDesk field maps

The bot fills WebForms fields by their HTML `name` attribute
(`forms/field_maps.py`). Form 100's map was captured from the live editor;
Forms **120, 122, 400, and 500** still have `TODO(calibrate)` placeholders
that need real names captured from a live TransactionDesk session.

Safety model: `fill_form` silently skips names that don't exist on the page,
so a *missing* mapping just leaves a box blank — but a *wrong* mapping fills
the wrong box. That's why guessed names ship commented out. Only uncomment a
line once you've confirmed the real name.

## How to capture field names (~5 minutes per form)

1. Log into TransactionDesk via the TRREB portal
   (https://ontariomlp.ca/trrebwebform/ → WebForms).
2. Open any transaction → **Add Form** → pick the form
   (e.g. *(Ontario) 120 - Amendment to Agreement*).
3. In the form editor, open browser DevTools (**F12** or right-click →
   Inspect) and click directly on the input box you care about.
4. In the Elements panel, read the `name="..."` attribute of the
   `<input>` / `<textarea>` — e.g. `<input name="txtp_OrigAgreementDate_d">`.
5. If the form loads in an iframe, click inside the form first so DevTools
   selects the iframe's document.

To grab **all** fields at once, paste this in the DevTools console (run it in
the form iframe's context if there is one):

```js
[...document.querySelectorAll('input[name], textarea[name]')]
  .map(el => el.name)
  .join('\n')
```

## Where to put them

Edit `forms/field_maps.py`. Each map is `html_name → deal_data_key`.
Uncomment the relevant `TODO(calibrate)` line and replace `"???"` with the
captured name, e.g.:

```python
FORM_120_FIELDS = {
    ...
    "txtp_OrigAgreementDate_d": "original_agreement_date_d",
    "txtp_OrigAgreementDate_mmmm": "original_agreement_date_mmmm",
    "txtp_OrigAgreementDate_yy": "original_agreement_date_yy",
    "txtAmendment": "amendment_description",
}
```

The right-hand keys are already produced by `_flatten_deal_data` in
`integrations/transactiondesk.py`:

| Deal fact | Available flat keys |
|---|---|
| Any date (`original_agreement_date`, `amendment_date`, `waiver_date`, `lease_start_date`, `lease_end_date`) | `<key>` (as typed), `<key>_d`, `<key>_mmmm`, `<key>_yy` |
| Monthly rent | `monthly_rent_formatted`, `monthly_rent_words` |
| Rent deposit | `rent_deposit_formatted`, `rent_deposit_words` |
| Text facts | `amendment_description`, `condition_waived`, `parking`, `locker`, `appliances`, `utilities_included`, `conditions`, `zoning`, `due_diligence_days`, `hst_applicable`, `assignment_rights`, `environmental_assessment`, `commercial_property_type` |

After editing, run the test suite (`python3 -m pytest tests/ -q`) and do one
live fill with `/realmtest` + a test transaction to confirm boxes land where
expected.
