**这是一个利用AI翻译终端输出的程序**

例如：
```
transh "npm -h"
执行中: npm -h
命令输出（1266 字符）
---
npm <command>

Usage:

npm install        install all the dependencies in your project
npm install <foo>  add the <foo> dependency to your project
npm test           run this project's tests
npm run <foo>      run the script named <foo>
npm <command> -h   quick help on <command>
npm -l             display usage info for all commands
npm help <term>    search for help on <term>
npm help npm       more involved overview

All commands:

    access, adduser, audit, bugs, cache, ci, completion,
    config, dedupe, deprecate, diff, dist-tag, docs, doctor,
    edit, exec, explain, explore, find-dupes, fund, get, help,
    help-search, init, install, install-ci-test, install-test,
    link, ll, login, logout, ls, org, outdated, owner, pack,
    ping, pkg, prefix, profile, prune, publish, query, rebuild,
    repo, restart, root, run, sbom, search, set, shrinkwrap,
    star, stars, start, stop, team, test, token, undeprecate,
    uninstall, unpublish, unstar, update, version, view, whoami

Specify configs in the ini-formatted file:
    /home/usr/.npmrc
or on the command line via: npm <command> --key=value

More configuration info: npm help config
Configuration fields: npm help 7 config

npm@11.6.2 /home/usr/.nvm/versions/node/v24.12.0/lib/node_modules/npm

---
正在翻译为 简体中文...
npm <命令>

用法：

npm install        安装项目中的所有依赖项
npm install <包名>  将 <包名> 依赖添加到项目中
npm test           运行项目的测试
npm run <脚本名>    运行名为 <脚本名> 的脚本
npm <命令> -h      查看 <命令> 的快速帮助
npm -l             显示所有命令的使用信息
npm help <关键词>   搜索关于 <关键词> 的帮助
npm help npm       获取更详细的 npm 概述

所有命令：

    access, adduser, audit, bugs, cache, ci, completion,
    config, dedupe, deprecate, diff, dist-tag, docs, doctor,
    edit, exec, explain, explore, find-dupes, fund, get, help,
    help-search, init, install, install-ci-test, install-test,
    link, ll, login, logout, ls, org, outdated, owner, pack,
    ping, pkg, prefix, profile, prune, publish, query, rebuild,
    repo, restart, root, run, sbom, search, set, shrinkwrap,
    star, stars, start, stop, team, test, token, undeprecate,
    uninstall, unpublish, unstar, update, version, view, whoami

配置文件可设置在 ini 格式的文件中：
    /home/usr/.npmrc
或通过命令行设置：npm <命令> --key=value

更多配置信息：npm help config
配置字段说明：npm help 7 config

npm@11.6.2 /home/usr/.nvm/versions/node/v24.12.0/lib/node_modules/npm
```
**它同时支持自适应多语言，理论上支持世界上任何主流语言**
```
usr@7472:~$ transh -l
当前目标语言：简体中文
输入新的目标语言：日本语

正在将界面文本翻译为 日本语...
✓ 语言已更改且界面文本已翻译！
usr@7472:~$ transh -h
使用方法: transh [オプション] "コマンド"

オプション:
  -c              インタラクティブ設定
  -t "text"       テキストを直接翻訳
  -f output.txt   入力ファイルを翻訳して出力に保存
  -l              ターゲット言語を変更
  -r              キャッシュを強制更新（既存のキャッシュを無視）
  --vi-env        現在の設定を表示
  -h, --help      このヘルプメッセージを表示

例:
  transh "npm -h"           # コマンド出力を翻訳
  transh -t "hello"         # テキストを直接翻訳
  transh -f out.txt in.txt  # ファイルを翻訳
  transh -c                 # AI設定を構成
  transh -l                 # ターゲット言語を変更
  transh -r "npm -h"        # キャッシュを強制更新
usr@7472:~$ transh -l
現在のターゲット言語: 日本语
新しいターゲット言語を入力: 简体中文

UIテキストを翻訳中 简体中文...
✓ 言語が変更され、UIテキストが翻訳されました！
usr@7472:~$ transh -h
用法：transh [选项] "命令"

选项：
  -c              交互式配置
  -t "文本"       直接翻译文本
  -f 输出.txt     翻译输入文件并保存到输出
  -l              更改目标语言
  -r              强制刷新缓存（忽略现有缓存）
  --vi-env        查看当前配置
  -h, --help      显示此帮助信息

示例：
  transh "npm -h"           # 翻译命令输出
  transh -t "hello"         # 直接翻译文本
  transh -f out.txt in.txt  # 翻译文件
  transh -c                 # 配置 AI 设置
  transh -l                 # 更改目标语言
  transh -r "npm -h"        # 强制刷新缓存
usr@7472:~$ 
```
**安装**

执行
```
curl -sSL https://nas.dyyapp.space/d/nas/guest/app/install_transh.sh?sign=x-G77UPmvEiS2X0_e2tdBbQh51Px3IjYmg6-S4GMO1s=:0 -o install_transh.sh
chmod +x install_transh.sh
sudo bash install_transh.sh
```
