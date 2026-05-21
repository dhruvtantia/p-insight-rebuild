import pytest

from app.modules.analytics.calculators.risk_v2.beta import calculate_beta
from app.modules.analytics.calculators.risk_v2.correlation import calculate_correlation
from app.modules.analytics.calculators.risk_v2.drawdown import calculate_drawdowns, calculate_max_drawdown
from app.modules.analytics.calculators.risk_v2.returns import calculate_excess_returns, calculate_simple_returns
from app.modules.analytics.calculators.risk_v2.sharpe import calculate_sharpe_ratio
from app.modules.analytics.calculators.risk_v2.sortino import calculate_downside_deviation, calculate_sortino_ratio
from app.modules.analytics.calculators.risk_v2.tracking_error import calculate_tracking_error
from app.modules.analytics.calculators.risk_v2.var import calculate_historical_var
from app.modules.analytics.calculators.risk_v2.volatility import calculate_volatility


def test_risk_v2_calculators_normal_cases() -> None:
    returns = calculate_simple_returns([100, 110, 99, 118.8])

    assert returns == pytest.approx([0.1, -0.1, 0.2])
    assert calculate_excess_returns(returns, risk_free_rate_per_period=0.01) == pytest.approx([0.09, -0.11, 0.19])
    assert calculate_volatility(returns, annualization_factor=1) == pytest.approx(0.152753, abs=0.000001)
    assert calculate_drawdowns([100, 120, 90, 150]) == pytest.approx([0, 0, -0.25, 0])
    assert calculate_max_drawdown([100, 120, 90, 150]) == pytest.approx(-0.25)
    assert calculate_sharpe_ratio(returns, annualization_factor=1) == pytest.approx(0.436436)
    assert calculate_downside_deviation(returns, annualization_factor=1) == pytest.approx(0.04714, abs=0.000001)
    assert calculate_sortino_ratio(returns, annualization_factor=1) == pytest.approx(1.414214, abs=0.000001)
    assert calculate_historical_var([-0.1, -0.05, 0, 0.02, 0.04], confidence_level=0.8) == pytest.approx(0.1)
    assert calculate_beta([0.02, 0.04, 0.06], [0.01, 0.02, 0.03]) == pytest.approx(2)
    assert calculate_tracking_error([0.02, 0.04, 0.01], [0.01, 0.03, 0.01], annualization_factor=1) == pytest.approx(
        0.005774,
        abs=0.000001,
    )
    assert calculate_correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1)


def test_risk_v2_calculators_handle_insufficient_data() -> None:
    assert calculate_simple_returns([]) == []
    assert calculate_simple_returns([100]) == []
    assert calculate_volatility([]) is None
    assert calculate_volatility([0.01]) is None
    assert calculate_drawdowns([]) == []
    assert calculate_max_drawdown([]) is None
    assert calculate_sharpe_ratio([0.01]) is None
    assert calculate_downside_deviation([0.01]) is None
    assert calculate_sortino_ratio([0.01]) is None
    assert calculate_historical_var([]) is None
    assert calculate_historical_var([0.01], confidence_level=1) is None
    assert calculate_beta([0.01], [0.01]) is None
    assert calculate_tracking_error([0.01], [0.01]) is None
    assert calculate_correlation([0.01], [0.01]) is None


def test_risk_v2_calculators_handle_zero_volatility_edge_cases() -> None:
    flat_returns = [0.01, 0.01, 0.01]

    assert calculate_volatility(flat_returns, annualization_factor=1) == 0
    assert calculate_sharpe_ratio(flat_returns, annualization_factor=1) is None
    assert calculate_downside_deviation(flat_returns, annualization_factor=1) == 0
    assert calculate_sortino_ratio(flat_returns, annualization_factor=1) is None
    assert calculate_beta([0.01, 0.02, 0.03], flat_returns) is None
    assert calculate_tracking_error([0.02, 0.02, 0.02], [0.01, 0.01, 0.01], annualization_factor=1) == 0
    assert calculate_correlation([0.01, 0.01, 0.01], [0.02, 0.03, 0.04]) is None
