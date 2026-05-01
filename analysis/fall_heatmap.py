import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path

# ── 한글 폰트 설정 ──────────────────────────────────────────
def set_korean_font():
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            fm.fontManager.addfont(path)
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            return
    plt.rcParams["font.family"] = "DejaVu Sans"

set_korean_font()
plt.rcParams["axes.unicode_minus"] = False

# ── 데이터 로드 ──────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_DIR / "fall_incidents.csv")
df["발생일시"] = pd.to_datetime(df["발생일시"])
df["월"] = df["발생일시"].dt.month

# 시간대 순서 정의
TIME_ORDER = ["00-06", "06-12", "12-18", "18-24"]
WARD_ORDER = sorted(df["병동"].unique())

# ── 공통 히트맵 함수 ─────────────────────────────────────────
def draw_heatmap(pivot, title, xlabel, ylabel, fname, fmt="d", cmap="YlOrRd"):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=fmt,
        cmap=cmap,
        linewidths=0.5,
        linecolor="white",
        ax=ax,
        cbar_kws={"label": "낙상 건수"},
    )
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    plt.tight_layout()
    out = OUTPUT_DIR / fname
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"저장: {out}")


# ══════════════════════════════════════════════════════════════
# 1. 병동 × 시간대  (메인 히트맵)
# ══════════════════════════════════════════════════════════════
pivot1 = (
    df.groupby(["병동", "발생시간대"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=WARD_ORDER, columns=TIME_ORDER, fill_value=0)
)
draw_heatmap(
    pivot1,
    "병동별 · 시간대별 낙상 발생 빈도",
    "발생 시간대",
    "병동",
    "heatmap_ward_time.png",
)

# ══════════════════════════════════════════════════════════════
# 2. 병동 × 발생장소
# ══════════════════════════════════════════════════════════════
PLACE_ORDER = ["병실침대", "병실바닥", "복도", "화장실", "샤워실", "휠체어이동중"]
pivot2 = (
    df.groupby(["병동", "발생장소"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=WARD_ORDER, columns=PLACE_ORDER, fill_value=0)
)
draw_heatmap(
    pivot2,
    "병동별 · 발생장소별 낙상 빈도",
    "발생 장소",
    "병동",
    "heatmap_ward_place.png",
    cmap="Blues",
)

# ══════════════════════════════════════════════════════════════
# 3. 병동 × 손상정도
# ══════════════════════════════════════════════════════════════
SEVERITY_ORDER = ["없음", "경미(타박)", "중등도(열상/염좌)", "중증(골절)"]
pivot3 = (
    df.groupby(["병동", "손상정도"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=WARD_ORDER, columns=SEVERITY_ORDER, fill_value=0)
)
draw_heatmap(
    pivot3,
    "병동별 · 손상정도별 낙상 빈도",
    "손상 정도",
    "병동",
    "heatmap_ward_severity.png",
    cmap="OrRd",
)

# ══════════════════════════════════════════════════════════════
# 4. 월 × 시간대  (시계열 패턴)
# ══════════════════════════════════════════════════════════════
pivot4 = (
    df.groupby(["월", "발생시간대"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=TIME_ORDER, fill_value=0)
    .sort_index()
)
pivot4.index = [f"{m}월" for m in pivot4.index]
draw_heatmap(
    pivot4,
    "월별 · 시간대별 낙상 발생 빈도",
    "발생 시간대",
    "월",
    "heatmap_month_time.png",
    cmap="PuBu",
)

print("\n히트맵 4종 생성 완료.")
