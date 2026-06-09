# AGENTS.md

## GitHub 提交归属

本项目使用 GitHub 账号 `xTreeRoot` 作为仓库提交归属。

重建历史、创建提交、修正提交者信息、amend、rebase 或执行任何会产生新提交对象的操作时，必须保持本仓库 Git 配置与提交 `author` / `committer` 一致，统一使用：

```text
xTreeRoot <79004055+xTreeRoot@users.noreply.github.com>
```

执行提交前，应确认或设置本仓库本地 Git 配置：

```bash
git config user.name "xTreeRoot"
git config user.email "79004055+xTreeRoot@users.noreply.github.com"
```

如需通过环境变量创建、重写或修正提交，也必须保持一致：

```bash
GIT_AUTHOR_NAME="xTreeRoot" \
GIT_AUTHOR_EMAIL="79004055+xTreeRoot@users.noreply.github.com" \
GIT_COMMITTER_NAME="xTreeRoot" \
GIT_COMMITTER_EMAIL="79004055+xTreeRoot@users.noreply.github.com" \
git commit
```

提交必须归入 GitHub 账号：

```text
https://github.com/xTreeRoot
```

## GitHub 远端

推送这个已有项目到 GitHub 仓库时使用：

```bash
git remote add origin https://github.com/xTreeRoot/wallpaper-mp4-exporter.git
git branch -M main
git push -u origin main
```
