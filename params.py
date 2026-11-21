from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

PaymentMethodType = Literal[
    "card",
    "bank_account",
    "mobile_money",
    "opay",
    "applepay",
    "googlepay",
    "ussd",
    "bank_transfer",
]


class NameParam(TypedDict, total=False):
    first: str
    middle: str
    last: str


class PhoneParam(TypedDict, total=False):
    country_code: str
    number: str


class AddressParam(TypedDict, total=False):
    city: str
    country: str
    line1: str
    line2: str
    postal_code: str
    state: str


class CustomerCreateParams(TypedDict, total=False):
    email: str
    name: NameParam
    phone: PhoneParam
    address: AddressParam
    meta: dict[str, Any]


class EncryptedCardParam(TypedDict):
    nonce: str
    encrypted_card_number: str
    encrypted_expiry_month: str
    encrypted_expiry_year: str
    encrypted_cvv: str


class MobileMoneyParam(TypedDict):
    country_code: str
    network: str
    phone_number: str


class USSDParam(TypedDict):
    account_bank: str


class OPayParam(TypedDict, total=False):
    country: str


class PaymentMethodCreateParams(TypedDict, total=False):
    type: PaymentMethodType
    customer_id: str
    card: EncryptedCardParam
    mobile_money: MobileMoneyParam
    ussd: USSDParam
    opay: OPayParam
    bank_account: dict[str, Any]
    bank_transfer: dict[str, Any]
    meta: dict[str, Any]


class ChargeCreateParams(TypedDict, total=False):
    amount: float
    currency: str
    reference: str
    customer_id: str
    payment_method_id: str
    redirect_url: str
    authorization: dict[str, Any]
    description: str
    meta: dict[str, Any]


class OrchestratorDirectChargeParams(TypedDict, total=False):
    amount: float
    currency: str
    reference: str
    customer: CustomerCreateParams
    payment_method: PaymentMethodCreateParams
    redirect_url: str
    authorization: dict[str, Any]
    merchant_vat_amount: float
    meta: dict[str, Any]


class VirtualAccountCreateParams(TypedDict, total=False):
    reference: str
    customer_id: str
    amount: float
    currency: str
    account_type: Literal["static", "dynamic"]
    narration: str
    expiry: int
    bvn: str
    nin: str
    meta: dict[str, Any]


class TransferRecipientCreateParams(TypedDict, total=False):
    type: str
    bank: dict[str, Any]
    mobile_money: dict[str, Any]
    wallet: dict[str, Any]
    meta: dict[str, Any]


class TransferCreateParams(TypedDict, total=False):
    action: Literal["instant", "scheduled"]
    reference: str
    amount: float
    currency: str
    recipient_id: str
    narration: str
    meta: dict[str, Any]
    schedule: NotRequired[dict[str, Any]]
