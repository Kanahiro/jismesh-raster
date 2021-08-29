import argparse

import pandas as pd
import jismesh.utils as ju
from PIL import Image


def make_meshinfo(meshcode: str) -> dict:
    if len(meshcode) == 4:
        return {
            "num": 1,
            "size": (1, 2/3)
        }
    elif len(meshcode) == 6:
        return {
            "num": 2,
            "size": (1/8, 1/12)
        }
    elif len(meshcode) == 8:
        return {
            "num": 3,
            "size": (1/80, 1/120)
        }
    raise Exception("無効なメッシュコードです")


def make_xy_indexing_methods(meshnum: int) -> tuple:
    if meshnum == 1:
        return (lambda meshcode: meshcode[2:4], lambda meshcode: meshcode[0:2])
    elif meshnum == 2:
        return (lambda meshcode: meshcode[2:4] + meshcode[5], lambda meshcode: meshcode[0:2] + meshcode[4])
    elif meshnum == 3:
        return (lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7], lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6])
    raise Exception("無効なメッシュ次数です")


def concat_indexes_to_meshcode(x_index: str, y_index: str) -> str:
    if len(x_index) == 2:
        return y_index + x_index
    elif len(x_index) == 3:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2]
    elif len(x_index) == 4:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2] + y_index[3] + x_index[3]


def make_all_indexes(min_index: str, max_index: str) -> list:
    def filtering(code: str):
        if len(code) > 2 and int(code[2]) > 7:
            return False
        return True
    return list(filter(filtering, [str(
        i + 1) for i in range(int(min_index), int(max_index) - 1)]))


def get_args():
    parser = argparse.ArgumentParser(
        description='地域メッシュ単位のデータからラスターデータを生成するスクリプト')
    parser.add_argument('csvfile', help='読み込むCSVファイル')
    parser.add_argument('output', help='データの保存先絶対パス')
    parser.add_argument('--meshcol', help='メッシュコードのカラムを0から始まる番号、デフォルトは0')
    parser.add_argument('--valuecol', help='値のカラムを0から始まる番号、デフォルトは1')
    parser.add_argument(
        '--strategy', help='集計方法、mean, median, min, max, stddev, sum')
    parser.add_argument('--nodata', help='データがないメッシュにセットする値、デフォルトは-9999.0')
    parser.add_argument(
        '--noheader', help='CSVにヘッダーが無い場合に入力', action='store_true')
    return parser.parse_args()


def rasterize(csvfile: str,
              output: str,
              meshcol=0,
              valuecol=1,
              aggr_strategy="",
              nodata=-9999.0,
              noheader=False):
    meshcode_col = 0 if meshcol is None else int(meshcol)
    value_col = 1 if valuecol is None else int(valuecol)

    csv_df = pd.read_csv(
        csvfile, header=None) if noheader else pd.read_csv(csvfile)
    meshcode_colname = csv_df.columns[meshcode_col]
    value_colname = csv_df.columns[value_col]
    csv_df = csv_df[[meshcode_colname, value_colname]].astype(
        {meshcode_colname: str, value_colname: float})

    if len(csv_df[meshcode_colname]) != len(csv_df[meshcode_colname].unique()):
        if aggr_strategy == "mean":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
        elif aggr_strategy == "median":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
        elif aggr_strategy == "min":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
        elif aggr_strategy == "max":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
        elif aggr_strategy == "stddev":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()
        elif aggr_strategy == "sum":
            csv_df = csv_df.groupby(meshcode_colname).mean().reset_index()

        csv_df = csv_df.drop_duplicates(subset=meshcode_colname)

    meshinfo = make_meshinfo(csv_df[meshcode_colname].iloc[0])
    x_indexing, y_indexing = make_xy_indexing_methods(meshinfo["num"])

    csv_df["x_index"] = csv_df[meshcode_colname].map(x_indexing)
    csv_df["y_index"] = csv_df[meshcode_colname].map(y_indexing)

    min_x_index = csv_df["x_index"].min()
    max_x_index = csv_df["x_index"].max()
    min_y_index = csv_df["y_index"].min()
    max_y_index = csv_df["y_index"].max()

    origin_meshcode = concat_indexes_to_meshcode(min_x_index, max_y_index)
    origin_latlng = ju.to_meshpoint(origin_meshcode, 0.5, 0.5)

    # 存在しないメッシュのリスト
    x_indexes = csv_df["x_index"].values
    y_indexes = csv_df["y_index"].values
    append_x_indexes = list(filter(
        lambda code: code not in x_indexes, make_all_indexes(min_x_index, max_x_index)))
    append_y_indexes = list(filter(
        lambda code: code not in y_indexes, make_all_indexes(min_y_index, max_y_index)))

    # 画像をつくるための2次元配列
    matrix2d_df = csv_df[["x_index", "y_index", value_colname]
                         ].pivot(values=value_colname, index='y_index', columns='x_index')

    # 存在しないメッシュを内挿
    if len(append_x_indexes) > 0:
        matrix2d_df = matrix2d_df.join(
            pd.DataFrame(index=[], columns=append_x_indexes))
    if len(append_y_indexes) > 0:
        matrix2d_df = pd.concat([matrix2d_df, pd.DataFrame(
            index=append_y_indexes, columns=matrix2d_df.columns)]).fillna(-9999.0 if nodata is None else float(nodata))

    # メッシュの地図上の配置と同じ2次元配列に並べる
    matrix2d_df = matrix2d_df.sort_index(ascending=False)
    matrix2d_df = matrix2d_df.sort_index(axis=1)

    image = Image.fromarray(matrix2d_df.values)
    image.save(output)

    worldfile_path = output.split(".")[0] + ".tfw"
    with open(worldfile_path, mode="w", encoding="utf-8") as f:
        f.write(f"""\
        {meshinfo["size"][0]}
        0
        0
        {-meshinfo["size"][1]}
        {origin_latlng[1]}
        {origin_latlng[0]}
        """.replace(" ", ""))


def main():
    args = get_args()
    rasterize(**{
        "csvfile": args.csvfile,
        "output": args.output,
        "meshcol": 0 if args.meshcol is None else args.meshcol,
        "valuecol": 1 if args.valuecol is None else args.valuecol,
        "aggr_strategy": args.strategy,
        "nodata": -9999.0 if args.nodata is None else args.nodata,
        "noheader": args.noheader
    })


if __name__ == "__main__":
    main()
