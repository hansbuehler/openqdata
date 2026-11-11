from __future__ import annotations

import cvxpy as cp
import cvxpy.atoms.affine.sum as cvxpy_sum

from openqdata.utils.cvxpy import patch_cvxpy_sum_shape_from_args


def test_patch_cvxpy_sum_shape_from_args_is_idempotent() -> None:
    patch_cvxpy_sum_shape_from_args()
    patched = cvxpy_sum.Sum.shape_from_args
    try:
        assert getattr(patched, "_openqdata_cvxpy_sum_shape_patch", False)
        assert patch_cvxpy_sum_shape_from_args() is False

        original = getattr(patched, "_openqdata_original")
        cvxpy_sum.Sum.shape_from_args = original
        assert patch_cvxpy_sum_shape_from_args() is True
        assert patch_cvxpy_sum_shape_from_args() is False

        assert getattr(cvxpy_sum.Sum.shape_from_args, "_openqdata_cvxpy_sum_shape_patch", False)

        expr = cp.sum(cp.Variable((2, 3)), axis=0)
        assert expr.shape == (3,)
    finally:
        cvxpy_sum.Sum.shape_from_args = patched