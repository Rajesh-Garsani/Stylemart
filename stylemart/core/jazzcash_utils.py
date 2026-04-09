import hashlib
import datetime
from django.conf import settings


def build_payment_payload(order_id, amount):
    now = datetime.datetime.now()
    txn_datetime = now.strftime("%Y%m%d%H%M%S")

    # Expiry time (1 hour from now)
    exp_datetime = (now + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")

    # Safely convert Decimal/Float amount to paisas (e.g. Rs. 150.00 -> 15000 paisa)
    amount_paisa = str(int(float(amount) * 100))

    payload = {
        "pp_Version": "1.1",
        "pp_TxnType": "",  # Leaving this empty enables ALL payment methods (Cards + Wallets)
        "pp_Language": "EN",
        "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
        "pp_Password": settings.JAZZCASH_PASSWORD,
        "pp_TxnRefNo": f"T{order_id}{txn_datetime}",
        "pp_Amount": amount_paisa,
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": txn_datetime,
        "pp_BillReference": f"Order{order_id}",
        "pp_Description": f"Payment for Order {order_id}",
        "pp_TxnExpiryDateTime": exp_datetime,
        "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
    }

    # FIX 2: Completely remove empty keys from the dictionary so they aren't posted in the HTML form
    payload = {k: v for k, v in payload.items() if v != ""}

    # 1. Sort the remaining keys alphabetically
    sorted_keys = sorted(payload.keys())

    # 2. Build the secure hash string: Salt & value1 & value2 ...
    hash_string = settings.JAZZCASH_INTEGRITY_SALT + '&' + '&'.join(
        str(payload[k]) for k in sorted_keys
    )

    # FIX 1: Generate SHA256 hash and convert it to .upper()
    payload["pp_SecureHash"] = hashlib.sha256(hash_string.encode("utf-8")).hexdigest().upper()

    return payload