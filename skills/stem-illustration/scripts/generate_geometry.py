"""严格几何证明图生成器（基于 matplotlib）。

用于绘制需要数学严格性的几何证明图（如 Garfield 1876 勾股定理证明、
其他欧几里得几何证明、坐标变换等），避免 AI 生图无法保证几何精度的缺陷。

设计原则：
- 用 matplotlib.patches.Polygon 按真实坐标绘制多边形
- 用 plt.annotate 标注边长、角度
- 用 mlines.Line2D 绘制直线段
- 每个三角形 / 多边形的顶点和边长都用 print 验证
- 输出高分辨率 PNG，可直接用于教材/论文

用法：
    python generate_geometry.py garfield
    python generate_geometry.py garfield --a 5 --b 12 --c 13
    python generate_geometry.py --list  # 列出可用证明
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

# 中文字体配置（matplotlib 默认字体不支持中文）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11


# ============================================================================
# Garfield 1876 勾股定理证明
# ============================================================================
# 严格几何构造（已数学验证）：
#   设直角三角形腿 a, b, 斜边 c, 其中 a^2 + b^2 = c^2
#   构造直角梯形 ABCD：
#     A = (0, a+b), B = (a, a+b), C = (b, 0), D = (0, 0)
#   - AB = a  (上底)
#   - CD = b  (下底)
#   - AD = a+b (左侧高, 垂直)
#   - BC = c*sqrt(2) (右侧斜边, 是内部等腰直角三角形的斜边)
#
#   内部 3 个三角形：
#     T1 = ABX, X = (0, a)
#       直角在 A, 腿 AB=a, AX=b, 斜边 BX=c
#     T2 = DCY, Y = (0, a)  -- 注意 Y 与 X 重合
#       直角在 D, 腿 DC=b, DY=a, 斜边 CY=c
#     T3 = BXC  (内部等腰直角三角形)
#       BX = c, XC = c, BC = c*sqrt(2)
#       腰与腰之间的夹角 = 90°
#
#   面积等式：
#     梯形面积 = T1 + T2 + T3
#     1/2 (a+b)^2 = 2 * 1/2 ab + 1/2 c^2
#     a^2 + 2ab + b^2 = 2ab + c^2
#     a^2 + b^2 = c^2
# ============================================================================


def _right_angle_marker(ax, vertex, dx, dy, size=0.25):
    """在指定顶点绘制直角标记（小方块）。

    dx, dy: 沿两条边的方向向量（分量）。
    """
    vx, vy = float(vertex[0]), float(vertex[1])
    dx, dy = float(dx[0] if isinstance(dx, (tuple, list)) else dx), float(dy[0] if isinstance(dy, (tuple, list)) else dy)
    # 方块的 4 个顶点：从 vertex 出发，沿 dx 走 size，再沿 dy 走 size，再回到 vertex
    p1 = (vx, vy)
    p2 = (vx + dx * size, vy + dy * size)
    p3 = (vx + dx * size - dy * size, vy + dy * size + dx * size)
    p4 = (vx - dy * size, vy + dx * size)
    poly = Polygon([p1, p2, p3, p4], closed=True, fill=False, edgecolor="black", linewidth=1.0)
    ax.add_patch(poly)


def garfield_proof(a: float = 3, b: float = 4, c: float | None = None, output: str | None = None):
    """绘制 Garfield 1876 勾股定理证明图。

    Args:
        a, b: 直角三角形的两条直角边
        c: 斜边（默认 sqrt(a^2+b^2)）
        output: 输出 PNG 路径
    """
    if c is None:
        c = math.sqrt(a * a + b * b)

    # 严格验证：c^2 = a^2 + b^2
    assert abs(c * c - (a * a + b * b)) < 1e-9, f"输入不满足勾股定理: a={a}, b={b}, c={c}"

    print(f"[verify] a={a}, b={b}, c={c:.6f}")
    print(f"[verify] a^2 + b^2 = {a*a + b*b:.6f}, c^2 = {c*c:.6f}")

    # 坐标
    A = (0, a + b)
    B = (a, a + b)
    C = (b, 0)
    D = (0, 0)
    X = (0, a)  # = Y
    Y = (0, a)

    # 验证关键边长
    AB = math.dist(A, B)
    CD = math.dist(C, D)
    AD = math.dist(A, D)
    BC = math.dist(B, C)
    BX = math.dist(B, X)
    CY = math.dist(C, Y)
    XC = math.dist(X, C)

    print(f"[verify] AB (上底) = {AB:.4f}, should be a={a}")
    print(f"[verify] CD (下底) = {CD:.4f}, should be b={b}")
    print(f"[verify] AD (左侧高) = {AD:.4f}, should be a+b={a+b}")
    print(f"[verify] BC (右侧斜边) = {BC:.4f}, should be c*sqrt(2)={c*math.sqrt(2):.4f}")
    print(f"[verify] BX = {BX:.4f}, should be c={c:.4f}")
    print(f"[verify] CY = {CY:.4f}, should be c={c:.4f}")
    print(f"[verify] XC = {XC:.4f}, should be c={c:.4f}")
    print(f"[verify] X == Y: {X == Y}")

    # 验证三角形面积
    def triangle_area(p1, p2, p3):
        return abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (p2[1] - p1[1])) / 2

    T1 = triangle_area(A, B, X)
    T2 = triangle_area(D, C, Y)
    T3 = triangle_area(B, X, C)
    trap = triangle_area(A, B, C) + triangle_area(A, C, D)
    print(f"[verify] T1 面积 = {T1:.4f}, should be a*b/2={a*b/2}")
    print(f"[verify] T2 面积 = {T2:.4f}, should be a*b/2={a*b/2}")
    print(f"[verify] T3 面积 = {T3:.4f}, should be c^2/2={c*c/2}")
    print(f"[verify] 梯形面积 = {trap:.4f}, should be (a+b)^2/2={(a+b)**2/2}")
    print(f"[verify] T1+T2+T3 = {T1+T2+T3:.4f}, 梯形面积 = {trap:.4f}, "
          f"diff = {abs(T1+T2+T3-trap):.6e}")

    # 用 mathtext 渲染 c^2 等上标（避免 SimHei 不支持 U+00B2 的问题）
    plt.rcParams["text.usetex"] = False
    import matplotlib
    matplotlib.rcParams["mathtext.default"] = "regular"
    SQ = "²"  # 备用: $c^2$
    # 用 chr(0x00B2) 在某些系统能渲染
    # 最稳的方式：使用 mathtext 语法
    c2 = r"$c^2$"  # matplotlib mathtext
    c2over2 = r"$\frac{c^2}{2}$"
    abover2 = r"$\frac{ab}{2}$"

    # ============ 绘图 ============
    fig = plt.figure(figsize=(14, 16))
    gs = fig.add_gridspec(3, 1, height_ratios=[5, 0.4, 4], hspace=0.3)
    ax_geo = fig.add_subplot(gs[0])
    ax_sep = fig.add_subplot(gs[1])
    ax_alg = fig.add_subplot(gs[2])

    # --- 几何构造图 ---
    ax_geo.set_aspect("equal")
    ax_geo.set_xlim(-2, max(b, c) + 2)
    ax_geo.set_ylim(-2, a + b + 2)
    ax_geo.axis("off")

    # 颜色
    COLOR_T1 = "#bfdbfe"  # 浅蓝
    COLOR_T2 = "#bfdbfe"
    COLOR_T3 = "#fef3c7"  # 浅黄
    COLOR_TRAP = "#ffffff"
    COLOR_EDGE = "#1f2937"  # 深灰

    # 绘制梯形 ABCD（先画外框）
    trap_outer = Polygon([A, B, C, D], closed=True, fill=False, edgecolor=COLOR_EDGE, linewidth=2.0)
    ax_geo.add_patch(trap_outer)

    # 绘制 3 个三角形（带颜色填充）
    t1_poly = Polygon([A, B, X], closed=True, facecolor=COLOR_T1, edgecolor=COLOR_EDGE, linewidth=1.5, alpha=0.9)
    t2_poly = Polygon([D, C, Y], closed=True, facecolor=COLOR_T2, edgecolor=COLOR_EDGE, linewidth=1.5, alpha=0.9)
    t3_poly = Polygon([B, X, C], closed=True, facecolor=COLOR_T3, edgecolor=COLOR_EDGE, linewidth=1.5, alpha=0.9)
    ax_geo.add_patch(t1_poly)
    ax_geo.add_patch(t2_poly)
    ax_geo.add_patch(t3_poly)

    # 直角标记
    _right_angle_marker(ax_geo, A, (1, 0), (0, -1), size=0.5)  # 直角在 A（指向内部）
    _right_angle_marker(ax_geo, D, (1, 0), (0, 1), size=0.5)    # 直角在 D
    _right_angle_marker(ax_geo, B, (-1, 0), (0, -1), size=0.4)  # 提示 B 处的角度（直角在 A, B 处不一定是直角）
    _right_angle_marker(ax_geo, C, (-1, 0), (0, 1), size=0.5)   # 提示 C 处

    # 标注顶点
    label_offset = 0.3
    ax_geo.annotate("A", A, textcoords="offset points", xytext=(-15, 5), fontsize=14, fontweight="bold")
    ax_geo.annotate("B", B, textcoords="offset points", xytext=(5, 5), fontsize=14, fontweight="bold")
    ax_geo.annotate("C", C, textcoords="offset points", xytext=(8, -15), fontsize=14, fontweight="bold")
    ax_geo.annotate("D", D, textcoords="offset points", xytext=(-15, -15), fontsize=14, fontweight="bold")
    ax_geo.annotate("X=Y", X, textcoords="offset points", xytext=(-30, -5), fontsize=12, fontweight="bold", color="#dc2626")

    # 边长标注
    # AB (上底)
    mid_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
    ax_geo.annotate(f"a = {a}", mid_AB, textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=13, color="#1e40af", fontweight="bold")
    # CD (下底)
    mid_CD = ((C[0] + D[0]) / 2, (C[1] + D[1]) / 2)
    ax_geo.annotate(f"b = {b}", mid_CD, textcoords="offset points", xytext=(0, -18),
                    ha="center", fontsize=13, color="#1e40af", fontweight="bold")
    # AD (左侧高)
    mid_AD = ((A[0] + D[0]) / 2, (A[1] + D[1]) / 2)
    ax_geo.annotate(f"a+b = {a+b}", mid_AD, textcoords="offset points", xytext=(-30, 0),
                    ha="center", fontsize=13, color="#1e40af", fontweight="bold")
    # BC (右侧斜边)
    mid_BC = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)
    ax_geo.annotate(f"c√2 = {c*math.sqrt(2):.3f}", mid_BC, textcoords="offset points", xytext=(20, 0),
                    ha="center", fontsize=12, color="#6b7280", style="italic")
    # BX (T1 斜边)
    mid_BX = ((B[0] + X[0]) / 2, (B[1] + X[1]) / 2)
    ax_geo.annotate(f"c = {c:.3f}", mid_BX, textcoords="offset points", xytext=(-25, 5),
                    ha="center", fontsize=12, color="#dc2626", fontweight="bold")
    # CY (T2 斜边)
    mid_CY = ((C[0] + Y[0]) / 2, (C[1] + Y[1]) / 2)
    ax_geo.annotate(f"c = {c:.3f}", mid_CY, textcoords="offset points", xytext=(5, -5),
                    ha="center", fontsize=12, color="#dc2626", fontweight="bold")
    # XC (T3 一条腰)
    mid_XC = ((X[0] + C[0]) / 2, (X[1] + C[1]) / 2)
    ax_geo.annotate(f"c = {c:.3f}", mid_XC, textcoords="offset points", xytext=(-10, 8),
                    ha="center", fontsize=12, color="#dc2626", fontweight="bold")

    # 三角形内标注
    ax_geo.annotate("T1", ((A[0]+B[0]+X[0])/3, (A[1]+B[1]+X[1])/3),
                    ha="center", fontsize=11, color="#1e40af", fontweight="bold")
    ax_geo.annotate("T2", ((D[0]+C[0]+Y[0])/3, (D[1]+C[1]+Y[1])/3),
                    ha="center", fontsize=11, color="#1e40af", fontweight="bold")
    ax_geo.text((B[0]+X[0]+C[0])/3 + 0.3, (B[1]+X[1]+C[1])/3, r"T3" + "\n" + r"($\frac{c^2}{2}$)",
                ha="center", va="center", fontsize=11, color="#92400e", fontweight="bold")

    # 标题
    ax_geo.set_title(r"Garfield's Proof of the Pythagorean Theorem — Geometric Construction" + "\n"
                     r"加菲尔德总统的勾股定理证明 (James A. Garfield, 20th US President, 1876)" + "\n"
                     rf"$a = {a},\ b = {b},\ c = \sqrt{{a^2 + b^2}} = {c:.4f}$",
                     fontsize=13, fontweight="bold", pad=15)

    # 图例
    legend_elements = [
        mpatches.Patch(facecolor=COLOR_T1, edgecolor=COLOR_EDGE, label=rf"$T_1 = T_2 = \frac{{ab}}{{2}} = {a*b/2}$  (两个全等直角三角形)"),
        mpatches.Patch(facecolor=COLOR_T3, edgecolor=COLOR_EDGE, label=rf"$T_3 = \frac{{c^2}}{{2}} = {c*c/2:.4f}$  (内部等腰直角三角形)"),
    ]
    ax_geo.legend(handles=legend_elements, loc="upper right", fontsize=10, framealpha=0.95)

    # --- 分隔线 ---
    ax_sep.axis("off")
    ax_sep.axhline(y=0.5, color="#6b7280", linewidth=0.8, linestyle="--")

    # --- 代数推导 ---
    ax_alg.axis("off")
    ax_alg.set_xlim(0, 10)
    ax_alg.set_ylim(0, 10)

    eqs = [
        (1, "梯形面积（按梯形公式）", r"= $\frac{1}{2}$ (a + b) (a + b)"),
        (2, "化简", r"= $\frac{1}{2}$ (a + b)$^2$"),
        (3, "展开", r"= $\frac{1}{2}$ (a$^2$ + 2ab + b$^2$)"),
        (4, "按分割求和（2 个 T1/T2 + 1 个 T3）", r"= 2 $\cdot$ $\frac{1}{2}$ab + $\frac{1}{2}$c$^2$ = ab + $\frac{1}{2}$c$^2$"),
        (5, "令两式相等", r"$\frac{1}{2}$ (a$^2$ + 2ab + b$^2$) = ab + $\frac{1}{2}$c$^2$"),
        (6, "两边同乘以 2", r"a$^2$ + 2ab + b$^2$ = 2ab + c$^2$"),
        (7, "两边同减去 2ab", r"a$^2$ + b$^2$ = c$^2$"),
    ]

    y_start = 9.0
    y_step = 1.0
    for i, (n, label, formula) in enumerate(eqs):
        y = y_start - i * y_step
        # 步骤编号
        ax_alg.text(0.3, y, f"({n})", fontsize=13, fontweight="bold", color="#1e40af")
        # 步骤说明
        ax_alg.text(1.0, y, label, fontsize=11, color="#374151")
        # 公式
        ax_alg.text(4.5, y, formula, fontsize=12, color="#111827")

    # 最终结论（双下划线）
    ax_alg.text(2.5, 0.6, r"$\therefore\ a^2 + b^2 = c^2$    (Q.E.D.)",
                fontsize=18, fontweight="bold", color="#1e40af",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#fef3c7", edgecolor="#92400e", linewidth=2))

    # 保存
    if output is None:
        output = f"d:/stem-skill/generated-images/garfield_proof_a{a}_b{b}.png"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"\n[save] {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description="严格几何证明图生成器")
    sub = parser.add_subparsers(dest="cmd")

    # garfield 子命令
    p_garfield = sub.add_parser("garfield", help="Garfield 1876 勾股定理证明")
    p_garfield.add_argument("--a", type=float, default=3, help="直角边 a")
    p_garfield.add_argument("--b", type=float, default=4, help="直角边 b")
    p_garfield.add_argument("--c", type=float, default=None, help="斜边 c（默认 sqrt(a²+b²)）")
    p_garfield.add_argument("--output", type=str, default=None, help="输出 PNG 路径")

    # list 子命令
    sub.add_parser("--list", help="列出可用证明")

    args = parser.parse_args()

    if args.cmd == "garfield":
        out = garfield_proof(a=args.a, b=args.b, c=args.c, output=args.output)
        print(f"\n[done] 验证完成且已保存: {out}")
    elif args.cmd == "--list":
        print("可用证明：")
        print("  garfield  - Garfield 1876 勾股定理证明 (by James A. Garfield, US President)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
