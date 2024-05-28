# -* - coding: utf-8 -*-

# 対応ファイル: m4a
# いろんな文字化けを治す
# タグ情報をもとにファイル整理もできる

# M4Aファイルのタグ情報が SJIS で書き込まれている場合、UTF-16に書き換えるプログラム
# ・古いM4Aファイルはタグ情報が SJIS で書き込まれている場合がある。
# ・現在はM4Aファイルのタグ情報は UTF-16 で書き込むルールになっている。
# ・よって最近の音楽プレーヤー等で古いM4Aファイルを読み込んだ際に SJIS の日本語が文字化けする。
# ・SJISで書き込まれたタグ情報をUTF-16に変換するのが本プログラムである。
# ・更新対象の M4Aタグ要素は Artist, Album, AlbumArtist, OriginalArtist, disc_num, track_num, title

# ---------------------------------------------------------------------
# ユーザー設定値
# ---------------------------------------------------------------------

# m4a格納フォルダ (最上位パスを指定)
from math import log


def delete_ng_letter(str):
    return (
        str.replace(":", "：")
        .replace("?", "？")
        .replace("*", "＊")
        .replace("/", "／")
        .replace("\\", "＼")
        .replace("<", "＜")
        .replace(">", "＞")
        .replace("|", "｜")
        .replace('"', "”")
    )


# 入力フォルダ
targetFolderPath = "C:\\破損"

# 出力ファイル
logFilePath = "C:\\mp3TagLog.txt"

# 出力ファイル2
logFilePath2 = "C:\\mp3TagLog2.txt"
logFileText2 = ""

# ファイル整理後のフォルダ
afterTargetFolderPath = "C:\\dst\\"


# タグ更新フラグ
# True:  タグ情報一覧ファイルを出力後、MP3ファイルのタグ更新する
# False: タグ情報一覧ファイルを出力後、MP3ファイルのタグ更新しない, さらにファイルを移動するかも
# convertMP3tag = True
convertM4Atag = False

# ファイル移動フラグ
isGoingtoMove = False


# ---------------------------------------------------------------------
# ライブラリ類の読み込み
# ---------------------------------------------------------------------
import mutagen
import mutagen.mp4
import glob
import sys
import os
from tkinter import Tk, messagebox

import shutil


# ---------------------------------------------------------------------
# メッセージボックスの表示
# ---------------------------------------------------------------------
def MBox(msg):

    # Tkを定義
    root = Tk()
    root.withdraw()  # Tkのrootウインドウを表示しない

    # コンソール表示
    print("\n" + msg + "\n")

    # メッセージボックスの表示
    messagebox.showerror(os.path.basename(__file__), msg)


# ---------------------------------------------------------------------
# エラー終了 (コンソールとメッセージボックスでエラー内容を通知して終了)
# ---------------------------------------------------------------------
def ErrorEnd(msg):

    # メッセージボックスを表示
    MBox(msg)

    # プロセス終了
    sys.exit()


# ---------------------------------------------------------------------
# 設定値の妥当性確認
# ---------------------------------------------------------------------
def CheckParams():

    # ターゲットフォルダパス(設定値)を絶対パスに変換
    targetDir = os.path.abspath(targetFolderPath)

    # 設定値のチェック (入力フォルダパスがフォルダパスであるか。ファイルパスで無いか)
    if os.path.isdir(targetDir) == False:
        ErrorEnd("Error | 指定されたパスはフォルダパスではありません " + targetDir)

    # 設定値のチェック (入力されたフォルダパスが実在するか)
    if os.path.exists(targetDir) == False:
        ErrorEnd("Error | 指定されたフォルダが存在しません " + targetDir)

    # ターゲットフォルダ以下にあるファイルを再起的に探索
    searchText = targetDir + "/**/*.m4a"
    targetFiles = sorted(glob.glob(searchText, recursive=True))
    if len(targetFiles) == 0:
        ErrorEnd(
            "Error | 指定されたフォルダ内に対象ファイルが存在しません " + targetDir
        )


