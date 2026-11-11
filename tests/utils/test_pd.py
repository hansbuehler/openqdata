from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from openqdata.utils.pd import create_empty_df, verify_schema


def test_create_empty_df_preserves_schema_columns_and_dtypes() -> None:
    schema = {
        "name": np.dtype("O"),
        "count": np.dtype("int32"),
        "weight": np.dtype("float32"),
    }

    df = create_empty_df(schema)

    assert df.empty
    assert list(df.columns) == list(schema)
    for column, dtype in schema.items():
        assert df[column].dtype == dtype


def test_verify_schema_returns_same_dataframe_for_matching_schema() -> None:
    df = pd.DataFrame(
        {
            "count": pd.Series([1, 2], dtype="int32"),
            "weight": pd.Series([1.5, 2.5], dtype="float32"),
        }
    )
    schema = {
        "count": np.dtype("int32"),
        "weight": np.dtype("float32"),
    }

    validated = verify_schema(df, schema)

    assert validated is df


def test_verify_schema_header_callable_is_lazy_on_success() -> None:
    df = pd.DataFrame({"count": pd.Series([1], dtype="int32")})
    calls: list[str] = []

    def header() -> str:
        calls.append("called")
        return "sample"

    verify_schema(df, {"count": np.dtype("int32")}, header)

    assert calls == []


def test_verify_schema_rejects_missing_and_extra_columns_with_header() -> None:
    df = pd.DataFrame(
        {
            "count": pd.Series([1], dtype="int32"),
            "extra": pd.Series([2], dtype="int32"),
        }
    )

    with pytest.raises(ValueError, match="sample: .*missing columns.*weight.*extra columns.*extra"):
        verify_schema(
            df,
            {
                "count": np.dtype("int32"),
                "weight": np.dtype("float32"),
            },
            "sample",
        )


def test_verify_schema_rejects_extra_columns_unless_explicitly_allowed() -> None:
    df = pd.DataFrame(
        {
            "count": pd.Series([1], dtype="int32"),
            "extra": pd.Series([2], dtype="int32"),
        }
    )
    schema = {"count": np.dtype("int32")}

    with pytest.raises(ValueError, match="extra columns.*extra"):
        verify_schema(df, schema)

    validated = verify_schema(df, schema, allow_extra_columns=True)
    assert validated is df


def test_verify_schema_rejects_dtype_mismatch() -> None:
    df = pd.DataFrame({"count": pd.Series([1], dtype="int64")})

    with pytest.raises(ValueError, match="schema mismatches.*'count'.*int32.*int64"):
        verify_schema(df, {"count": np.dtype("int32")})


def test_verify_schema_invokes_header_callable_only_when_needed() -> None:
    df = pd.DataFrame({"count": pd.Series([1], dtype="int32")})
    calls: list[str] = []

    def header() -> str:
        calls.append("called")
        return "sample"

    with pytest.raises(ValueError, match="sample: .*missing columns.*weight"):
        verify_schema(
            df,
            {
                "count": np.dtype("int32"),
                "weight": np.dtype("float32"),
            },
            header,
        )

    assert calls == ["called"]


def test_verify_schema_rejects_invalid_inputs() -> None:
    with pytest.raises(AssertionError, match="must be a pandas DataFrame"):
        verify_schema([], {"count": np.dtype("int32")})

    with pytest.raises(AssertionError, match="schema must be a mapping"):
        verify_schema(pd.DataFrame({"count": [1]}), ["count"])


def test_verify_schema_rejects_invalid_schema_dtype() -> None:
    df = pd.DataFrame({"count": pd.Series([1], dtype="int32")})

    with pytest.raises(ValueError, match="Invalid dtype for column 'count'"):
        verify_schema(df, {"count": object()})

def test_restore_object_strings_preserves_values_and_numeric_validation():
    from openqdata.utils.pd import restore_object_strings
    frame = pd.DataFrame({"symbol": pd.Series(["SPX", None], dtype="string"),
                          "value": pd.Series([1., 2.], dtype="float64")})
    schema = {"symbol": np.dtype("O"), "value": np.dtype("float32")}
    result = restore_object_strings(frame, schema)
    assert result["symbol"].dtype == np.dtype("O")
    assert result["symbol"].iloc[0] == "SPX"
    assert pd.isna(result["symbol"].iloc[1])
    assert isinstance(frame["symbol"].dtype, pd.StringDtype)
    with pytest.raises(ValueError, match="value"):
        verify_schema(result, schema)
    assert restore_object_strings(result, schema) is result
