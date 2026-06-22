import pandas as pd


def interpolate_trajectory(raw_trajectory):
    columns = ["frame", "cx", "cy", "w", "h", "conf"]

    if not raw_trajectory:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(raw_trajectory, columns=columns)

    df["frame"] = pd.to_numeric(df["frame"], errors="coerce").astype("Int64")

    for col in ["cx", "cy", "w", "h", "conf"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["cx"] = df["cx"].interpolate(method="linear")
    df["cy"] = df["cy"].interpolate(method="linear")

    df["w"] = df["w"].interpolate(method="linear").bfill().ffill()
    df["h"] = df["h"].interpolate(method="linear").bfill().ffill()

    # conf가 0.0이면 실제 탐지가 아니라 보간된 좌표라는 의미로 사용
    df["conf"] = df["conf"].fillna(0.0)

    return df