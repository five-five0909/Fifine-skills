# Problem: PISFM C/N Ratio Constraint Loss — Mathematical Properties

## Statement

Let $r_i = \frac{\mathrm{SOC}_i}{\mathrm{TN}_i + \epsilon}$ where $\mathrm{SOC}_i, \mathrm{TN}_i > 0$ and $\epsilon > 0$.

Define the C/N ratio constraint loss from the PISFM model:

$$\mathcal{L}_{cn} = \frac{1}{B} \sum_{i=1}^{B} \left[ \mathrm{ReLU}(r_i - 30)^2 + \mathrm{ReLU}(8 - r_i)^2 \right]$$

where $\mathrm{ReLU}(x) = \max(0, x)$.

Prove the following three properties:

1. **Non-negativity**: $\mathcal{L}_{cn} \geq 0$ for all valid inputs.
2. **Zero condition**: $\mathcal{L}_{cn} = 0$ if and only if $8 \leq r_i \leq 30$ for all $i \in \{1,\ldots,B\}$.
3. **Convexity**: The per-sample term $f(r) = \mathrm{ReLU}(r-30)^2 + \mathrm{ReLU}(8-r)^2$ is convex in $r \in \mathbb{R}$.

## Notes

- From PISFM (Physics-Informed Soil Feature Model) for soil organic carbon prediction.
- Bounds $[8,30]$ are the geochemically valid C/N range for forest soils (Cleveland & Liptzin 2007).
- $\mathrm{ReLU}(x)^2$ is a squared hinge loss / quadratic penalty.