# ---------------------------------------------------------------------
# ファイルのパーミション変更 (読み取り専用だった場合は書き込み可能に変更)
# ---------------------------------------------------------------------
def ChangePermission_RtoW():

    # ターゲットフォルダ以下にあるファイルを再起的に探索
    searchText = targetFolderPath + "/**/*.m4a"
    targetFiles = sorted(glob.glob(searchText, recursive=True))

    # ターゲットファイルが読み取り専用の場合は、書き込み可能に変更
    # for i, file in enumerate(targetFiles):
    #     target = os.path.abspath(file)
    #     if not os.access(target, os.W_OK):
    #         os.chmod(target, stat.S_IWRITE)


# ---------------------------------------------------------------------
# タグ情報を一覧出力する + タグ情報を更新する
# ---------------------------------------------------------------------
def ConvertTagInfo_SJIStoUTF16(encodeInfoFilePath, updateTag):
    global logFileText2

    # ターゲットフォルダ以下にあるファイルを再起的に探索
    searchText = targetFolderPath + "/**/*.m4a"
    targetFiles = sorted(glob.glob(searchText, recursive=True))

    # 出力ファイル(タグ情報)を新規作成・初期化
    with open(encodeInfoFilePath, mode="w", encoding="UTF-16") as f:

        # 出力ファイルのヘッダ行を出力
        f.write(",,Before,,,,,,,,,,After,,,,,,,," + "\r\n")
        f.write(
            "FilePath,Diff,Encode,Artist,Album_Artist,Original_Artist,Album,disc_num,track_num,title,Encode,Artist,Album_Artist,Original_Artist,Album,disc_num,track_num,title"
            + "\r\n"
        )

        # 変数の初期化 ()ディスクNo. トラックNo.更新用)
        preArtist = ""
        preAlbum = ""
        trackNo = 0

        # ターゲットファイルを一つずつ処理してゆく
        for i, targetFile in enumerate(targetFiles):

            # ターゲットファイルのパスをフルパス化
            targetFile = os.path.abspath(targetFile)
            # print(str(i + 1) + "/" + str(len(targetFiles)) + " " + targetFile)
            f.write('"' + targetFile + '"')

            # M4Aタグ情報を取得する
            audioInfo = mutagen.mp4.MP4(targetFile)
            tags = audioInfo.tags
            if not tags:
                print("Info | NoTag")
                f.write(',"' + "NoTag" + '"' + "\r\n")
                continue

            artist = tags.get("\xa9ART")
            album_artist = tags.get("aART")
            original_artist = tags.get("\xa9wrt")
            album = tags.get("\xa9alb")
            disc_num = tags.get("disk")
            track_num = tags.get("trkn")
            title = tags.get("\xa9nam")

            # 上記のものは、長さ1の配列または、str
            # もし配列なら
            if type(artist) == list:
                artist = artist[0]
            if type(album_artist) == list:
                album_artist = album_artist[0]
            if type(original_artist) == list:
                original_artist = original_artist[0]
            if type(album) == list:
                album = album[0]
            if type(disc_num) == list:
                disc_num = disc_num[0]
            if type(track_num) == list:
                track_num = track_num[0]
            if type(title) == list:
                title = title[0]

            # numにかんしてtupleの場合は、0番目を取得
            if type(disc_num) == tuple:
                disc_num = disc_num[0]

            artist_2 = None
            album_2 = None
            title_2 = None
            album_artist_2 = None
            original_artist_2 = None

            # 1つ前のファイルと同じアーティスト名・アルバム名ならトラックナンバーを1つカウントアップ
            if (artist != preArtist) or (album != preAlbum):
                trackNo = 1
            else:
                trackNo = trackNo + 1
            disc_num_2 = (None, None)
            track_num_2 = (trackNo, None)
            preArtist = artist
            preAlbum = album

            # タグ情報の文字コード変換
            enc1, enc2 = "", ""
            # 元々入力されていた文字列が UTF-16 の場合 (違う場合はExceptionが発生する)
            try:
                enc1, enc2 = "latin1", "cp932"
                # enc1, enc2 = "utf-16", "utf-16"
                if artist is not None:
                    artist_2 = artist[0].encode(enc1).decode(enc2)
                if album is not None:
                    album_2 = album[0].encode(enc1).decode(enc2)
                if title is not None:
                    title_2 = title[0].encode(enc1).decode(enc2)
                if album_artist is not None:
                    album_artist_2 = album_artist[0].encode(enc1).decode(enc2)
                if original_artist is not None:
                    original_artist_2 = original_artist[0].encode(enc1).decode(enc2)
            except Exception as e:
                try:
                    enc1, enc2 = "cp932", "utf-16"
                    if artist is not None:
                        artist_2 = artist[0].encode(enc1).decode(enc2)
                    if album is not None:
                        album_2 = album[0].encode(enc1).decode(enc2)
                    if title is not None:
                        title_2 = title[0].encode(enc1).decode(enc2)
                    if album_artist is not None:
                        album_artist_2 = album_artist[0].encode(enc1).decode(enc2)
                    if original_artist is not None:
                        original_artist_2 = original_artist[0].encode(enc1).decode(enc2)
                except Exception as e:
                    enc1, enc2 = "unknown", "unknown"

            # タグ情報を更新する
            if updateTag == True:

                # SJISからUTF-16に変換する
                # タグ情報をセット
                if artist_2 is not None:
                    tags["\xa9ART"] = artist_2
                if album_2 is not None:
                    tags["\xa9alb"] = album_2
                if title_2 is not None:
                    tags["\xa9nam"] = title_2
                if album_artist_2 is not None:
                    tags["aART"] = album_artist_2
                if original_artist_2 is not None:
                    tags["\xa9wrt"] = original_artist_2
                tags["trkn"] = [track_num_2]
                tags["disk"] = disc_num

                # ファイル名の更新
                try:
                    # print(targetFile)
                    os.rename(
                        targetFile,
                        afterTargetFolderPath + delete_ng_letter(title_2) + ".m4a",
                    )
                except Exception as e:
                    print(f"Error: {e}")

                # M4Aタグ情報を更新する
                try:
                    audioInfo.save()
                except Exception as e:
                    msg = f"Error | 例外発生 : タグ情報を更新できませんでした。\nファイル名={targetFile}\n{e}"
                    print(msg)
                    MBox(msg)
            else:
                # タグ情報の更新をしない場合
                # アーティスト名/アルバム名/01-タイトル.{拡張子}のように整理する
                # afterTargetFolderPath
                #  アーティスト名のフォルダが存在しない場合は、作成する
                #  アーティスト名のフォルダ内に、アルバム名のフォルダが存在しない場合は、作成する

                artist = delete_ng_letter(artist)

                if album_artist is not None:
                    album_artist = delete_ng_letter(album_artist)
                else:
                    album_artist = artist
                album = delete_ng_letter(album)
                title = delete_ng_letter(title)

                if isGoingtoMove:
                    if not os.path.exists(afterTargetFolderPath + album_artist_2):
                        os.makedirs(afterTargetFolderPath + album_artist_2)

                    if not os.path.exists(
                        afterTargetFolderPath + album_artist_2 + "\\" + album_2
                    ):
                        os.makedirs(
                            afterTargetFolderPath + album_artist_2 + "\\" + album_2
                        )

                new_fileName = (
                    str(track_num[0]).zfill(2)
                    + "-"
                    + title
                    + os.path.splitext(targetFile)[1]
                )
                print(str(i + 1) + "/" + str(len(targetFiles)))
                print(artist + "\\" + album + "\\" + new_fileName)
                logFileText2 += str(i + 1) + "/" + str(len(targetFiles)) + "\n"
                logFileText2 += targetFile + "\n"
                logFileText2 += album_artist + "\\" + album + "\\" + new_fileName + "\n"

                if isGoingtoMove:
                    shutil.move(
                        targetFile,
                        afterTargetFolderPath
                        + album_artist_2
                        + "\\"
                        + album_2
                        + "\\"
                        + new_fileName,
                    )


# ---------------------------------------------------------------------
# main関数
# ---------------------------------------------------------------------
def main():
    # ユーザー設定値のチェック
    CheckParams()

    # ファイルのパーミション変更 (読み取り専用だった場合は書き込み可能に変更)
    ChangePermission_RtoW()

    # タグ情報の一覧出力 + タグ情報の更新
    ConvertTagInfo_SJIStoUTF16(logFilePath, convertM4Atag)

    # タグ情報の一覧出力
    with open(logFilePath2, mode="w", encoding="UTF-16") as f:
        f.write(logFileText2)


# main関数を呼び出し
if __name__ == "__main__":
    main()
