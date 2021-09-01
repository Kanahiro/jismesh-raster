import argparse

import pandas as pd
import jismesh.utils as ju
from PIL import Image


def get_meshsize(meshcode: str) -> dict:
    if len(meshcode) == 4:
        return (1, 2/3)
    elif len(meshcode) == 6:
        return (1/8, 1/12)
    elif len(meshcode) == 8:
        return (1/80, 1/120)
    elif len(meshcode) == 9:
        return (1/160, 1/240)
    elif len(meshcode) == 10:
        return (1/320, 1/480)
    elif len(meshcode) == 11:
        return (1/640, 1/960)
    raise Exception("無効なメッシュコードです")


def make_xy_indexing_methods(meshcode: str) -> tuple:
    if len(meshcode) == 4:
        return (lambda meshcode: meshcode[2:4], lambda meshcode: meshcode[0:2])
    elif len(meshcode) == 6:
        return (lambda meshcode: meshcode[2:4] + meshcode[5], lambda meshcode: meshcode[0:2] + meshcode[4])
    elif len(meshcode) == 8:
        return (lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7], lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6])
    elif len(meshcode) == 9:
        return (lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7] + (str(int(meshcode[8]) - 2) if int(meshcode[8]) > 2 else meshcode[8]),
                lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6] + str(-(-int(meshcode[8]) // 2)))
    elif len(meshcode) == 10:
        return (lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7] + (str(int(meshcode[8]) - 2) if int(meshcode[8]) > 2 else meshcode[8]) + (str(int(meshcode[9]) - 2) if int(meshcode[9]) > 2 else meshcode[9]),
                lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6] + str(-(-int(meshcode[8]) // 2)) + str(-(-int(meshcode[9]) // 2)))
    elif len(meshcode) == 10:
        return (lambda meshcode: meshcode[2:4] + meshcode[5] + meshcode[7] + (str(int(meshcode[8]) - 2) if int(meshcode[8]) > 2 else meshcode[8]) + (str(int(meshcode[9]) - 2) if int(meshcode[9]) > 2 else meshcode[9]) + (str(int(meshcode[10]) - 2) if int(meshcode[10]) > 2 else meshcode[10]),
                lambda meshcode: meshcode[0:2] + meshcode[4] + meshcode[6] + str(-(-int(meshcode[8]) // 2)) + str(-(-int(meshcode[9]) // 2))) + str(-(-int(meshcode[10]) // 2))
    raise Exception("無効なメッシュ次数です")


def concat_indexes_to_meshcode(x_index: str, y_index: str) -> str:
    if len(x_index) == 2:
        return y_index + x_index
    elif len(x_index) == 3:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2]
    elif len(x_index) == 4:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2] + y_index[3] + x_index[3]
    elif len(x_index) == 5:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2] + y_index[3] + x_index[3] + str(int(x_index[4]) + 2 * (int(y_index[4]) - 1))
    elif len(x_index) == 6:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2] + y_index[3] + x_index[3] + str(int(x_index[4]) + 2 * (int(y_index[4]) - 1)) + str(int(x_index[5]) + 2 * (int(y_index[5]) - 1))
    elif len(x_index) == 6:
        return y_index[0:2] + x_index[0:2] + y_index[2] + x_index[2] + y_index[3] + x_index[3] + str(int(x_index[4]) + 2 * (int(y_index[4]) - 1)) + str(int(x_index[5]) + 2 * (int(y_index[5]) - 1)) + str(int(x_index[6]) + 2 * (int(y_index[6]) - 1))


def make_all_indexes(min_index: str, max_index: str) -> list:
    def filtering(code: str):
        if len(code) > 2 and int(code[2]) > 7:
            return False
        if len(code) > 4 and (int(code[4]) != 1 and int(code[4]) != 2):
            return False
        if len(code) > 5 and (int(code[5]) != 1 and int(code[5]) != 2):
            return False
        if len(code) > 6 and (int(code[6]) != 1 and int(code[6]) != 2):
            return False
        return True
    return list(filter(filtering, [str(
        i + 1) for i in range(int(min_index), int(max_index) - 1)]))


def get_args():
    parser = argparse.ArgumentParser(
        description='地域メッシュ単位のデータからラスターデータを生成するスクリプト')
    parser.add_argument('csvfile', help='読み込むCSVファイル')
    parser.add_argument('output', help='データの保存先絶対パス')
    parser.add_argument('--meshcol', help='メッシュコードの列番号を左から数えた番号で指定、デフォルトは0')
    parser.add_argument('--valuecol', help='値の列番号を左から数えた番号で指定、デフォルトは1')
    parser.add_argument(
        '--method', help='集計方法、mean, median, min, max, stddev, sum')
    parser.add_argument('--nodata', help='データがないメッシュにセットする値、デフォルトはnan')
    parser.add_argument(
        '--noheader', help='CSVにヘッダーが無い場合に入力', action='store_true')
    return parser.parse_args()


def rasterize(csvfile: str,
              output: str,
              meshcol=0,
              valuecol=1,
              aggr_method=None,
              nodata=None,
              noheader=False):

    csv_df = pd.read_csv(
        csvfile, header=None) if noheader else pd.read_csv(csvfile)
    meshcode_colname = csv_df.columns[meshcol]
    value_colname = csv_df.columns[valuecol]
    csv_df = csv_df[[meshcode_colname, value_colname]].astype(
        {meshcode_colname: str, value_colname: float})

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

    meshsize = get_meshsize(csv_df[meshcode_colname].iloc[0])
    x_indexing, y_indexing = make_xy_indexing_methods(
        csv_df[meshcode_colname].iloc[0])

    csv_df["x_index"] = csv_df[meshcode_colname].map(x_indexing)
    csv_df["y_index"] = csv_df[meshcode_colname].map(y_indexing)

    min_x_index = csv_df["x_index"].min()
    max_x_index = csv_df["x_index"].max()
    min_y_index = csv_df["y_index"].min()
    max_y_index = csv_df["y_index"].max()

    origin_meshcode = concat_indexes_to_meshcode(min_x_index, max_y_index)
    origin_latlng = ju.to_meshpoint(origin_meshcode, 0.5, 0.5)

    # データには存在しないが画像範囲内となるメッシュのリストを生成
    x_indexes = csv_df["x_index"].values
    y_indexes = csv_df["y_index"].values
    append_x_indexes = list(filter(
        lambda code: code not in x_indexes, make_all_indexes(min_x_index, max_x_index)))
    append_y_indexes = list(filter(
        lambda code: code not in y_indexes, make_all_indexes(min_y_index, max_y_index)))

    # 画像をつくるための2次元配列
    matrix2d_df = csv_df[["x_index", "y_index", value_colname]
                         ].pivot(values=value_colname, index='y_index', columns='x_index')

    # 不足メッシュを内挿
    if len(append_x_indexes) > 0:
        matrix2d_df = matrix2d_df.join(
            pd.DataFrame(index=[], columns=append_x_indexes))
    if len(append_y_indexes) > 0:
        matrix2d_df = pd.concat([matrix2d_df, pd.DataFrame(
            index=append_y_indexes, columns=matrix2d_df.columns)])

    # メッシュの地図上の配置と同じ2次元配列に並べる
    matrix2d_df = matrix2d_df.sort_index(ascending=False)
    matrix2d_df = matrix2d_df.sort_index(axis=1)
    if nodata is not None:
        # 値が指定されているならNaN埋め
        matrix2d_df = matrix2d_df.fillna(nodata)

    image = Image.fromarray(matrix2d_df.values)
    image.save(output)

    worldfile_path = output.split(".")[0] + ".tfw"
    with open(worldfile_path, mode="w", encoding="utf-8") as f:
        f.write(f"""\
        {meshsize[0]}
        0
        0
        {-meshsize[1]}
        {origin_latlng[1]}
        {origin_latlng[0]}
        """.replace(" ", ""))


def main():
    args = get_args()
    rasterize(**{
        "csvfile": args.csvfile,
        "output": args.output,
        "meshcol": 0 if args.meshcol is None else int(args.meshcol),
        "valuecol": 1 if args.valuecol is None else int(args.valuecol),
        "aggr_method": args.method,
        "nodata": -9999.0 if args.nodata is None else float(args.nodata),
        "noheader": args.noheader
    })


if __name__ == "__main__":
    main()
