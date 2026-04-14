"""Stub ROAI calculator — returns zero/empty values for all metrics.

This is the example skeleton: it has the correct interface but no real
calculation logic. Tests will fail on value assertions but all endpoints
will run without errors. Replace this file with a real implementation.
"""
from __future__ import annotations

from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator

class RoaiPortfolioCalculator(PortfolioCalculator):
    """Stub ROAI calculator — no real implementation."""

    def get_performance(self) -> dict:
        sorted_acts = self.sorted_activities()
        symbols: set[str] = set()
        for act in sorted_acts:
            sym = act.get("symbol", "")
            if sym and act.get("type", "") not in ("DIVIDEND", "FEE", "LIABILITY"):
                symbols.add(sym)

        first_date = min((a["date"] for a in sorted_acts), default=None)
        return {
            "chart": [],
            "firstOrderDate": first_date,
            "performance": {
                "currentNetWorth": 0,
                "currentValue": 0,
                "currentValueInBaseCurrency": 0,
                "netPerformance": 0,
                "netPerformancePercentage": 0,
                "netPerformancePercentageWithCurrencyEffect": 0,
                "netPerformanceWithCurrencyEffect": 0,
                "totalFees": 0,
                "totalInvestment": 0,
                "totalLiabilities": 0.0,
                "totalValueables": 0.0,
            },
        }

    def get_investments(self, group_by: str | None = None) -> dict:
        return {"investments": []}

    def get_holdings(self) -> dict:
        return {"holdings": {}}

    def get_details(self, base_currency: str = "USD") -> dict:
        return {
            "accounts": {
                "default": {
                    "balance": 0.0,
                    "currency": base_currency,
                    "name": "Default Account",
                    "valueInBaseCurrency": 0.0,
                }
            },
            "createdAt": min((a["date"] for a in self.activities), default=None),
            "holdings": {},
            "platforms": {
                "default": {
                    "balance": 0.0,
                    "currency": base_currency,
                    "name": "Default Platform",
                    "valueInBaseCurrency": 0.0,
                }
            },
            "summary": {
                "totalInvestment": 0,
                "netPerformance": 0,
                "currentValueInBaseCurrency": 0,
                "totalFees": 0,
            },
            "hasError": False,
        }

    def get_dividends(self, group_by: str | None = None) -> dict:
        return {"dividends": []}

    def evaluate_report(self) -> dict:
        return {
            "xRay": {
                "categories": [
                    {"key": "accounts", "name": "Accounts", "rules": []},
                    {"key": "currencies", "name": "Currencies", "rules": []},
                    {"key": "fees", "name": "Fees", "rules": []},
                ],
                "statistics": {"rulesActiveCount": 0, "rulesFulfilledCount": 0},
            }
        }

    # --- Translated from TypeScript: calculateOverallPerformance ---
    def calculateOverallPerformance(self, positions):
        currentValueInBaseCurrency = Decimal(0)
        grossPerformance = Decimal(0)
        grossPerformanceWithCurrencyEffect = Decimal(0)
        hasErrors = False
        netPerformance = Decimal(0)
        totalFeesWithCurrencyEffect = Decimal(0)
        totalInterestWithCurrencyEffect = Decimal(0)
        totalInvestment = Decimal(0)
        totalInvestmentWithCurrencyEffect = Decimal(0)
        totalTimeWeightedInvestment = Decimal(0)
        totalTimeWeightedInvestmentWithCurrencyEffect = Decimal(0)
        for currentPosition in positions.filter(lambda x: includeInTotalAssetValue):
            if (currentPosition.feeInBaseCurrency):
                totalFeesWithCurrencyEffect = (totalFeesWithCurrencyEffect + currentPosition.feeInBaseCurrency)
            if (currentPosition.valueInBaseCurrency):
                currentValueInBaseCurrency = (currentValueInBaseCurrency + currentPosition.valueInBaseCurrency)
            else:
                hasErrors = True
            if (currentPosition.investment):
                totalInvestment = (totalInvestment + currentPosition.investment)
                totalInvestmentWithCurrencyEffect = (totalInvestmentWithCurrencyEffect + currentPosition.investmentWithCurrencyEffect)
            else:
                hasErrors = True
            if (currentPosition.grossPerformance):
                grossPerformance = (grossPerformance + currentPosition.grossPerformance)
                grossPerformanceWithCurrencyEffect = (grossPerformanceWithCurrencyEffect + currentPosition.grossPerformanceWithCurrencyEffect)
                netPerformance = (netPerformance + currentPosition.netPerformance)
            elif ((currentPosition.quantity == 0)):
                hasErrors = True
            if (currentPosition.timeWeightedInvestment):
                totalTimeWeightedInvestment = (totalTimeWeightedInvestment + currentPosition.timeWeightedInvestment)
                totalTimeWeightedInvestmentWithCurrencyEffect = (totalTimeWeightedInvestmentWithCurrencyEffect + currentPosition.timeWeightedInvestmentWithCurrencyEffect)
            elif ((currentPosition.quantity == 0)):
                Logger.warn(f"Missing historical market data for {currentPosition.symbol} ({currentPosition.dataSource})", 'PortfolioCalculator')
                hasErrors = True
        return {"currentValueInBaseCurrency": currentValueInBaseCurrency, "hasErrors": hasErrors, "positions": positions, "totalFeesWithCurrencyEffect": totalFeesWithCurrencyEffect, "totalInterestWithCurrencyEffect": totalInterestWithCurrencyEffect, "totalInvestment": totalInvestment, "totalInvestmentWithCurrencyEffect": totalInvestmentWithCurrencyEffect, "activitiesCount": self.activities.filter(lambda x: ['BUY', 'SELL'].includes(type)).length, "createdAt": date.today(), "errors": [], "historicalData": [], "totalLiabilitiesWithCurrencyEffect": Decimal(0)}
    # --- End translated: calculateOverallPerformance ---


    # --- Translated from TypeScript: getPerformanceCalculationType ---
    def getPerformanceCalculationType(self):
        return PerformanceCalculationType.ROAI
    # --- End translated: getPerformanceCalculationType ---


    # --- Translated from TypeScript: getSymbolMetrics ---
    # (output not yet valid Python — included as reference)
    # def getSymbolMetrics(self, options):
    #     chartDateMap = options.get('chartDateMap')
    #     dataSource = options.get('dataSource')
    #     end = options.get('end')
    #     exchangeRates = options.get('exchangeRates')
    #     marketSymbolMap = options.get('marketSymbolMap')
    #     start = options.get('start')
    #     symbol = options.get('symbol')
    #     currentExchangeRate = exchangeRates[date.today().strftime(DATE_FORMAT)]
    #     currentValues = {}
    #     currentValuesWithCurrencyEffect = {}
    #     fees = Decimal(0)
    #     feesAtStartDate = Decimal(0)
    #     feesAtStartDateWithCurrencyEffect = Decimal(0)
    #     feesWithCurrencyEffect = Decimal(0)
    #     grossPerformance = Decimal(0)
    #     grossPerformanceWithCurrencyEffect = Decimal(0)
    #     grossPerformanceAtStartDate = Decimal(0)
    #     grossPerformanceAtStartDateWithCurrencyEffect = Decimal(0)
    #     grossPerformanceFromSells = Decimal(0)
    #     grossPerformanceFromSellsWithCurrencyEffect = Decimal(0)
    #     initialValue = None
    #     initialValueWithCurrencyEffect = None
    #     investmentAtStartDate = None
    #     investmentAtStartDateWithCurrencyEffect = None
    #     investmentValuesAccumulated = {}
    #     investmentValuesAccumulatedWithCurrencyEffect = {}
    #     investmentValuesWithCurrencyEffect = {}
    #     lastAveragePrice = Decimal(0)
    #     lastAveragePriceWithCurrencyEffect = Decimal(0)
    #     netPerformanceValues = {}
    #     netPerformanceValuesWithCurrencyEffect = {}
    #     timeWeightedInvestmentValues = {}
    #     timeWeightedInvestmentValuesWithCurrencyEffect = {}
    #     totalAccountBalanceInBaseCurrency = Decimal(0)
    #     totalDividend = Decimal(0)
    #     totalDividendInBaseCurrency = Decimal(0)
    #     totalInterest = Decimal(0)
    #     totalInterestInBaseCurrency = Decimal(0)
    #     totalInvestment = Decimal(0)
    #     totalInvestmentFromBuyTransactions = Decimal(0)
    #     totalInvestmentFromBuyTransactionsWithCurrencyEffect = Decimal(0)
    #     totalInvestmentWithCurrencyEffect = Decimal(0)
    #     totalLiabilities = Decimal(0)
    #     totalLiabilitiesInBaseCurrency = Decimal(0)
    #     totalQuantityFromBuyTransactions = Decimal(0)
    #     totalUnits = Decimal(0)
    #     valueAtStartDate = None
    #     valueAtStartDateWithCurrencyEffect = None
    #     orders = copy.deepcopy(self.activities.filter(lambda x: SymbolProfile.symbol === symbol))
    #     isCash = orders[0].SymbolProfile.assetSubClass === 'CASH'
    #     if (orders.length <= 0):
    #         return {"currentValues": {}, "currentValuesWithCurrencyEffect": {}, "feesWithCurrencyEffect": Decimal(0), "grossPerformance": Decimal(0), "grossPerformancePercentage": Decimal(0), "grossPerformancePercentageWithCurrencyEffect": Decimal(0), "grossPerformanceWithCurrencyEffect": Decimal(0), "hasErrors": False, "initialValue": Decimal(0), "initialValueWithCurrencyEffect": Decimal(0), "investmentValuesAccumulated": {}, "investmentValuesAccumulatedWithCurrencyEffect": {}, "investmentValuesWithCurrencyEffect": {}, "netPerformance": Decimal(0), "netPerformancePercentage": Decimal(0), "netPerformancePercentageWithCurrencyEffectMap": {}, "netPerformanceValues": {}, "netPerformanceValuesWithCurrencyEffect": {}, "netPerformanceWithCurrencyEffectMap": {}, "timeWeightedInvestment": Decimal(0), "timeWeightedInvestmentValues": {}, "timeWeightedInvestmentValuesWithCurrencyEffect": {}, "timeWeightedInvestmentWithCurrencyEffect": Decimal(0), "totalAccountBalanceInBaseCurrency": Decimal(0), "totalDividend": Decimal(0), "totalDividendInBaseCurrency": Decimal(0), "totalInterest": Decimal(0), "totalInterestInBaseCurrency": Decimal(0), "totalInvestment": Decimal(0), "totalInvestmentWithCurrencyEffect": Decimal(0), "totalLiabilities": Decimal(0), "totalLiabilitiesInBaseCurrency": Decimal(0)}
    #     dateOfFirstTransaction = parse_date(orders[0].date)
    #     endDateString = end.strftime(DATE_FORMAT)
    #     startDateString = start.strftime(DATE_FORMAT)
    #     unitPriceAtStartDate = marketSymbolMap[startDateString][symbol]
    #     unitPriceAtEndDate = marketSymbolMap[endDateString][symbol]
    #     latestActivity = orders[1]
    #     if (dataSource === 'MANUAL' && ['BUY', 'SELL'].includes(latestActivity.type) && latestActivity.unitPrice && unitPriceAtEndDate):
    #         unitPriceAtEndDate = latestActivity.unitPrice
    #     elif (isCash):
    #         unitPriceAtEndDate = Decimal(str(1))
    #     if (unitPriceAtEndDate || (unitPriceAtStartDate && dateOfFirstTransaction < start)):
    #         return {"currentValues": {}, "currentValuesWithCurrencyEffect": {}, "feesWithCurrencyEffect": Decimal(0), "grossPerformance": Decimal(0), "grossPerformancePercentage": Decimal(0), "grossPerformancePercentageWithCurrencyEffect": Decimal(0), "grossPerformanceWithCurrencyEffect": Decimal(0), "hasErrors": True, "initialValue": Decimal(0), "initialValueWithCurrencyEffect": Decimal(0), "investmentValuesAccumulated": {}, "investmentValuesAccumulatedWithCurrencyEffect": {}, "investmentValuesWithCurrencyEffect": {}, "netPerformance": Decimal(0), "netPerformancePercentage": Decimal(0), "netPerformancePercentageWithCurrencyEffectMap": {}, "netPerformanceWithCurrencyEffectMap": {}, "netPerformanceValues": {}, "netPerformanceValuesWithCurrencyEffect": {}, "timeWeightedInvestment": Decimal(0), "timeWeightedInvestmentValues": {}, "timeWeightedInvestmentValuesWithCurrencyEffect": {}, "timeWeightedInvestmentWithCurrencyEffect": Decimal(0), "totalAccountBalanceInBaseCurrency": Decimal(0), "totalDividend": Decimal(0), "totalDividendInBaseCurrency": Decimal(0), "totalInterest": Decimal(0), "totalInterestInBaseCurrency": Decimal(0), "totalInvestment": Decimal(0), "totalInvestmentWithCurrencyEffect": Decimal(0), "totalLiabilities": Decimal(0), "totalLiabilitiesInBaseCurrency": Decimal(0)}
    #     orders.append({"date": startDateString, "fee": Decimal(0), "feeInBaseCurrency": Decimal(0), "itemType": 'start', "quantity": Decimal(0), "SymbolProfile": {"dataSource": dataSource, "symbol": symbol, "assetSubClass": 'CASH' if isCash else None}, "type": 'BUY', "unitPrice": unitPriceAtStartDate})
    #     orders.append({"date": endDateString, "fee": Decimal(0), "feeInBaseCurrency": Decimal(0), "itemType": 'end', "SymbolProfile": {"dataSource": dataSource, "symbol": symbol, "assetSubClass": 'CASH' if isCash else None}, "quantity": Decimal(0), "type": 'BUY', "unitPrice": unitPriceAtEndDate})
    #     lastUnitPrice = None
    #     ordersByDate = {}
    #     for order in orders:
    #         ordersByDate[order.date] = ordersByDate[order.date] ?? []
    #         ordersByDate[order.date].append(order)
    #     if (self.chartDates):
    #         self.chartDates = Object.keys(chartDateMap).sort()
    #     for dateString in self.chartDates:
    #         if (dateString < startDateString):
    #             pass
    #         elif (dateString > endDateString):
    #             pass
    #         if (ordersByDate[dateString].length > 0):
    #             for order in ordersByDate[dateString]:
    #                 order.unitPriceFromMarketData = marketSymbolMap[dateString][symbol] ?? lastUnitPrice
    #         else:
    #             orders.append({"date": dateString, "fee": Decimal(0), "feeInBaseCurrency": Decimal(0), "quantity": Decimal(0), "SymbolProfile": {"dataSource": dataSource, "symbol": symbol, "assetSubClass": 'CASH' if isCash else None}, "type": 'BUY', "unitPrice": marketSymbolMap[dateString][symbol] ?? lastUnitPrice, "unitPriceFromMarketData": marketSymbolMap[dateString][symbol] ?? lastUnitPrice})
    #         latestActivity = orders[1]
    #         lastUnitPrice = latestActivity.unitPriceFromMarketData ?? latestActivity.unitPrice
    #     orders = sorted(orders, key=lambda x: sortIndex.getTime())
    #     indexOfStartOrder = orders.findIndex(lambda x: itemType === 'start')
    #     indexOfEndOrder = orders.findIndex(lambda x: itemType === 'end')
    #     totalInvestmentDays = 0
    #     sumOfTimeWeightedInvestments = Decimal(0)
    #     sumOfTimeWeightedInvestmentsWithCurrencyEffect = Decimal(0)
    #     i = 0
    #     while i < orders.length:
    #         order = orders[i]
    #         if (PortfolioCalculator.ENABLE_LOGGING):
    #             console.log()
    #             console.log()
    #             console.log(i + 1, order.date, order.type, f"({order.itemType})" if order.itemType else '')
    #         exchangeRateAtOrderDate = exchangeRates[order.date]
    #         if (order.type === 'DIVIDEND'):
    #             dividend = (order.quantity * order.unitPrice)
    #             totalDividend = (totalDividend + dividend)
    #             totalDividendInBaseCurrency = (totalDividendInBaseCurrency + (dividend * exchangeRateAtOrderDate ?? 1))
    #         elif (order.type === 'INTEREST'):
    #             interest = (order.quantity * order.unitPrice)
    #             totalInterest = (totalInterest + interest)
    #             totalInterestInBaseCurrency = (totalInterestInBaseCurrency + (interest * exchangeRateAtOrderDate ?? 1))
    #         elif (order.type === 'LIABILITY'):
    #             liabilities = (order.quantity * order.unitPrice)
    #             totalLiabilities = (totalLiabilities + liabilities)
    #             totalLiabilitiesInBaseCurrency = (totalLiabilitiesInBaseCurrency + (liabilities * exchangeRateAtOrderDate ?? 1))
    #         if (order.itemType === 'start'):
    #             order.unitPrice = orders[i + 1].unitPrice if indexOfStartOrder === 0 else unitPriceAtStartDate
    #         if (order.fee):
    #             order.feeInBaseCurrency = (order.fee * currentExchangeRate ?? 1)
    #             order.feeInBaseCurrencyWithCurrencyEffect = (order.fee * exchangeRateAtOrderDate ?? 1)
    #         unitPrice = order.unitPrice if ['BUY', 'SELL'].includes(order.type) else order.unitPriceFromMarketData
    #         if (unitPrice):
    #             order.unitPriceInBaseCurrency = (unitPrice * currentExchangeRate ?? 1)
    #             order.unitPriceInBaseCurrencyWithCurrencyEffect = (unitPrice * exchangeRateAtOrderDate ?? 1)
    #         marketPriceInBaseCurrency = (order.unitPriceFromMarketData * currentExchangeRate ?? 1) ?? Decimal(0)
    #         marketPriceInBaseCurrencyWithCurrencyEffect = (order.unitPriceFromMarketData * exchangeRateAtOrderDate ?? 1) ?? Decimal(0)
    #         valueOfInvestmentBeforeTransaction = (totalUnits * marketPriceInBaseCurrency)
    #         valueOfInvestmentBeforeTransactionWithCurrencyEffect = (totalUnits * marketPriceInBaseCurrencyWithCurrencyEffect)
    #         if (investmentAtStartDate && i >= indexOfStartOrder):
    #             investmentAtStartDate = totalInvestment ?? Decimal(0)
    #             investmentAtStartDateWithCurrencyEffect = totalInvestmentWithCurrencyEffect ?? Decimal(0)
    #             valueAtStartDate = valueOfInvestmentBeforeTransaction
    #             valueAtStartDateWithCurrencyEffect = valueOfInvestmentBeforeTransactionWithCurrencyEffect
    #         transactionInvestment = Decimal(0)
    #         transactionInvestmentWithCurrencyEffect = Decimal(0)
    #         if (order.type === 'BUY'):
    #             transactionInvestment = ((order.quantity * order.unitPriceInBaseCurrency) * getFactor(order.type))
    #             transactionInvestmentWithCurrencyEffect = ((order.quantity * order.unitPriceInBaseCurrencyWithCurrencyEffect) * getFactor(order.type))
    #             totalQuantityFromBuyTransactions = (totalQuantityFromBuyTransactions + order.quantity)
    #             totalInvestmentFromBuyTransactions = (totalInvestmentFromBuyTransactions + transactionInvestment)
    #             totalInvestmentFromBuyTransactionsWithCurrencyEffect = (totalInvestmentFromBuyTransactionsWithCurrencyEffect + transactionInvestmentWithCurrencyEffect)
    #         elif (order.type === 'SELL'):
    #             if ((totalUnits > 0)):
    #                 transactionInvestment = (((totalInvestment / totalUnits) * order.quantity) * getFactor(order.type))
    #                 transactionInvestmentWithCurrencyEffect = (((totalInvestmentWithCurrencyEffect / totalUnits) * order.quantity) * getFactor(order.type))
    #         if (PortfolioCalculator.ENABLE_LOGGING):
    #             console.log('order.quantity', float(order.quantity))
    #             console.log('transactionInvestment', float(transactionInvestment))
    #             console.log('transactionInvestmentWithCurrencyEffect', float(transactionInvestmentWithCurrencyEffect))
    #         totalInvestmentBeforeTransaction = totalInvestment
    #         totalInvestmentBeforeTransactionWithCurrencyEffect = totalInvestmentWithCurrencyEffect
    #         totalInvestment = (totalInvestment + transactionInvestment)
    #         totalInvestmentWithCurrencyEffect = (totalInvestmentWithCurrencyEffect + transactionInvestmentWithCurrencyEffect)
    #         if (i >= indexOfStartOrder && initialValue):
    #             if (i === indexOfStartOrder && (valueOfInvestmentBeforeTransaction == 0)):
    #                 initialValue = valueOfInvestmentBeforeTransaction
    #                 initialValueWithCurrencyEffect = valueOfInvestmentBeforeTransactionWithCurrencyEffect
    #             elif ((transactionInvestment > 0)):
    #                 initialValue = transactionInvestment
    #                 initialValueWithCurrencyEffect = transactionInvestmentWithCurrencyEffect
    #         fees = (fees + order.feeInBaseCurrency ?? 0)
    #         feesWithCurrencyEffect = (feesWithCurrencyEffect + order.feeInBaseCurrencyWithCurrencyEffect ?? 0)
    #         totalUnits = (totalUnits + (order.quantity * getFactor(order.type)))
    #         valueOfInvestment = (totalUnits * marketPriceInBaseCurrency)
    #         valueOfInvestmentWithCurrencyEffect = (totalUnits * marketPriceInBaseCurrencyWithCurrencyEffect)
    #         grossPerformanceFromSell = ((order.unitPriceInBaseCurrency - lastAveragePrice) * order.quantity) if order.type === 'SELL' else Decimal(0)
    #         grossPerformanceFromSellWithCurrencyEffect = ((order.unitPriceInBaseCurrencyWithCurrencyEffect - lastAveragePriceWithCurrencyEffect) * order.quantity) if order.type === 'SELL' else Decimal(0)
    #         grossPerformanceFromSells = (grossPerformanceFromSells + grossPerformanceFromSell)
    #         grossPerformanceFromSellsWithCurrencyEffect = (grossPerformanceFromSellsWithCurrencyEffect + grossPerformanceFromSellWithCurrencyEffect)
    #         lastAveragePrice = Decimal(0) if (totalQuantityFromBuyTransactions == 0) else (totalInvestmentFromBuyTransactions / totalQuantityFromBuyTransactions)
    #         lastAveragePriceWithCurrencyEffect = Decimal(0) if (totalQuantityFromBuyTransactions == 0) else (totalInvestmentFromBuyTransactionsWithCurrencyEffect / totalQuantityFromBuyTransactions)
    #         if ((totalUnits == 0)):
    #             totalInvestmentFromBuyTransactions = Decimal(0)
    #             totalInvestmentFromBuyTransactionsWithCurrencyEffect = Decimal(0)
    #             totalQuantityFromBuyTransactions = Decimal(0)
    #         if (PortfolioCalculator.ENABLE_LOGGING):
    #             console.log('grossPerformanceFromSells', float(grossPerformanceFromSells))
    #             console.log('grossPerformanceFromSellWithCurrencyEffect', float(grossPerformanceFromSellWithCurrencyEffect))
    #         newGrossPerformance = ((valueOfInvestment - totalInvestment) + grossPerformanceFromSells)
    #         newGrossPerformanceWithCurrencyEffect = ((valueOfInvestmentWithCurrencyEffect - totalInvestmentWithCurrencyEffect) + grossPerformanceFromSellsWithCurrencyEffect)
    #         grossPerformance = newGrossPerformance
    #         grossPerformanceWithCurrencyEffect = newGrossPerformanceWithCurrencyEffect
    #         if (order.itemType === 'start'):
    #             feesAtStartDate = fees
    #             feesAtStartDateWithCurrencyEffect = feesWithCurrencyEffect
    #             grossPerformanceAtStartDate = grossPerformance
    #             grossPerformanceAtStartDateWithCurrencyEffect = grossPerformanceWithCurrencyEffect
    #         if (i > indexOfStartOrder):
    #             if ((valueOfInvestmentBeforeTransaction > 0) && ['BUY', 'SELL'].includes(order.type)):
    #                 orderDate = parse_date(order.date)
    #                 previousOrderDate = parse_date(orders[i - 1].date)
    #                 daysSinceLastOrder = (orderDate - previousOrderDate).days
    #                 if (daysSinceLastOrder <= 0):
    #                     daysSinceLastOrder = Number.EPSILON
    #                 totalInvestmentDaysdaysSinceLastOrder
    #                 sumOfTimeWeightedInvestments = (sumOfTimeWeightedInvestments + (((valueAtStartDate - investmentAtStartDate) + totalInvestmentBeforeTransaction) * daysSinceLastOrder))
    #                 sumOfTimeWeightedInvestmentsWithCurrencyEffect = (sumOfTimeWeightedInvestmentsWithCurrencyEffect + (((valueAtStartDateWithCurrencyEffect - investmentAtStartDateWithCurrencyEffect) + totalInvestmentBeforeTransactionWithCurrencyEffect) * daysSinceLastOrder))
    #             currentValues[order.date] = valueOfInvestment
    #             currentValuesWithCurrencyEffect[order.date] = valueOfInvestmentWithCurrencyEffect
    #             netPerformanceValues[order.date] = ((grossPerformance - grossPerformanceAtStartDate) - (fees - feesAtStartDate))
    #             netPerformanceValuesWithCurrencyEffect[order.date] = ((grossPerformanceWithCurrencyEffect - grossPerformanceAtStartDateWithCurrencyEffect) - (feesWithCurrencyEffect - feesAtStartDateWithCurrencyEffect))
    #             investmentValuesAccumulated[order.date] = totalInvestment
    #             investmentValuesAccumulatedWithCurrencyEffect[order.date] = totalInvestmentWithCurrencyEffect
    #             investmentValuesWithCurrencyEffect[order.date] = ((investmentValuesWithCurrencyEffect[order.date] ?? Decimal(0)) + transactionInvestmentWithCurrencyEffect)
    #             timeWeightedInvestmentValues[order.date] = (sumOfTimeWeightedInvestments / totalInvestmentDays) if totalInvestmentDays > Number.EPSILON else totalInvestment if (totalInvestment > 0) else Decimal(0)
    #             timeWeightedInvestmentValuesWithCurrencyEffect[order.date] = (sumOfTimeWeightedInvestmentsWithCurrencyEffect / totalInvestmentDays) if totalInvestmentDays > Number.EPSILON else totalInvestmentWithCurrencyEffect if (totalInvestmentWithCurrencyEffect > 0) else Decimal(0)
    #         if (PortfolioCalculator.ENABLE_LOGGING):
    #             console.log('totalInvestment', float(totalInvestment))
    #             console.log('totalInvestmentWithCurrencyEffect', float(totalInvestmentWithCurrencyEffect))
    #             console.log('totalGrossPerformance', float((grossPerformance - grossPerformanceAtStartDate)))
    #             console.log('totalGrossPerformanceWithCurrencyEffect', float((grossPerformanceWithCurrencyEffect - grossPerformanceAtStartDateWithCurrencyEffect)))
    #         if (i === indexOfEndOrder):
    #             pass
    #         i1
    #     totalGrossPerformance = (grossPerformance - grossPerformanceAtStartDate)
    #     totalGrossPerformanceWithCurrencyEffect = (grossPerformanceWithCurrencyEffect - grossPerformanceAtStartDateWithCurrencyEffect)
    #     totalNetPerformance = ((grossPerformance - grossPerformanceAtStartDate) - (fees - feesAtStartDate))
    #     timeWeightedAverageInvestmentBetweenStartAndEndDate = (sumOfTimeWeightedInvestments / totalInvestmentDays) if totalInvestmentDays > 0 else Decimal(0)
    #     timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect = (sumOfTimeWeightedInvestmentsWithCurrencyEffect / totalInvestmentDays) if totalInvestmentDays > 0 else Decimal(0)
    #     grossPerformancePercentage = (totalGrossPerformance / timeWeightedAverageInvestmentBetweenStartAndEndDate) if (timeWeightedAverageInvestmentBetweenStartAndEndDate > 0) else Decimal(0)
    #     grossPerformancePercentageWithCurrencyEffect = (totalGrossPerformanceWithCurrencyEffect / timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect) if (timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect > 0) else Decimal(0)
    #     feesPerUnit = ((fees - feesAtStartDate) / totalUnits) if (totalUnits > 0) else Decimal(0)
    #     feesPerUnitWithCurrencyEffect = ((feesWithCurrencyEffect - feesAtStartDateWithCurrencyEffect) / totalUnits) if (totalUnits > 0) else Decimal(0)
    #     netPerformancePercentage = (totalNetPerformance / timeWeightedAverageInvestmentBetweenStartAndEndDate) if (timeWeightedAverageInvestmentBetweenStartAndEndDate > 0) else Decimal(0)
    #     netPerformancePercentageWithCurrencyEffectMap = {}
    #     netPerformanceWithCurrencyEffectMap = {}
    #     for dateRange in :
    #         dateInterval = getIntervalFromDateRange(dateRange)
    #         endDate = dateInterval.endDate
    #         startDate = dateInterval.startDate
    #         if (startDate < start):
    #             startDate = start
    #         rangeEndDateString = endDate.strftime(DATE_FORMAT)
    #         rangeStartDateString = startDate.strftime(DATE_FORMAT)
    #         currentValuesAtDateRangeStartWithCurrencyEffect = currentValuesWithCurrencyEffect[rangeStartDateString] ?? Decimal(0)
    #         investmentValuesAccumulatedAtStartDateWithCurrencyEffect = investmentValuesAccumulatedWithCurrencyEffect[rangeStartDateString] ?? Decimal(0)
    #         grossPerformanceAtDateRangeStartWithCurrencyEffect = (currentValuesAtDateRangeStartWithCurrencyEffect - investmentValuesAccumulatedAtStartDateWithCurrencyEffect)
    #         average = Decimal(0)
    #         dayCount = 0
    #         i = self.chartDates.length - 1
    #         while i >= 0:
    #             date = self.chartDates[i]
    #             if (date > rangeEndDateString):
    #                 pass
    #             elif (date < rangeStartDateString):
    #                 pass
    #             if (investmentValuesAccumulatedWithCurrencyEffect[date] instanceof Big && (investmentValuesAccumulatedWithCurrencyEffect[date] > 0)):
    #                 average = (average + (investmentValuesAccumulatedWithCurrencyEffect[date] + grossPerformanceAtDateRangeStartWithCurrencyEffect))
    #                 dayCount += 1
    #             i1
    #         if (dayCount > 0):
    #             average = (average / dayCount)
    #         netPerformanceWithCurrencyEffectMap[dateRange] = (netPerformanceValuesWithCurrencyEffect[rangeEndDateString] - ) ?? Decimal(0)
    #         netPerformancePercentageWithCurrencyEffectMap[dateRange] = (netPerformanceWithCurrencyEffectMap[dateRange] / average) if (average > 0) else Decimal(0)
    #     if (PortfolioCalculator.ENABLE_LOGGING):
    #         console.log(f"""
    #                 {symbol}
    #                 Unit price: {round(orders[indexOfStartOrder].unitPrice, 2)} -> {round(unitPriceAtEndDate, 2)}
    #                 Total investment: {round(totalInvestment, 2)}
    #                 Total investment with currency effect: {round(totalInvestmentWithCurrencyEffect, 2)}
    #                 Time weighted investment: {round(timeWeightedAverageInvestmentBetweenStartAndEndDate, 2)}
    #                 Time weighted investment with currency effect: {round(timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect, 2)}
    #                 Total dividend: {round(totalDividend, 2)}
    #                 Gross performance: {round(totalGrossPerformance, 2)} / {round((grossPerformancePercentage * 100), 2)}%
    #                 Gross performance with currency effect: {round(totalGrossPerformanceWithCurrencyEffect, 2)} / {round((grossPerformancePercentageWithCurrencyEffect * 100), 2)}%
    #                 Fees per unit: {round(feesPerUnit, 2)}
    #                 Fees per unit with currency effect: {round(feesPerUnitWithCurrencyEffect, 2)}
    #                 Net performance: {round(totalNetPerformance, 2)} / {round((netPerformancePercentage * 100), 2)}%
    #                 Net performance with currency effect: {round(netPerformancePercentageWithCurrencyEffectMap['max'], 2)}%""")
    #     return {"currentValues": currentValues, "currentValuesWithCurrencyEffect": currentValuesWithCurrencyEffect, "feesWithCurrencyEffect": feesWithCurrencyEffect, "grossPerformancePercentage": grossPerformancePercentage, "grossPerformancePercentageWithCurrencyEffect": grossPerformancePercentageWithCurrencyEffect, "initialValue": initialValue, "initialValueWithCurrencyEffect": initialValueWithCurrencyEffect, "investmentValuesAccumulated": investmentValuesAccumulated, "investmentValuesAccumulatedWithCurrencyEffect": investmentValuesAccumulatedWithCurrencyEffect, "investmentValuesWithCurrencyEffect": investmentValuesWithCurrencyEffect, "netPerformancePercentage": netPerformancePercentage, "netPerformancePercentageWithCurrencyEffectMap": netPerformancePercentageWithCurrencyEffectMap, "netPerformanceValues": netPerformanceValues, "netPerformanceValuesWithCurrencyEffect": netPerformanceValuesWithCurrencyEffect, "netPerformanceWithCurrencyEffectMap": netPerformanceWithCurrencyEffectMap, "timeWeightedInvestmentValues": timeWeightedInvestmentValues, "timeWeightedInvestmentValuesWithCurrencyEffect": timeWeightedInvestmentValuesWithCurrencyEffect, "totalAccountBalanceInBaseCurrency": totalAccountBalanceInBaseCurrency, "totalDividend": totalDividend, "totalDividendInBaseCurrency": totalDividendInBaseCurrency, "totalInterest": totalInterest, "totalInterestInBaseCurrency": totalInterestInBaseCurrency, "totalInvestment": totalInvestment, "totalInvestmentWithCurrencyEffect": totalInvestmentWithCurrencyEffect, "totalLiabilities": totalLiabilities, "totalLiabilitiesInBaseCurrency": totalLiabilitiesInBaseCurrency, "grossPerformance": totalGrossPerformance, "grossPerformanceWithCurrencyEffect": totalGrossPerformanceWithCurrencyEffect, "hasErrors": (totalUnits > 0) && (initialValue || unitPriceAtEndDate), "netPerformance": totalNetPerformance, "timeWeightedInvestment": timeWeightedAverageInvestmentBetweenStartAndEndDate, "timeWeightedInvestmentWithCurrencyEffect": timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect}
    # --- End translated: getSymbolMetrics ---

