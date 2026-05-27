---
title: "PyInstallerで作ったexe、ウイルス扱いされる問題をInno Setupで解決した話"
emoji: "🛡️"
type: "tech"
topics: ["Python", "PyInstaller", "InnoSetup", "セキュリティ", "配布"]
published: true
---

Pythonで設計データの比較・検証用ツールを作って、exeにして配布しています。PyInstallerでビルドしたexeがAVに誤検知される問題は前から知ってたんですが、自分のツールでもVirusTotalに投げたら **66ベンダー中16件がウイルス判定**でした。配布する以上、放置するわけにもいかない。

## 最初の考え: --onedirに変えてみた

PyInstallerの仕組みを調べると、`--onefile` は実行時に一時フォルダにファイルを展開する動作をしています。これがAVに嫌われるんだろうという推測で、最初は `--onedir` に変えてビルドしてVirusTotalに投げてみました。結果は **16/66 のまま**。変わらない。このやり方じゃ駄目でした。

## 他の案を並べてみる

ネットで調べると、AVベンダーに誤検知報告する手もあるし、bootloaderを自前ビルドする方法もあります。正直、bootloader自前ビルドは試したい気もしたけど、VisualStudioの環境構築がめんどくなってやめました。Nuitkaに移行する案もあるけど、ビルドが重いし依存関係の修正に手間かかる。毎回バージョンリリースのたびに対応するのは現実的じゃないです。

## Inno Setupで包んでみる

そこで思いついたのがInno Setupです。exeそのものじゃなくて、.iss書いてインストーラーにしちゃえば、PyInstaller特有の一時フォルダ展開がAVに見えなくなるんじゃないかと。

issファイルざっと20行書いてビルド、VirusTotalに投げました。**0/66**。

## 最小構成のissファイル

```ini
[Setup]
AppName=MyApp
AppVersion=1.0
DefaultDirName={autopf}\MyApp
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\MyApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{autoprograms}\MyApp"; Filename: "{app}\MyApp.exe"

[Run]
Filename: "{app}\MyApp.exe"; Description: "起動する"; Flags: nowait postinstall skipifsilent
```

`PrivilegesRequired=lowest` で管理者権限を要求しないようにしています。インストーラーで管理者権限って出ると構えるので。`Compression=lzma2` と `SolidCompression=yes` をセットにすると圧縮が効いて、375MBのZIPが200MB台に落ちました。`Flags: recursesubdirs` はPyInstallerの出力ディレクトリをそのまま突っ込むときに必須です。

## 今のところはこの形

正直、ずっと効くのかはわかりません。AV側の検知ロジックは常に更新されてるし、次のバージョンリリースでどうなるかは見守るしかない。ただ少なくともいま、issファイル20行で **16/66 → 0/66** まで落ちたので、他の方法と比べても手間に見合ってると思っています。

ZIP版も配布は残してあります。インストーラーに抵抗ある人もいるので。AV誤検知は出るけど、ダウンロードページに回避手順を書いておけば、ユーザーが判断して選べるかなと。

---

Inno Setup: https://jrsoftware.org/isinfo.php
