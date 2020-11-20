# Air Mass 1.5 global spectrum on a horizontal plane ( Hulstrom, Bird and Riordan, Solar Cells, vol 15, 365-391 (1985) )
# the initial data for the incident power sums to 962.58 W/m2, here it is normalised to 1 sun = 1000 W/m2


def sun():
    """
    Returns the sun spectrum and incident power.

    Returns
    -------
        wavelength_sun : list , length = M
            list of light wavelengths for the description of the sun spectrum (unit : nm)
        power_sun      : list , length = M
            list of incident power for every wavelength (unit : W/m2)

    """
    wavelength_sun = [
        305.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0, 340.0, 345.0, 350.0,
        360.0, 370.0, 380.0, 390.0, 400.0, 410.0, 420.0, 430.0, 440.0, 450.0,
        460.0, 470.0, 480.0, 490.0, 500.0, 510.0, 520.0, 530.0, 540.0, 550.0,
        570.0, 590.0, 610.0, 630.0, 650.0, 670.0, 690.0, 710.0, 718.0, 724.0,
        740.0, 753.0, 758.0, 763.0, 768.0, 780.0, 800.0, 816.0, 824.0, 832.0,
        840.0, 860.0, 880.0, 905.0, 915.0, 925.0, 930.0, 937.0, 948.0, 965.0,
        980.0, 994.0, 1040.0, 1070.0, 1100.0, 1120.0, 1130.0, 1137.0, 1161.0,
        1180.0, 1200.0, 1235.0, 1290.0, 1320.0, 1350.0, 1395.0, 1443.0, 1463.0,
        1477.0, 1497.0, 1520.0, 1539.0, 1558.0, 1578.0, 1592.0, 1610.0, 1630.0,
        1646.0, 1678.0, 1740.0, 1800.0, 1860.0, 1920.0, 1960.0, 1985.0, 2005.0,
        2035.0, 2065.0, 2100.0, 2148.0, 2198.0, 2270.0, 2360.0, 2450.0, 2494.0,
        2537.0, 2941.0, 2973.0, 3005.0, 3056.0, 3132.0, 3156.0, 3204.0, 3245.0,
        3317.0, 3344.0, 3450.0, 3573.0, 3765.0, 4045.0
    ]

    power_sun = [
        0.04800, 0.23238, 0.54450, 0.90135, 1.28742, 1.88289, 1.98457, 2.15306,
        2.22299, 3.65008, 5.34591, 6.54581, 7.08628, 7.57170, 9.95916,
        11.44670, 11.68187, 11.15997, 13.02812, 15.09041, 15.89996, 15.91177,
        16.13227, 15.53414, 15.54154, 15.70997, 15.10392, 15.60647, 15.56661,
        23.28738, 29.95176, 28.43396, 29.38973, 28.80925, 28.39838, 27.29172,
        23.75072, 17.68235, 7.41233, 11.80100, 17.21923, 10.77465, 5.56304,
        3.79513, 8.67959, 17.84488, 19.15106, 10.61303, 6.53929, 7.26152,
        13.45886, 19.43966, 20.55956, 13.59171, 6.81306, 4.97575, 2.47678,
        2.53067, 4.77279, 8.20990, 9.33587, 21.93074, 26.39676, 18.50298,
        10.41107, 2.49641, 1.45884, 2.72242, 6.96365, 8.60153, 12.00256,
        20.93583, 17.42957, 7.30847, 1.86257, 0.57198, 1.69503, 1.66614,
        1.98705, 3.96003, 5.31758, 5.19100, 5.29055, 4.24367, 3.91570, 4.43194,
        4.34685, 5.60431, 10.05307, 9.79486, 2.66783, 0.32569, 0.16752,
        0.80785, 1.67246, 1.10419, 2.56887, 2.23780, 3.53577, 4.00654, 4.42194,
        5.61576, 5.22307, 1.86556, 0.73717, 0.85958, 0.90637, 0.22564, 0.25458,
        0.24642, 0.29146, 0.54884, 0.17814, 0.26120, 0.52581, 0.38099, 1.36829,
        1.85006, 2.27700, 1.12998
    ]

    return wavelength_sun, power_sun
