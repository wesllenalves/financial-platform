from decimal import Decimal

from app.rules.engine import Rule, RuleResult, FinancialContext
from app.rules.models import FindingSeverity
from app.transactions.models import TransactionType


class LowBalanceRule:
    """Detects if any account balance is critically low."""
    rule_id = "low_balance"

    def evaluate(self, ctx: FinancialContext) -> list[RuleResult]:
        results = []
        for acc in ctx.accounts:
            # We approximate current balance by taking opening + sum of transactions
            # In a real app we'd use the precomputed current_balance
            account_txns = [t for t in ctx.transactions if t.account_id == acc.id]
            income = sum(t.amount for t in account_txns if t.transaction_type == TransactionType.income)
            expense = sum(t.amount for t in account_txns if t.transaction_type == TransactionType.expense)
            balance = acc.opening_balance + income - expense

            if balance < Decimal("100.00"):
                severity = FindingSeverity.critical if balance < 0 else FindingSeverity.high
                results.append(
                    RuleResult(
                        rule_id=self.rule_id,
                        severity=severity,
                        title=f"Low balance detected in account {acc.name}",
                        evidence={
                            "account_id": str(acc.id),
                            "account_name": acc.name,
                            "current_balance": str(balance),
                            "threshold": "100.00"
                        },
                        estimated_monthly_impact=None
                    )
                )
        return results


class HighExpenseGrowthRule:
    """A mock rule to represent looking at expense growth over time."""
    rule_id = "high_expense_growth"

    def evaluate(self, ctx: FinancialContext) -> list[RuleResult]:
        # For simplicity, if total expenses in period > 5000, trigger warning
        expenses = sum(t.amount for t in ctx.transactions if t.transaction_type == TransactionType.expense)
        if expenses > Decimal("5000.00"):
            return [
                RuleResult(
                    rule_id=self.rule_id,
                    severity=FindingSeverity.medium,
                    title="High total expenses this period",
                    evidence={
                        "total_expenses": str(expenses),
                        "threshold": "5000.00"
                    },
                    estimated_monthly_impact=expenses - Decimal("5000.00")
                )
            ]
        return []


RULES_REGISTRY: list[Rule] = [
    LowBalanceRule(),
    HighExpenseGrowthRule()
]
