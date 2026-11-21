from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .auth import OAuthTokenManager
from .http import APIClient, Environment
from .services import (
    BankService,
    CardTransactionService,
    ChargeService,
    CustomerService,
    GenericCrudService,
    MobileNetworkService,
    OrchestrationService,
    PaymentMethodService,
    RefundService,
    SettlementService,
    TransferService,
    VirtualAccountService,
    WalletService,
    TransactionService,
    TransactionVerificationService
)


@dataclass(slots=True)
class V4Services:
    customers: CustomerService
    payment_methods: PaymentMethodService
    charges: ChargeService
    card_transactions: CardTransactionService
    orchestration: OrchestrationService
    banks: BankService
    mobile_networks: MobileNetworkService
    virtual_accounts: VirtualAccountService
    transfers: TransferService
    wallets: WalletService
    refunds: RefundService
    settlements: SettlementService
    orders: GenericCrudService
    chargebacks: GenericCrudService
    fees: GenericCrudService
    transactions: TransactionService
    verification: TransactionVerificationService


class FlutterwaveClient:
    """Service-based entry point for Flutterwave v4.

    This follows Stripe's modern SDK principle: configuration lives on an instance, not in
    module-level globals. That means you can safely keep separate sandbox/live clients in the
    same process and mock the client in tests.
    """

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        environment: str | Environment = "sandbox",
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
        max_network_retries: int = 2,
        token_url: str | None = None,
        encryption_key: str | None = None,
    ) -> None:
        token_manager = OAuthTokenManager(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            token_url=token_url or "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token",
            http_client=http_client,
        )
        self._encryption_key = encryption_key
        self._api_client = APIClient(
            token_manager=token_manager,
            environment=environment,
            http_client=http_client,
            timeout=timeout,
            max_network_retries=max_network_retries,
        )
        self.v4 = self._build_v4_services()

        # Convenience aliases for the current stable v4 namespace.
        self.customers = self.v4.customers
        self.payment_methods = self.v4.payment_methods
        self.charges = self.v4.charges
        self.card_transactions = self.v4.card_transactions
        self.orchestration = self.v4.orchestration
        self.banks = self.v4.banks
        self.mobile_networks = self.v4.mobile_networks
        self.virtual_accounts = self.v4.virtual_accounts
        self.transfers = self.v4.transfers
        self.wallets = self.v4.wallets
        self.refunds = self.v4.refunds
        self.settlements = self.v4.settlements
        self.orders = self.v4.orders
        self.chargebacks = self.v4.chargebacks
        self.fees = self.v4.fees
        self.transactions = self.v4.transactions
        self.verification = self.v4.verification

    def close(self) -> None:
        self._api_client.close()

    def __enter__(self) -> "FlutterwaveClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def request_raw(self, method: str, path: str, **kwargs: Any) -> Any:
        """Escape hatch for new Flutterwave endpoints before this SDK wraps them."""
        return self._api_client.request(method, path, **kwargs)

    def _build_v4_services(self) -> V4Services:
        api = self._api_client
        return V4Services(
            customers=CustomerService(api),
            payment_methods=PaymentMethodService(api),
            charges=ChargeService(api),
            card_transactions=CardTransactionService(
                customers=CustomerService(api),
                payment_methods=PaymentMethodService(api),
                charges=ChargeService(api),
                orchestration=OrchestrationService(api),
                encryption_key=self._encryption_key,
            ),
            orchestration=OrchestrationService(api),
            banks=BankService(api),
            mobile_networks=MobileNetworkService(api),
            virtual_accounts=VirtualAccountService(api),
            transfers=TransferService(api),
            wallets=WalletService(api),
            refunds=RefundService(api),
            settlements=SettlementService(api),
            orders=GenericCrudService(api, "/orders"),
            chargebacks=GenericCrudService(api, "/chargebacks"),
            fees=GenericCrudService(api, "/fees"),
            transactions=TransactionService(api),
            verification=TransactionVerificationService(api),
        )
