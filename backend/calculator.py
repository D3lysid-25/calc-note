"""
Engine de calcul pour notes de calcul.
Support : numérique, symbolique (SymPy), unités (Pint)
"""
import re
from typing import Any, Dict, Tuple
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
import pint

# Registry Pint global
ureg = pint.UnitRegistry()
ureg.default_format = "~P"  # pretty print

# Transformations pour parsing SymPy plus naturel
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _is_unit_expression(expr: str) -> bool:
    """Détecte si l'expression contient probablement des unités."""
    unit_keywords = [
        "m", "kg", "s", "a", "k", "mol", "cd", "n", "pa", "j", "w", "v", "ohm",
        "mm", "cm", "km", "g", "mg", "t", "min", "h", "day", "deg", "rad",
        "kn", "mpa", "gpa", "kpa", "bar", "psi", "lbf", "kip",
        "meter", "kilogram", "second", "newton", "pascal", "joule", "watt",
        "kn", "n", "mpa", "kpa",
    ]
    expr_lower = expr.lower()
    return any(re.search(rf"\b{re.escape(u)}\b", expr_lower) for u in unit_keywords)


def evaluate_expression(
    expression: str, context: Dict[str, Any] | None = None
) -> Tuple[bool, str, str, Dict[str, Any]]:
    """
    Évalue une expression.
    Retourne : (success, result_str, result_latex, updated_context)
    """
    if context is None:
        context = {}

    expression = expression.strip()
    if not expression:
        return False, "", "", context

    # Gestion des assignations : x = ...
    assign_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$", expression)
    var_name = None
    if assign_match:
        var_name = assign_match.group(1)
        expression = assign_match.group(2).strip()

    try:
        # ---------- Cas avec unités (Pint) ----------
        if _is_unit_expression(expression) or any(
            isinstance(v, pint.Quantity) for v in context.values()
        ):
            # On construit un namespace sûr pour eval
            local_ns = {"ureg": ureg, "Q_": ureg.Quantity}
            for k, v in context.items():
                local_ns[k] = v

            # Remplacement simple pour syntaxe plus naturelle
            # ex: 5*m → 5 * ureg.m
            def replace_units(match):
                num = match.group(1)
                unit = match.group(2)
                return f"({num} * ureg.{unit})"

            # Pattern basique : nombre + unité
            processed = re.sub(
                r"(\d+\.?\d*)\s*\*?\s*([a-zA-Zµ°]+(?:/[a-zA-Z0-9]+)?(?:\*\*[0-9]+)?)",
                replace_units,
                expression,
            )

            result = eval(processed, {"__builtins__": {}}, local_ns)

            if var_name:
                context[var_name] = result

            if isinstance(result, pint.Quantity):
                result_str = f"{result:~P}"
                # Approximation LaTeX simple
                result_latex = str(result).replace("**", "^")
            else:
                result_str = str(result)
                result_latex = result_str

            return True, result_str, result_latex, context

        # ---------- Cas symbolique / numérique (SymPy) ----------
        local_dict = {}
        for k, v in context.items():
            if isinstance(v, (int, float, sp.Expr)):
                local_dict[k] = v
            elif isinstance(v, str):
                try:
                    local_dict[k] = sp.sympify(v)
                except Exception:
                    pass

        # Parsing
        expr = parse_expr(
            expression,
            local_dict=local_dict,
            transformations=TRANSFORMATIONS,
            evaluate=False,
        )

        # Évaluation
        result = expr.doit() if hasattr(expr, "doit") else expr
        result = sp.simplify(result)

        # Si purement numérique → float
        if result.is_number:
            try:
                result = float(result)
            except Exception:
                pass

        result_str = str(result)
        result_latex = sp.latex(result)

        if var_name:
            context[var_name] = result

        return True, result_str, result_latex, context

    except Exception as e:
        return False, "", "", context | {"__error__": str(e)}
