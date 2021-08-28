# jismesh-raster

日本の標準地域メッシュで集計されたデータからメッシュのラスターデータを作るスクリプト

## what is this

-   標準地域メッシュは、経緯度を一定のルールで均等に分割して得られるメッシュである
-   メッシュの形状自体に意味はなく、紐付けられる集計値が重要であり、ベクターデータよりラスターデータが適している
-   本スクリプトでは、1 つメッシュに 1 ピクセルを割り当て、同時に適切なワールドファイルを出力する

## 出力データと仕様

-   .tif ファイル
    -   拡張子は必ずしも`.tif`ではなく、コマンド引数で指定したファイル名となる
    -   Float32
    -   Single band
    -   GeoTiff ではないことに留意（ヘッダーは書き込まれていない）
    -   CSV に存在するメッシュが全て含まれる最小の解像度となる
-   .tfw ファイル
    -   .tif ファイルと同名で書き出される
    -   経緯度で設定されている（つまり CRS は`EPSG:4326`）

## コマンド

```
必須項目:
  csvfile 読み込むCSVファイル
  output  データの保存先絶対パス

optional arguments:
  --meshcol  メッシュコードのカラムを0から始まる番号、デフォルトは0
  --valuecol 値のカラムを0から始まる番号、デフォルトは1
  --strategy 集計方法、mean, median, min, max, stddev, sum
  --nodata   データがないメッシュにセットする値、デフォルトは-9999.0
  --noheader CSVにヘッダーが無い場合に入力
```

## インストール

```sh
pip install jismesh-raster
```

## 使い方

以下の形式の CSV を例とする（出典：[全国の人流オープンデータ](https://www.geospatial.jp/ckan/dataset/mlit-1km-fromto)）

```csv
mesh1kmid,prefcode,citycode,year,month,dayflag,timezone,population
53394519,13,13101,2019,01,0,0,13533
53394519,13,13101,2019,01,0,1,5818
53394519,13,13101,2019,01,2,2,26039
53394528,13,13101,2019,01,0,0,27561
53394528,13,13101,2019,01,1,2,57219
53394528,13,13101,2019,01,2,0,73526
```

-   メッシュコードのカラムは左端から数えて 1 列目の`mesh1kmid`、メッシュ画像にしたい値は 8 列目の`population`である
-   このスクリプトでは 0 をスタートとして数えるので、`0`列目、`7`列目と読み替える
-   もし複数行にわたって同一のメッシュコードが存在する場合は、その`合計値`を求める
-   データが存在しない部分の値は`-999999.0`とする

```sh
jismesh-raster meshdata.csv mesh.tif --meshcol 0 --valuecol 7 --strategy sum --nodata -999999.0
```

-   `meshcol`のデフォルト値は`0`なので、今回の場合省略出来る
-   `nodata`のデフォルト値は`-9999.0`なので、それでもよければ省略出来る

```sh
jismesh-raster meshdata.csv mesh.tif --valuecol 7 --strategy sum
```

-   `strategy`を指定しない場合に複数行にわたって同一のメッシュコードが存在 s うる場合は、うちひとつのデータがメッシュの値となる

以下のような CSV の場合

```csv
53394519,13533
53394519,5818
53394519,26039
53394528,27561
53394528,57219
53394528,73526
```

-   ヘッダー行が無い場合は`noheader`オプションを指定する
-   `valuecol`のデフォルト値は`1`なので、上記の場合省略出来る

```sh
jismesh-raster meshdata.csv mesh.tif --strategy mean
```
