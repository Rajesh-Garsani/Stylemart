import hashlib, datetime
from django.conf import settings

def build_payment_payload(order_id, amount):
    now = datetime.datetime.now()
    txn_datetime = now.strftime("%Y%m%d%H%M%S")
    exp_datetime = (now + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")

    payload = {
        "pp_Version": "1.1",
        "pp_TxnType": "MWALLET",
        "pp_Language": "EN",
        "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
        "pp_SubMerchantID": "",
        "pp_Password": settings.JAZZCASH_PASSWORD,
        "pp_TxnRefNo": f"T{order_id}{txn_datetime}",
        "pp_Amount": str(int(amount * 100)),  # in paisa
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": txn_datetime,
        "pp_BillReference": f"Order{order_id}",
        "pp_Description": f"Payment for Order {order_id}",
        "pp_TxnExpiryDateTime": exp_datetime,
        "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
    }

    # Secure hash
    sorted_keys = sorted(payload.keys())
    hash_string = settings.JAZZCASH_INTEGRITY_SALT + '&' + '&'.join(
        str(payload[k]) for k in sorted_keys if payload[k] != ""
    )
    payload["pp_SecureHash"] = hashlib.sha256(hash_string.encode("utf-8")).hexdigest()

    return payload
