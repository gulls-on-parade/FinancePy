# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import time

from FinTestCases import FinTestCases, globalTestCaseMode

from financepy.finutils.FinDate import FinDate
from financepy.finutils.FinFrequency import FinFrequencyTypes
from financepy.finutils.FinDayCount import FinDayCountTypes
from financepy.models.FinModelRatesBK import FinModelRatesBK

from financepy.products.libor.FinLiborSwap import FinLiborSwap
from financepy.market.curves.FinLiborCurve import FinLiborCurve
from financepy.market.curves.FinFlatCurve import FinFlatCurve
from financepy.products.bonds.FinBond import FinBond
from financepy.products.bonds.FinBondEmbeddedOption import FinBondEmbeddedOption

testCases = FinTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinBondEmbeddedOptionMATLAB():
    # https://fr.mathworks.com/help/fininst/optembndbybk.html
    # I FIND THAT THE PRICE CONVERGES TO 102.365 WHICH IS CLOSE TO 102.382
    # FOUND BY MATLAB ALTHOUGH THEY DO NOT EXAMINE THE ASYMPTOTIC PRICE
    # WHICH MIGHT BE A BETTER MATCH - ALSO THEY DO NOT USE A REALISTIC VOL

    settlementDate = FinDate(1, 1, 2007)

    ###########################################################################

    dcType = FinDayCountTypes.THIRTY_360
    fixedFreq = FinFrequencyTypes.ANNUAL
    swap1 = FinLiborSwap(settlementDate, "1Y", 0.0350, fixedFreq, dcType)
    swap2 = FinLiborSwap(settlementDate, "2Y", 0.0400, fixedFreq, dcType)
    swap3 = FinLiborSwap(settlementDate, "3Y", 0.0450, fixedFreq, dcType)
    swaps = [swap1, swap2, swap3]
    discountCurve = FinLiborCurve("USD_LIBOR", settlementDate, [], [], swaps)

    ###########################################################################

    maturityDate = FinDate(1, 1, 2010)
    coupon = 0.0525
    frequencyType = FinFrequencyTypes.ANNUAL
    accrualType = FinDayCountTypes.ACT_ACT_ICMA
    bond = FinBond(maturityDate, coupon, frequencyType, accrualType)

    callDates = []
    callPrices = []
    putDates = []
    putPrices = []

    putDate = FinDate(1, 1, 2008)
    for i in range(0, 24):
        putDates.append(putDate)
        putPrices.append(100)
        putDate = putDate.addMonths(1)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.valueBondUsingDiscountCurve(settlementDate, discountCurve)
    testCases.print("Bond Pure Price:", v)

    sigma = 0.01  # This volatility is very small for a BK process
    a = 0.1

    puttableBond = FinBondEmbeddedOption(maturityDate, coupon,
                                         frequencyType, accrualType,
                                         callDates, callPrices,
                                         putDates, putPrices)

    testCases.header("PERIOD", "NumTimeSteps", "BondWithOption", "BondPure")

    timeSteps = range(100, 200, 10)  # 1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = FinModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlementDate, discountCurve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'], v['bondpure'])
        values.append(v['bondwithoption'])

    plt.figure()
    plt.plot(timeSteps, values)

###############################################################################


def test_FinBondEmbeddedOptionQUANTLIB():

    # Based on example at the nice blog on Quantlib at
    # http://gouthamanbalaraman.com/blog/callable-bond-quantlib-python.html
    # I get a price of 68.97 for 1000 time steps which is higher than the
    # 68.38 found in blog article. But this is for 40 grid points.
    # Note also that a basis point vol of 0.120 is 12% which is VERY HIGH!

    valueDate = FinDate(16, 8, 2016)
    settlementDate = valueDate.addWorkDays(3)

    ###########################################################################

    discountCurve = FinFlatCurve(valueDate, 0.035,
                                 FinFrequencyTypes.SEMI_ANNUAL)

    ###########################################################################

    maturityDate = FinDate(15, 9, 2022)
    coupon = 0.025
    frequencyType = FinFrequencyTypes.QUARTERLY
    accrualType = FinDayCountTypes.ACT_ACT_ICMA
    bond = FinBond(maturityDate, coupon, frequencyType, accrualType)

    ###########################################################################
    # Set up the call and put times and prices
    ###########################################################################

    nextCallDate = FinDate(15, 9, 2016)
    callDates = [nextCallDate]
    callPrices = [100.0]

    for i in range(1, 24):
        nextCallDate = nextCallDate.addMonths(3)
        callDates.append(nextCallDate)
        callPrices.append(100.0)

    putDates = []
    putPrices = []

    # the value used in blog of 12% bp vol is unrealistic
    sigma = 0.12/0.035  # basis point volatility
    a = 0.03

    puttableBond = FinBondEmbeddedOption(maturityDate, coupon,
                                         frequencyType, accrualType,
                                         callDates, callPrices,
                                         putDates, putPrices)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.valueBondUsingDiscountCurve(settlementDate, discountCurve)
    testCases.print("Bond Pure Price:", v)

    testCases.header("PERIOD", "NumTimeSteps", "BondWithOption", "BondPure")
    timeSteps = range(100, 200, 10) #1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = FinModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlementDate, discountCurve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'], v['bondpure'])
        values.append(v['bondwithoption'])

    plt.figure()
    plt.title("Puttable Bond Price Convergence")
    plt.plot(timeSteps, values)

###############################################################################


test_FinBondEmbeddedOptionMATLAB()
test_FinBondEmbeddedOptionQUANTLIB()