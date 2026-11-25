# Working with Polynomials

ComboLink represents the Kauffman bracket and Jones polynomial with its
framework-independent `Polynomial` class. It is a sparse Laurent polynomial
with integer coefficients: only nonzero terms are stored, and exponents may
be negative.

This page covers both the polynomial values returned by link functions and
the public `Polynomial` API for constructing and manipulating polynomial
objects directly.

## Read a polynomial returned by ComboLink

The bracket is expressed in `A`; the Jones polynomial is expressed in `t`.
Both functions return `Polynomial` objects rather than formatted strings:

```python
import combolink as cl

trefoil = cl.knot(3, 1)
bracket = cl.kauffman_bracket(trefoil)
jones = cl.jones(trefoil)

print(bracket.var("A"))
print(jones.var("t"))
```

`.var(...)` accepts one name for each variable and formats the result as a
string. Exponents are written with a caret, including negative exponents such
as `A^-7`. For the trefoil, the bracket can be checked directly against a
constructed polynomial:

```python
expected = cl.Polynomial({5: -1, -3: -1, -7: 1})
assert bracket == expected
assert bracket.coefficients[(-7,)] == 1
```

The scalar exponent keys in the constructor are shorthand for one-variable
terms. Internally, the exponents are normalized to one-item tuples.

## Construct a polynomial

Pass a mapping from exponents to integer coefficients. Scalar exponent keys
create a one-variable polynomial:

```python
p = cl.Polynomial({-2: 3, 0: 1, 4: -1})
assert p.var("A") == "3A^-2 + 1 - A^4"
```

For multiple variables, use tuples with one exponent per variable:

```python
q = cl.Polynomial({
    (1, 0): 2,
    (0, 1): -1,
    (-1, 2): 3,
})

print(q.var("x", "y"))  # 3x^-1y^2 - y + 2x
```

Each term must have the same number of exponents. A mismatch raises
`TypeError`. Terms with a zero coefficient are omitted from storage.

The number of variables is determined by the exponent tuple on the first
term. For an empty mapping, it defaults to zero unless `fallback_n_vars` is
provided:

```python
zero_univariate = cl.Polynomial({}, fallback_n_vars=1)
assert zero_univariate.var("A") == ""
```

For common zero and constant-one values, use the named constructors:

```python
zero = cl.Polynomial.zero()       # one-variable zero
one = cl.Polynomial.one()         # one-variable constant 1
two_variable_zero = cl.Polynomial.zero(n_vars=2)
two_variable_one = cl.Polynomial.one(n_vars=2)

assert zero.var("A") == ""
assert one.var("A") == "1"
assert two_variable_one.var("x", "y") == "1"
```

## Inspect and format terms

`coefficients` maps exponent tuples to coefficients. In one variable, a key
such as `(3,)` represents the coefficient of the third power. In two
variables, `(2, -1)` is the coefficient of `x^2 y^-1`:

```python
p = cl.Polynomial({(2, -1): 4, (0, 0): -2})
assert p.coefficients[(2, -1)] == 4
assert p.var("x", "y") == "- 2 + 4x^2y^-1"
```

Terms are formatted in ascending order of their exponent tuples, not the
descending order sometimes used in printed algebra. The formatter omits a
coefficient of `1` on nonconstant terms and omits variables whose exponent is
zero. It requires exactly one name per variable; an incorrect number raises
`ValueError`.

For one-variable polynomials, `repr()` uses `_` as the variable name. Use
`.var("x", "y", ...)` to control the variable names explicitly.

## Evaluate a polynomial

Call the polynomial with one numeric value for each variable:

```python
p = cl.Polynomial({-1: 1, 1: 1})  # A^-1 + A
value = p(2)
assert value == 2.5
```

For a multivariate polynomial, values follow the same order as the exponents
in the keys:

```python
q = cl.Polynomial({(1, 1): 1, (0, 0): 2})  # xy + 2
assert q(3, 4) == 14
```

Passing the wrong number of values raises `ValueError`. Evaluation returns a
numeric value; it does not substitute variable names into a symbolic
expression.

## Add, multiply, and raise to powers

`+` adds polynomials and combines coefficients of matching terms. `*`
multiplies them by adding exponents and multiplying coefficients. Both
operations require the same number of variables:

```python
x_plus_one = cl.Polynomial({1: 1, 0: 1})
x_minus_one = cl.Polynomial({1: 1, 0: -1})

difference_of_squares = x_plus_one * x_minus_one
assert difference_of_squares.var("x") == "- 1 + x^2"

sum_poly = x_plus_one + x_minus_one
assert sum_poly.var("x") == "2x"
```

`**` raises a polynomial to a non-negative integer power. Power zero returns
the constant one with the same number of variables; a negative power raises
`ValueError`.

```python
square = x_plus_one**2
assert square.var("x") == "1 + 2x + x^2"
assert (x_plus_one**0).var("x") == "1"
```

The class implements polynomial-plus-polynomial addition,
polynomial-times-polynomial multiplication, and non-negative integer powers.
It does not overload scalar arithmetic or provide symbolic division. To add a
constant, represent it as a polynomial, for example
`cl.Polynomial({(0,): 2})` for the one-variable constant 2.

## Compare polynomial values

Polynomials compare equal when both their stored coefficients and variable
counts match:

```python
assert cl.Polynomial({1: 1, 0: 1}) == cl.Polynomial({0: 1, 1: 1})
assert cl.Polynomial.zero() != cl.Polynomial.zero(n_vars=2)
```

This compares algebraic expressions, not diagrams. An invariant polynomial
can distinguish some diagrams, but equality of one invariant alone does not
prove that two diagrams represent the same knot or link.

## Link polynomials and Reidemeister moves

`kauffman_bracket(diagram)` computes the Kauffman bracket. It is unchanged by
Type II and Type III moves, but a Type I move changes it by a normalization
factor. `jones(diagram)` applies writhe normalization and returns the Jones
polynomial, which is invariant under Reidemeister moves.

The bracket implementation considers smoothing choices at all crossings.
Its state count grows exponentially with the number of crossings, so use it
with that cost in mind for large diagrams.

## Related pages

- [Properties and notation](properties.md)
- [Diagram operations](operations.md)
- [Documentation hub](guide.md)
