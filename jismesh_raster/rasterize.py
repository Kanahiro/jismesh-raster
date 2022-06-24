import argparse

import pandas as pd
import jismesh.utils as ju
from PIL import Image


MESH_SCHEMES = {
    "80km": {
        "size": (1, 2 / 3),
        "xy_indexing": (lambda meshcode: meshcode[2:4], lambda meshcode: meshcode[0:2]),
        "concat": lambda x_idx, y_idx: y_idx + x_idx,
    },
    "10km": {
        "size": (1 / 8, 1 / 12),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4] + meshcode[5],
            lambda meshcode: meshcode[0:2] + meshcode[4],
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2] + x_idx[0:2] + y_idx[2] + x_idx[2],
    },
    "1km": {
        "size": (1 / 80, 1 / 120),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7],
            lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6],
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + y_idx[3]
        + x_idx[3],
    },
    "500m": {
        "size": (1 / 160, 1 / 240),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4]
            + meshcode[5]
            + meshcode[7]  # 1km
            + str(int(meshcode[8]) - 1 % 2),
            lambda meshcode: meshcode[0:2]
            + meshcode[4]
            + meshcode[6]
            + str(-(-int(meshcode[8]) // 2)),
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + y_idx[3]
        + x_idx[3]
        + str(int(x_idx[4]) + 2 * (int(y_idx[4]) - 1)),
    },
    "250m": {
        "size": (1 / 320, 1 / 480),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4]
            + meshcode[5]
            + meshcode[7]  # 1km
            + str((int(meshcode[8]) - 1) % 2)
            + str((int(meshcode[9]) - 1) % 2),
            lambda meshcode: meshcode[0:2]
            + meshcode[4]
            + meshcode[6]
            + str(-(-int(meshcode[8]) // 2))
            + str(-(-int(meshcode[9]) // 2)),
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + y_idx[3]
        + x_idx[3]
        + str(int(x_idx[4]) + 2 * (int(y_idx[4]) - 1))
        + str(int(x_idx[5]) + 2 * (int(y_idx[5]) - 1)),
    },
    "125m": {
        "size": (1 / 640, 1 / 960),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4]
            + meshcode[5]
            + meshcode[7]
            + str((int(meshcode[8]) - 1) % 2)
            + str((int(meshcode[9]) - 1) % 2)
            + str((int(meshcode[10]) - 1) % 2),
            lambda meshcode: meshcode[0:2]
            + meshcode[4]
            + meshcode[6]
            + str(-(-int(meshcode[8]) // 2))
            + str(-(-int(meshcode[9]) // 2))
            + str(-(-int(meshcode[10]) // 2)),
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + y_idx[3]
        + x_idx[3]
        + str(int(x_idx[4]) + 2 * (int(y_idx[4]) - 1))
        + str(int(x_idx[5]) + 2 * (int(y_idx[5]) - 1))
        + str(int(x_idx[6]) + 2 * (int(y_idx[6]) - 1)),
    },
    "5km": {
        "size": (1 / 16, 1 / 24),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4]
            + meshcode[5]
            + str((int(meshcode[6]) - 1) % 2 + 1),
            lambda meshcode: meshcode[0:2]
            + meshcode[4]
            + str(-(-int(meshcode[6]) // 2)),
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + str(2 * int(y_idx[3]) + int(x_idx[3]) - 2),
    },
    "2km": {
        "size": (1 / 40, 1 / 60),
        "xy_indexing": (
            lambda meshcode: meshcode[2:4] + meshcode[5] + str(int(meshcode[7]) // 2),
            lambda meshcode: meshcode[0:2] + meshcode[4] + str(int(meshcode[6]) // 2),
        ),
        "concat": lambda x_idx, y_idx: y_idx[0:2]
        + x_idx[0:2]
        + y_idx[2]
        + x_idx[2]
        + str(int(y_idx[3]) * 2)
        + str(int(x_idx[3]) * 2)
        + "5",
    },
}


def get_meshname(meshcode: str) -> str:
    if len(meshcode) == 4:  # 80km
        return "80km"
    elif len(meshcode) == 6:  # 10km
        return "10km"
    elif len(meshcode) == 7:  # 5km
        return "5km"
    elif len(meshcode) == 8:  # 1km
        return "1km"
    elif len(meshcode) == 9:
        if meshcode[-1] == "5":
            return "2km"
        else:
            return "500m"
    elif len(meshcode) == 10:  # 250m
        return "250m"
    elif len(meshcode) == 11:  # 125m
        return "125m"
    raise Exception("無効なメッシュコードです")


def make_all_indexes(meshname: str, min_index: str, max_index: str) -> list:
    def filtering(code: str):
        if len(code) > 2 and int(code[2]) > 7:
            return False
        if meshname == "5km" and code[3] != "1" and code[3] != "2":
            return False
        elif meshname == "2km" and int(code[3]) > 4:
            return False
        else:
            if len(code) > 4 and code[4] != "1" and code[4] != "2":
                return False
            if len(code) > 5 and code[5] != "1" and code[5] != "2":
                return False
            if len(code) > 6 and code[6] != "1" and code[6] != "2":
                return False
        return True

    return list(
        filter(
            filtering, [str(i + 1) for i in range(int(min_index), int(max_index) - 1)]
        )
    )


def get_args():
    parser = argparse.ArgumentParser(description="地域メッシュ単位のデータからラスターデータを生成するスクリプト")
    parser.add_argument("csvfile", help="読み込むCSVファイル")
    parser.add_argument("output", help="データの保存先絶対パス")
    parser.add_argument("--meshcol", help="メッシュコードの列番号を左から数えた番号で指定、デフォルトは0")
    parser.add_argument("--valuecol", help="値の列番号を左から数えた番号で指定、デフォルトは1")
    parser.add_argument("--method", help="集計方法、mean, median, min, max, stddev, sum")
    parser.add_argument("--nodata", help="データがないメッシュにセットする値、デフォルトはnan")
    parser.add_argument("--noheader", help="CSVにヘッダーが無い場合に入力", action="store_true")
    return parser.parse_args()


def rasterize(
    csvfile: str,
    output: str,
    meshcol=0,
    valuecol=1,
    aggr_method=None,
    nodata=None,
    noheader=False,
):

    csv_df = pd.read_csv(csvfile, header=None) if noheader else pd.read_csv(csvfile)
    meshcode_colname = csv_df.columns[meshcol]
    value_colname = csv_df.columns[valuecol]
    csv_df = csv_df[[meshcode_colname, value_colname]].astype(
        {meshcode_colname: str, value_colname: float}
    )

    if aggr_method == "mean":
        csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
    elif aggr_method == "median":
        csv_df = csv_df.groupby(meshcode_colname).median().reset_index()
    elif aggr_method == "min":
        csv_df = csv_df.groupby(meshcode_colname).min().reset_index()
    elif aggr_method == "max":
        csv_df = csv_df.groupby(meshcode_colname).max().reset_index()
    elif aggr_method == "stddev":
        csv_df = csv_df.groupby(meshcode_colname).std().reset_index()
    elif aggr_method == "sum":
        csv_df = csv_df.groupby(meshcode_colname).sum().reset_index()
    else:
        if aggr_method is None:
            if len(csv_df) != len(csv_df[meshcode_colname].unique()):
                raise Exception("CSVの複数行に同一のメッシュコードが存在する場合、集計方法を指定してください")
        else:
            raise Exception("methodの指定が不正です、正しいmethod名を入力してください")

    meshname = get_meshname(csv_df[meshcode_colname].iloc[0])
    meshscheme = MESH_SCHEMES[meshname]
    print(meshname, meshscheme)
    x_indexing, y_indexing = meshscheme["xy_indexing"]

    csv_df["x_index"] = csv_df[meshcode_colname].map(x_indexing)
    csv_df["y_index"] = csv_df[meshcode_colname].map(y_indexing)

    min_x_index = csv_df["x_index"].min()
    max_x_index = csv_df["x_index"].max()
    min_y_index = csv_df["y_index"].min()
    max_y_index = csv_df["y_index"].max()

    origin_meshcode = meshscheme["concat"](min_x_index, max_y_index)
    origin_latlng = ju.to_meshpoint(origin_meshcode, 0.5, 0.5)
    print(origin_meshcode, origin_latlng, csv_df)

    # データには存在しないが画像範囲内となるメッシュのリストを生成
    x_indexes = csv_df["x_index"].values
    y_indexes = csv_df["y_index"].values
    append_x_indexes = list(
        filter(
            lambda code: code not in x_indexes,
            make_all_indexes(meshname, min_x_index, max_x_index),
        )
    )
    append_y_indexes = list(
        filter(
            lambda code: code not in y_indexes,
            make_all_indexes(meshname, min_y_index, max_y_index),
        )
    )

    # 画像をつくるための2次元配列
    matrix2d_df = csv_df[["x_index", "y_index", value_colname]].pivot(
        values=value_colname, index="y_index", columns="x_index"
    )

    # 不足メッシュを内挿
    if len(append_x_indexes) > 0:
        matrix2d_df = matrix2d_df.join(pd.DataFrame(index=[], columns=append_x_indexes))
    if len(append_y_indexes) > 0:
        matrix2d_df = pd.concat(
            [
                matrix2d_df,
                pd.DataFrame(index=append_y_indexes, columns=matrix2d_df.columns),
            ]
        )
    # メッシュの地図上の配置と同じ2次元配列に並べる
    matrix2d_df = matrix2d_df.sort_index(ascending=False)
    matrix2d_df = matrix2d_df.sort_index(axis=1)
    if nodata is not None:
        # 値が指定されているならNaN埋め
        matrix2d_df = matrix2d_df.fillna(nodata)
    print(matrix2d_df)
    image = Image.fromarray(matrix2d_df.values)
    image.save(output)

    worldfile_path = output.split(".")[0] + ".tfw"
    with open(worldfile_path, mode="w", encoding="utf-8") as f:
        f.write(
            f"""\
{meshscheme["size"][0]}
0
0
{-meshscheme["size"][1]}
{origin_latlng[1]}
{origin_latlng[0]}
"""
        )


def main():
    args = get_args()
    rasterize(
        **{
            "csvfile": args.csvfile,
            "output": args.output,
            "meshcol": 0 if args.meshcol is None else int(args.meshcol),
            "valuecol": 1 if args.valuecol is None else int(args.valuecol),
            "aggr_method": args.method,
            "nodata": -9999.0 if args.nodata is None else float(args.nodata),
            "noheader": args.noheader,
        }
    )


if __name__ == "__main__":
    main()
