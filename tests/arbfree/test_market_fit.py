"""Fit diagnostics use selected quotes and the configured half-spread floor."""

import numpy as np
import pytest

from openqdata.arbfree.arbfree import ArbFreePricer


@pytest.mark.parametrize("and_vols", [False, True])
@pytest.mark.parametrize("masked", [False, True])
def test_array_market_fit_reports_selected_quotes(monkeypatch, and_vols, masked):
    strikes = np.array([0.8, 0.9, 1., 1.1, 1.2])
    bids = np.array([.20, .15, .10, .05, .01])
    asks = np.array([.24, .19, .14, .09, .01002])
    prices = np.array([.28, .13, .12, .07, .01022])
    mask = np.array([True, False, True, False, True]) if masked else None
    model = ArbFreePricer()

    def price(self, *, expiries, strikes, and_vols):
        assert expiries.shape == strikes.shape
        fits = np.interp(strikes, [0.8, 0.9, 1., 1.1, 1.2], prices)
        return (fits, np.full_like(fits, .2)) if and_vols else fits

    monkeypatch.setattr(ArbFreePricer, "price", price)
    result = model.compute_market_fit(np.full_like(strikes, .5), strikes, bids, asks,
                                      masks=mask, and_vols=and_vols)

    np.testing.assert_allclose(result.fits, np.where(mask, prices, 0.) if masked else prices)
    np.testing.assert_allclose(result.fit_err, [2., 0., 0., 0., 2.] if masked else [2., 1., 0., 0., 2.])
    assert result.pcnt_fit == pytest.approx(2 / 3 if masked else 3 / 5)
    assert result.mean_err == pytest.approx(2. if masked else 5 / 3)
    assert result.median_err == pytest.approx(2.)
    assert result.mean_total_err == pytest.approx(4 / 3 if masked else 1.)
    assert result.median_total_err == pytest.approx(2. if masked else 1.)
    if and_vols:
        np.testing.assert_allclose(result.fit_vols, np.where(mask, .2, 0.) if masked else .2)
    else:
        assert "fit_vols" not in result
